from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
from payment.schemas import CreateIntentBody, SendOtpResp, ConfirmBody, IntentPublic, ConfirmResp
from payment.service import create_intent_service, send_otp_service, confirm_service
from payment.utils import get_current_user

router = APIRouter(prefix="/payment", tags=["payment"])

@router.post("/intents", response_model=IntentPublic)
async def api_create_intent(
    body: CreateIntentBody,
    semester_id: Optional[str] = Query(None),
    claims: dict = Depends(get_current_user),
):
    try:
        token = claims.get("_raw_token")  # forward sang studentfee_svc
        intent = await create_intent_service(
            payer_user_id=claims["sub"],
            token_for_my_invoice=token,
            student_id=body.student_id,
            semester_id=body.semester_id or semester_id,
        )
        return intent
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/intents/{intent_id}/send-otp", response_model=SendOtpResp)
async def api_send_otp(intent_id: str, _: dict = Depends(get_current_user)):
    try:
        _ = await send_otp_service(intent_id)
        return {"intent_id": intent_id, "otp_sent": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# @router.post("/intents/{intent_id}/confirm", response_model=ConfirmResp)
# async def api_confirm(intent_id: str, body: ConfirmBody, _: dict = Depends(get_current_user)):
#     try:
#         return await confirm_service(intent_id, body.otp)
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=str(e))


# @router.post("/intents/{intent_id}/confirm", response_model=ConfirmResp)
# async def api_confirm(intent_id: str, body: ConfirmBody, claims: dict = Depends(get_current_user)):
#     try:
#         return await confirm_service(intent_id, body.otp, claims["_raw_token"])
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=str(e))


# @router.post("/intents/{intent_id}/confirm", response_model=ConfirmResp)
# async def api_confirm(intent_id: str, body: ConfirmBody, claims: dict = Depends(get_current_user)):
#     try:
#         token = claims.get("_raw_token")
#         return await confirm_service(intent_id, body.otp, token)
#     except HTTPException as e:
#         # giữ nguyên mã lỗi (401/404/500...) từ service layer/external
#         raise e
#     except Exception as e:
#         # lỗi không đoán định được -> 500
#         raise HTTPException(status_code=500, detail=f"payment_svc: {e}")
@router.post("/intents/{intent_id}/confirm", response_model=ConfirmResp)
async def api_confirm(intent_id: str, body: ConfirmBody, claims: dict = Depends(get_current_user)):
    try:
        token = claims.get("_raw_token")
        return await confirm_service(intent_id, body.otp, token)

    except ValueError as e:
        # lỗi hợp lệ kiểu: OTP sai, OTP hết hạn, intent không tồn tại
        raise HTTPException(status_code=422, detail=f"payment_svc: {e}")

    except HTTPException as e:
        # giữ nguyên mã lỗi từ service khác (401, 404, 403...)
        raise e

    except Exception as e:
        # lỗi thật (lỗi DB, external fail, logic bug)
        raise HTTPException(status_code=500, detail=f"payment_svc: {e}")

@router.post("/intents/{intent_id}/cancel")
async def api_cancel_intent(intent_id: str, claims: dict = Depends(get_current_user)):
    try:
        from payment.repo import mark_failed
        mark_failed(intent_id, "failed")
        return {"intent_id": intent_id, "status": "failed"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# @router.get("/payments/history/{student_id}/{semester_id}")
# async def api_payment_history_by_semester(student_id: str, semester_id: str):
#     from payment.repo import get_payment_history_by_semester
#     try:
#         history = get_payment_history_by_semester(student_id, semester_id)
#         return history
#     except Exception as e:
#         print("🔥 [DEBUG] payment history error:", e)
#         raise HTTPException(status_code=400, detail=str(e))
@router.get("/payments/history/{student_id}/{semester_id}")
async def api_payment_history_by_semester(
    student_id: str,
    semester_id: str,
    claims: dict = Depends(get_current_user),
):
    from payment.repo import get_payment_history_by_semester
    try:
        token = claims.get("_raw_token")  # ✅ Lấy token từ claims
        history = await get_payment_history_by_semester(student_id, semester_id, token)
        return history
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))



