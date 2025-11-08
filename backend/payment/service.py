

from typing import Dict, Any, Optional
from datetime import datetime, timedelta, timezone
import random

from payment.repo import (
    create_intent, get_intent, set_otp,
    try_mark_processing, mark_failed, mark_confirmed, upsert_payment
)
from payment.external import (
    user_get_by_id, user_debit,
    sf_get_invoice_current_of, sf_get_my_invoice, sf_pay
)
from payment.mailer import send_otp_email, send_payment_success_email, send_payer_receipt_email

def _otp6() -> str:
    return f"{random.randint(0, 999999):06d}"


def _calc_total_from_invoice(inv: dict) -> float:
    amount = inv.get("total_amount")
    if amount is not None:
        return float(amount)
    items = inv.get("invoice_items", [])
    return float(sum(float(it.get("amount", 0) or 0) for it in items))


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _parse_iso_utc(s: str) -> datetime:
    # """
    # Parse ISO string lưu trong DB về datetime aware (UTC).
    # Hỗ trợ cả dạng có 'Z' và dạng '+00:00'.
    # """
    # if s.endswith("Z"):
    #     s = s.replace("Z", "+00:00")
    # dt = datetime.fromisoformat(s)
    # # nếu thiếu tzinfo thì ép về UTC (phòng xa)
    # if dt.tzinfo is None:
    #     dt = dt.replace(tzinfo=timezone.utc)
    # return dt.astimezone(timezone.utc)
    """
    Parse ISO string lưu trong DB về datetime aware (UTC).
    Hỗ trợ cả dạng có 'Z' và dạng '+00:00'.
    Tự động chuẩn hóa microseconds về 6 chữ số.
    """
    if not s:
        raise ValueError("Empty datetime string")

    s = s.strip()
    if s.endswith("Z"):
        s = s.replace("Z", "+00:00")

    # Chuẩn hóa phần microsecond (nếu có) về 6 chữ số
    if "." in s:
        main, frac = s.split(".", 1)
        if "+" in frac:
            frac, tz = frac.split("+", 1)
            frac = (frac + "000000")[:6]
            s = f"{main}.{frac}+{tz}"
        elif "-" in frac:
            frac, tz = frac.split("-", 1)
            frac = (frac + "000000")[:6]
            s = f"{main}.{frac}-{tz}"
        else:
            frac = (frac + "000000")[:6]
            s = f"{main}.{frac}"

    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


