from typing import Dict, Any, Optional
from payment.db import get_supabase_client
from payment.external import user_get_username


SCHEMA = "payment_svc"
TB_INTENT = "payment_intents"
TB_PAYMENT = "payments"

def _tbl(name: str):
    # Luôn chỉ rõ schema để tránh lệ thuộc cấu hình Exposed Schemas
    return get_supabase_client().schema(SCHEMA).table(name)

def _first(res):
    # Chuẩn hóa trả về & báo lỗi rõ ràng
    err = getattr(res, "error", None)
    if err:
        # err.message / err.code tùy client
        raise RuntimeError(getattr(err, "message", str(err)))
    data = res.data
    if isinstance(data, list):
        return data[0] if data else None
    return data  # .single() trả về dict

def get_intent(intent_id: str) -> Optional[Dict[str, Any]]:
    res = _tbl(TB_INTENT).select("*").eq("id", intent_id).single().execute()
    return _first(res)

def create_intent(row: Dict[str, Any]) -> Dict[str, Any]:
    res = _tbl(TB_INTENT).insert(row).execute()
    item = _first(res)
    if not item:
        raise RuntimeError("Insert returned no data")
    return item

# def set_otp(intent_id: str, code: str, expires_at_iso: str) -> Dict[str, Any]:
#     res = (
#         _tbl(TB_INTENT)
#         .update({
#             "otp_code": code,
#             "otp_expires_at": expires_at_iso,
#             "status": "otp_sent",
#         })
#         .eq("id", intent_id)
#         .execute()
#     )
#     item = _first(res)
#     if not item:
#         raise RuntimeError("Update OTP returned no data")
#     return item
def set_otp(intent_id: str, code: str, expires_at_iso: str) -> Dict[str, Any]:
    # Kiểm tra xem mã OTP đã tồn tại chưa
    existing_otp = (
        _tbl(TB_INTENT)
        .select("id")
        .eq("otp_code", code)
        .neq("id", intent_id)  # Loại trừ intent hiện tại
        .in_("status", ["otp_sent", "pending"])  # Chỉ kiểm tra các intent đang active
        .execute()
    )
    
    if _first(existing_otp):
        raise ValueError("OTP code already exists in another active transaction")
    
    # Lấy số lần thử hiện tại
    current = _tbl(TB_INTENT).select("otp_attempts").eq("id", intent_id).single().execute()
    current_attempt = (_first(current) or {}).get("otp_attempts", 0)
    
    # Nếu OTP chưa tồn tại, tiếp tục cập nhật và tăng attempt
    res = (
        _tbl(TB_INTENT)
        .update({
            "otp_code": code,
            "otp_expires_at": expires_at_iso,
            "status": "otp_sent",
            "otp_attempts": (current_attempt or 0) + 1
        })
        .eq("id", intent_id)
        .execute()
    )
    
    item = _first(res)
    if not item:
        raise RuntimeError("Update OTP returned no data")
    return item

def try_mark_processing(intent_id: str) -> Optional[Dict[str, Any]]:
    # Chỉ chuyển sang processing nếu hiện tại đang pending/otp_sent
    res = (
        _tbl(TB_INTENT)
        .update({"status": "processing"})
        .eq("id", intent_id)
        .in_("status", ["pending", "otp_sent"])
        .execute()
    )
    return _first(res)  # None nếu không có hàng nào phù hợp

def mark_failed(intent_id: str, new_status: str = "failed") -> Dict[str, Any]:
    res = _tbl(TB_INTENT).update({"status": new_status}).eq("id", intent_id).execute()
    item = _first(res)
    if not item:
        raise RuntimeError("Mark failed returned no data")
    return item

def mark_confirmed(intent_id: str) -> Dict[str, Any]:
    res = (
        _tbl(TB_INTENT)
        .update({
            "status": "confirmed",
            "otp_code": None,
            "otp_expires_at": None,
        })
        .eq("id", intent_id)
        .execute()
    )
    item = _first(res)
    if not item:
        raise RuntimeError("Mark confirmed returned no data")
    return item

def upsert_payment(intent_id: str, amount: float, bal_before: float, bal_after: float) -> Dict[str, Any]:
    res = (
        _tbl(TB_PAYMENT)
        .upsert(
            {
                "intent_id": intent_id,
                "amount": amount,
                "payer_balance_before": bal_before,
                "payer_balance_after": bal_after,
            },
            on_conflict="intent_id",
            ignore_duplicates=False,
        )
        .execute()
    )
    item = _first(res)
    if not item:
        raise RuntimeError("Upsert payment returned no data")
    return item

def get_intent_by_invoice(invoice_id: str) -> Optional[Dict[str, Any]]:
    res = (
        _tbl(TB_INTENT)
        .select("*")
        .eq("invoice_id", invoice_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    return _first(res)

# def get_payment_history_by_semester(student_id: str, semester_id: str):
#     client = get_supabase_client()

#     # 1️⃣ Lấy invoice_id của kỳ này từ studentfee_svc
#     invoice_res = (
#         client.schema("studentfee_svc")
#         .table("tuition_invoice")
#         .select("id")
#         .eq("student_id", student_id)
#         .eq("semester_id", semester_id)
#         .limit(1)  # ✅ tránh lỗi .single()
#         .execute()
#     )

#     invoices = invoice_res.data or []
#     if not invoices:
#         return []  # ✅ Trả rỗng thay vì báo lỗi 400

#     invoice_id = invoices[0]["id"]

#     # 2️⃣ Lấy intent tương ứng
#     intents_res = (
#         client.schema("payment_svc")
#         .table("payment_intents")
#         .select("id, payer_user_id, created_at")
#         .eq("invoice_id", invoice_id)
#         .order("created_at", desc=True)
#         .execute()
#     )
#     intents = intents_res.data or []
#     if not intents:
#         return []

#     intent_ids = [i["id"] for i in intents]

#     # 3️⃣ Lấy payment tương ứng
#     payments_res = (
#         client.schema("payment_svc")
#         .table("payments")
#         .select("*")
#         .in_("intent_id", intent_ids)
#         .order("paid_at", desc=True)
#         .execute()
#     )
#     payments = payments_res.data or []
#     if not payments:
#         return []
    
#     # 4️⃣ Gộp thêm metadata intent
#     intent_map = {i["id"]: i for i in intents}
#     for p in payments:
#         info = intent_map.get(p["intent_id"], {})
#         p["created_at"] = info.get("created_at")
#         p["payer_user_id"] = info.get("payer_user_id")
#         # p["student_id"] = info.get("student_id")

#     return payments

async def get_payment_history_by_semester(student_id: str, semester_id: str, token_for_my_invoice: str):
    import asyncio

    client = get_supabase_client()

    # 1️⃣ Lấy invoice_id của kỳ này từ studentfee_svc
    invoice_res = (
        client.schema("studentfee_svc")
        .table("tuition_invoice")
        .select("id")
        .eq("student_id", student_id)
        .eq("semester_id", semester_id)
        .limit(1)
        .execute()
    )

    invoices = invoice_res.data or []
    if not invoices:
        return []

    # invoice_id = invoices[0]["id"]

    # 2️⃣ Lấy intent tương ứng
    # intents_res = (
    #     client.schema("payment_svc")
    #     .table("payment_intents")
    #     .select("id, payer_user_id, created_at, student_id")
    #     .eq("invoice_id", invoice_id)
    #     .order("created_at", desc=True)
    #     .execute()
    # )
    # 2️⃣ Lấy intent tương ứng
    intents_res = (
        client.schema("payment_svc")
        .table("payment_intents")
        .select("id, payer_user_id, created_at, student_id")
        .or_(f"student_id.eq.{student_id},payer_user_id.eq.{student_id}")  # ✅ lấy cả 2 phía
        .order("created_at", desc=True)
        .execute()
    )

    intents = intents_res.data or []
    if not intents:
        return []

    intent_ids = [i["id"] for i in intents]
    # 3️⃣ Lấy payment tương ứng
    payments_res = (
        client.schema("payment_svc")
        .table("payments")
        .select("*")
        .in_("intent_id", intent_ids)
        .order("paid_at", desc=True)
        .execute()
    )
    payments = payments_res.data or []
    if not payments:
        return []

    # 🧠 Tập hợp tất cả user_id có thể xuất hiện trong giao dịch:
    # bao gồm người nộp (payer), người được nộp (student), và chính mình
    all_user_ids = set()
    for i in intents:
        all_user_ids.add(i["payer_user_id"])
        all_user_ids.add(i["student_id"])
    # đảm bảo cả người đang xem (student_id param) cũng nằm trong map
    all_user_ids.add(student_id)

    # 🚀 Gọi song song để lấy tên user
    tasks = [user_get_username(uid, token_for_my_invoice) for uid in all_user_ids]
    names = await asyncio.gather(*tasks, return_exceptions=True)
    user_map = {
        uid: (name if not isinstance(name, Exception) else uid)
        for uid, name in zip(all_user_ids, names)
    }

    # 4️⃣ Gộp thêm metadata intent
    intent_map = {i["id"]: i for i in intents}
    for p in payments:
        info = intent_map.get(p["intent_id"], {})
        p["created_at"] = info.get("created_at")
        p["payer_user_id"] = info.get("payer_user_id")
        p["student_id"] = info.get("student_id")

        # 🧩 map thêm username cho cả người nộp và người được nộp
        p["payer_username"] = user_map.get(info.get("payer_user_id"), info.get("payer_user_id"))
        p["student_username"] = user_map.get(info.get("student_id"), info.get("student_id"))

    return payments
    # # 3️⃣ Lấy payment tương ứng
    # payments_res = (
    #     client.schema("payment_svc")
    #     .table("payments")
    #     .select("*")
    #     .in_("intent_id", intent_ids)
    #     .order("paid_at", desc=True)
    #     .execute()
    # )
    # payments = payments_res.data or []
    # if not payments:
    #     return []

    # import asyncio

    # # Gọi song song user_get_username cho tất cả payer/student
    # user_ids = list({i["payer_user_id"] for i in intents} | {student_id})
    # tasks = [user_get_username(uid, token_for_my_invoice) for uid in user_ids]  # ✅ truyền token
    # names = await asyncio.gather(*tasks, return_exceptions=True)
    # user_map = {uid: (name if not isinstance(name, Exception) else uid) for uid, name in zip(user_ids, names)}

    # print(user_map)
    # print(payments)


    # # 4️⃣ Gộp thêm metadata intent
    # intent_map = {i["id"]: i for i in intents}
    # for p in payments:
    #     info = intent_map.get(p["intent_id"], {})
    #     p["created_at"] = info.get("created_at")
    #     p["payer_user_id"] = info.get("payer_user_id")
    #     p["student_id"] = info.get("student_id")
    #     p["payer_username"] = user_map.get(info.get("payer_user_id"), info.get("payer_user_id"))
    #     p["student_username"] = user_map.get(info.get("student_id"), info.get("student_id"))  # ✅ thêm dòng này

    # return payments