async def create_intent_service(
    *,
    payer_user_id: str,
    token_for_my_invoice: str | None,  # lấy từ claims["_raw_token"]
    student_id: str | None,
    semester_id: str | None
) -> dict:
    # normalize "" / "string" -> None
    student_id = (student_id or "").strip() or None
    semester_id = (semester_id or "").strip() or None
    if student_id and student_id.lower() == "string":
        student_id = None
    if semester_id and semester_id.lower() == "string":
        semester_id = None

    # 1) Lấy invoice
    if student_id:
        inv = await sf_get_invoice_current_of(student_id, token_for_my_invoice)
    else:
        inv = await sf_get_my_invoice(token_for_my_invoice, semester_id)

    if not inv:
        raise ValueError("Không tìm thấy hóa đơn")

    # 🧱 NGĂN THANH TOÁN LẠI
    if inv.get("status") == "paid":
        raise ValueError("Hóa đơn này đã được thanh toán, không thể tạo giao dịch mới.")

    # 2) Tính tổng tiền
    amount = _calc_total_from_invoice(inv)
    if amount <= 0:
        raise ValueError("Tổng tiền không hợp lệ")

    # 3) Lấy email người trả tiền từ user_svc (cần token)
    payer = await user_get_by_id(payer_user_id, token_for_my_invoice)
    from payment.repo import get_intent_by_invoice
    # old_intent = get_intent_by_invoice(inv["id"])
    # if old_intent and old_intent["status"] in ("pending", "otp_sent"):
    #     otp_exp = old_intent.get("otp_expires_at")
    #     if otp_exp:
    #         try:
    #             exp_dt = _parse_iso_utc(otp_exp)
    #             if exp_dt < _utcnow():
    #                 # OTP đã hết hạn → cho phép tạo intent mới
    #                 mark_failed(old_intent["id"], "expired")
    #             # else:
    #             #     # ✅ OTP vẫn còn hiệu lực → chặn thanh toán lại
    #             #     raise ValueError("Hóa đơn đang được xử lý hoặc đã có yêu cầu thanh toán đang chờ OTP.")
    #         except Exception as e:
    #             print(f"[WARN] Không parse được otp_expires_at: {otp_exp} ({e})")
    #             mark_failed(old_intent["id"], "failed")
    #     else:
    #         # ✅ chưa từng gửi OTP → cũng coi như đang thanh toán
    #         raise ValueError("Hóa đơn đang được xử lý hoặc đã có yêu cầu thanh toán đang chờ OTP.")

    old_intent = get_intent_by_invoice(inv["id"])
    if old_intent and old_intent["status"] in ("pending", "otp_sent"):
        exp_dt = _parse_iso_utc(old_intent["otp_expires_at"])
        if exp_dt < _utcnow():
            mark_failed(old_intent["id"], "expired")
    old_intent = get_intent_by_invoice(inv["id"])
    if old_intent and old_intent["status"] in ("pending", "otp_sent"):
        otp_exp = old_intent.get("otp_expires_at")
        if otp_exp:  # ✅ chỉ xử lý khi có giá trị
            try:
                exp_dt = _parse_iso_utc(otp_exp)
                if exp_dt < _utcnow():
                    mark_failed(old_intent["id"], "expired")
            except Exception as e:
                print(f"[WARN] Không parse được otp_expires_at: {otp_exp} ({e})")
                mark_failed(old_intent["id"], "failed")
        else:
            # ✅ nếu chưa từng gửi OTP, thì giữ nguyên intent để báo "đang thanh toán"
            pass


    # 4) Ghi intent
    try:
        return create_intent({
            "payer_user_id": payer_user_id,
            "payer_email":   payer["email"],
            "student_id":    inv["student_id"],
            "invoice_id":    inv["id"],
            "amount":        float(amount),
            "status":        "pending"
        })
    except Exception as e:
        err_text = str(e)
        if "uq_pi_one_open_per_invoice" in err_text or "duplicate key" in err_text:
            raise ValueError("Hóa đơn đang được xử lý hoặc đã có yêu cầu thanh toán đang chờ OTP.")
        raise
    # return create_intent({
    #     "payer_user_id": payer_user_id,
    #     "payer_email":   payer["email"],
    #     "student_id":    inv["student_id"],
    #     "invoice_id":    inv["id"],
    #     "amount":        float(amount),
    #     "status":        "pending"
    # })


# async def send_otp_service(intent_id: str) -> Dict:
#     intent = get_intent(intent_id)
#     if not intent:
#         raise ValueError("Intent không tồn tại")

#     # Check if current OTP is expired
#     if intent.get("otp_expires_at"):
#         exp_dt = _parse_iso_utc(intent["otp_expires_at"])
#         if exp_dt < _utcnow():
#             mark_failed(intent_id, "expired")
#             raise ValueError("OTP cũ đã hết hạn, vui lòng tạo giao dịch mới")

#     # Check attempt limit
#     if intent.get("otp_attempt", 0) >= 3:
#         mark_failed(intent_id, "max_attempts")
#         raise ValueError("Đã vượt quá số lần gửi OTP cho phép")

#     if intent["status"] not in ("pending", "otp_sent"):
#         raise ValueError("Intent không ở trạng thái cho phép gửi OTP")

#     otp = _otp6()
#     exp = (_utcnow() + timedelta(minutes=5)).isoformat()

#     send_otp_email(intent["payer_email"], otp)
#     return set_otp(intent_id, otp, exp)
# async def send_otp_service(intent_id: str) -> Dict:
#     intent = get_intent(intent_id)
#     if not intent:
#         raise ValueError("Intent không tồn tại")

#     # Lấy thông tin hóa đơn đang liên kết
#     invoice_id = intent["invoice_id"]
#     payer_user_id = intent["payer_user_id"]
#     payer_email = intent["payer_email"]
#     student_id = intent["student_id"]
#     amount = intent["amount"]

#     # ✅ Kiểm tra nếu OTP đã hết hạn → mark intent cũ failed & tạo intent mới
#     if intent.get("otp_expires_at"):
#         try:
#             exp_dt = _parse_iso_utc(intent["otp_expires_at"])
#             if exp_dt < _utcnow():
#                 mark_failed(intent_id, "failed")

#                 # 🧱 Tạo intent mới thay thế intent cũ
#                 new_intent = create_intent({
#                     "payer_user_id": payer_user_id,
#                     "payer_email": payer_email,
#                     "student_id": student_id,
#                     "invoice_id": invoice_id,
#                     "amount": float(amount),
#                     "status": "pending"
#                 })

#                 # Gửi lại OTP mới
#                 otp = _otp6()
#                 exp = (_utcnow() + timedelta(minutes=5)).isoformat()
#                 send_otp_email(payer_email, otp)
#                 return set_otp(new_intent["id"], otp, exp)
#         except Exception as e:
#             print(f"[WARN] Lỗi khi parse otp_expires_at: {e}")
#             mark_failed(intent_id, "failed")

#     # Nếu OTP còn hiệu lực thì không gửi lại
#     if intent.get("otp_expires_at"):
#         exp_dt = _parse_iso_utc(intent["otp_expires_at"])
#         if exp_dt > _utcnow():
#             raise ValueError("OTP hiện tại vẫn còn hiệu lực, vui lòng chờ hết hạn trước khi gửi lại.")

#     # Nếu intent không còn trong trạng thái hợp lệ
#     if intent["status"] not in ("pending", "otp_sent"):
#         raise ValueError("Intent không ở trạng thái cho phép gửi OTP")

#     # ✅ Gửi OTP mới cho intent hiện tại (trường hợp resend thủ công)
#     otp = _otp6()
#     exp = (_utcnow() + timedelta(minutes=5)).isoformat()
#     send_otp_email(payer_email, otp)
#     return set_otp(intent_id, otp, exp)
async def send_otp_service(intent_id: str) -> Dict:
    intent = get_intent(intent_id)
    if not intent:
        raise ValueError("Intent không tồn tại")

    payer_email = intent["payer_email"]

    otp = _otp6()
    # exp = (_utcnow() + timedelta(minutes=5)).isoformat()
    exp = (_utcnow() + timedelta(seconds=180)).isoformat()


    try:
        otp_exp_str = intent.get("otp_expires_at")

        # 🕓 Nếu chưa từng gửi OTP → gửi mới
        if not otp_exp_str:
            send_otp_email(payer_email, otp)
            return set_otp(intent_id, otp, exp)

        exp_dt = _parse_iso_utc(otp_exp_str)

        # 🔁 Nếu OTP đã hết hạn → KHÔNG mark expired, chỉ gửi OTP mới
        if exp_dt < _utcnow():
            send_otp_email(payer_email, otp)
            return set_otp(intent_id, otp, exp)

        # 🚫 Nếu OTP vẫn còn hiệu lực → chặn gửi lại
        else:
            raise ValueError("OTP hiện tại vẫn còn hiệu lực, vui lòng chờ hết hạn trước khi gửi lại.")

    except Exception as e:
        print(f"[WARN] Lỗi khi xử lý resend OTP: {e}")
        # fallback: vẫn gửi lại OTP mới nếu có lỗi parse
        send_otp_email(payer_email, otp)
        return set_otp(intent_id, otp, exp)








from typing import Dict, Optional
from payment.mailer import send_payment_success_email, send_payer_receipt_email

async def confirm_service(intent_id: str, otp_input: str, token_for_calls:Optional[str]) -> Dict:
    intent = get_intent(intent_id)
    if not intent:
        raise ValueError("Intent không tồn tại")

    # Idempotent guard
    if intent["status"] == "confirmed":
        raise ValueError("Intent đã confirmed (idempotent).")

    # Tránh mâu thuẫn với cơ chế lock:
    if intent["status"] == "processing":
        raise ValueError("Intent đang xử lý, thử lại sau.")

    if intent["status"] not in ("pending", "otp_sent"):
        raise ValueError(f"Trạng thái không cho phép confirm: {intent['status']}")

    # Kiểm tra OTP
    if not intent.get("otp_code") or not intent.get("otp_expires_at"):
        raise ValueError("Chưa phát OTP")

    if otp_input != intent["otp_code"]:
        raise ValueError("OTP sai, vui lòng thử lại.")

    exp_dt = _parse_iso_utc(intent["otp_expires_at"])
    if exp_dt < _utcnow():
        mark_failed(intent_id, "expired")
        raise ValueError("OTP hết hạn")

    # Optimistic lock: chỉ 1 tiến trình được xử lý
    locked = try_mark_processing(intent_id)
    if not locked:
        latest = get_intent(intent_id)
        if latest:
            if latest["status"] == "confirmed":
                raise ValueError("Intent đã confirmed (idempotent).")
            if latest["status"] == "processing":
                raise ValueError("Intent đang xử lý, thử lại sau.")
        raise ValueError("Không thể lock intent (race condition). Thử lại.")

    # Đo balance trước/sau chính xác
    payer_before = await user_get_by_id(intent["payer_user_id"], token_for_calls)
    bal_before = float(payer_before.get("balance", 0.0))

    # Trừ tiền
    try:
        debit = await user_debit(intent["payer_user_id"], float(intent["amount"]), token_for_calls)
        bal_after = float(debit.get("new_balance", debit.get("balance", 0.0)))

        student_data = await user_get_by_id(intent["student_id"], token_for_calls) #payee
        payer_data = await user_get_by_id(intent["payer_user_id"], token_for_calls) #payee
        
        student_user = student_data.get("username", "Không có thông tin")
        payer_user = payer_data.get("username", "Không có thông tin")
        student_email = student_data.get("email", "Không có thông tin")


        # Đánh dấu invoice đã thanh toán ở studentfee_svc
        await sf_pay(intent["invoice_id"], token_for_calls)
        
        # Xác nhận thành công
        confirmed = mark_confirmed(intent_id)
        payment = upsert_payment(
            intent_id=intent_id,
            amount=float(intent["amount"]),
            bal_before=bal_before,
            bal_after=bal_after,
        )

        # Gửi email biên nhận
        current_time = _utcnow().strftime("%Y-%m-%d %H:%M:%S")
        payment_info = {
            "order_id": intent_id,
            "amount": float(intent["amount"]),
            "payment_date": current_time,
            "description": f"Thanh toán học phí - Mã hóa đơn: {intent['invoice_id']}",
            "student_user": student_user, #payee
            "payer_user": payer_user, #payer

        }

      
        # Gửi email cho người thanh toán
        try:
            if payer_user != student_user:
                # Nếu người thanh toán khác người được thanh toán
                send_payer_receipt_email(
                    to_email=intent["payer_email"],
                    payment_info=payment_info
                )

                send_payer_receipt_email(
                    to_email=student_email,
                    payment_info=payment_info
                )
            else:
                # Nếu cùng một người (tự thanh toán cho mình)
                send_payer_receipt_email(
                    to_email=student_email,
                    payment_info=payment_info
                )
        except Exception as e:
            print(f"Lỗi khi gửi email xác nhận thanh toán: {e}")


        return {"intent": confirmed, "payment": payment}

    except Exception as e:
        # Nếu có lỗi trong quá trình xử lý, đánh dấu thất bại
        mark_failed(intent_id, "failed")
        raise ValueError(f"Lỗi xử lý thanh toán: {str(e)}")




