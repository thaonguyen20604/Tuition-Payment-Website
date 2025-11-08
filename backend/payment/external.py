# payment_svc/external.py
import httpx
from fastapi import HTTPException
import config
from typing import Optional, Dict, Any


async def _call(req):
    try:
        r = await req
        r.raise_for_status()
        # Robust: nếu không phải JSON thì trả text
        try:
            return r.json()
        except ValueError:
            return {"_raw": r.text}
    except httpx.HTTPStatusError as e:
        # Trả message rõ ràng kèm method + path từ upstream
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"{e.request.method} {e.request.url.path}: {e.response.text}"
        )
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Upstream unreachable: {e}")


def _auth_headers(token: Optional[str]) -> Dict[str, str]:
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


# =========================
# user_svc
# =========================

async def user_get_by_id(user_id: str, token:Optional[str]=None) -> dict:
    """
    GET /user/by-id/{user_id} - yêu cầu Authorization
    """
    async with httpx.AsyncClient(timeout=10) as client:
        return await _call(client.get(
            f"{config.USER_SVC_URL}/user/by-id/{user_id}",
            headers=_auth_headers(token),
        ))


async def user_debit(user_id: str, amount: float, token:Optional[str]=None) -> dict:
    """
    POST /user/{user_id}/debit - yêu cầu Authorization
    body: { "amount": <float> }
    """
    async with httpx.AsyncClient(timeout=10) as client:
        return await _call(client.post(
            f"{config.USER_SVC_URL}/user/{user_id}/debit",
            headers=_auth_headers(token),
            json={"amount": amount},
        ))
async def user_get_username(user_id: str, token: Optional[str] = None) -> str:
    async with httpx.AsyncClient(timeout=10) as client:
        data = await _call(client.get(
            f"{config.USER_SVC_URL}/user/by-id/{user_id}",
            headers=_auth_headers(token),
        ))
        print("📨 user_get_username response:", data)
        return data.get("username") or data.get("email") or user_id



# =========================
# studentfee_svc
# =========================

async def sf_get_invoice_current_of(student_id: str, token:Optional[str] = None) -> dict:
    """
    GET /studentfee/invoice/{student_id}
    Tuỳ policy có thể public; truyền token nếu service yêu cầu.
    """
    async with httpx.AsyncClient(timeout=10) as client:
        return await _call(client.get(
            f"{config.STUDENTFEE_SVC_URL}/studentfee/invoice/{student_id}",
            headers=_auth_headers(token),
        ))


async def sf_get_my_invoice(token:Optional[str], semester_id: Optional[str]) -> dict:
    """
    GET /studentfee/my-invoice?semester_id=...
    Bắt buộc Authorization vì lấy hóa đơn của chính user.
    """
    params: Dict[str, Any] = {}
    if semester_id:
        params["semester_id"] = semester_id

    async with httpx.AsyncClient(timeout=10) as client:
        return await _call(client.get(
            f"{config.STUDENTFEE_SVC_URL}/studentfee/my-invoice",
            headers=_auth_headers(token),
            params=params,
        ))


async def sf_pay(invoice_id: str, token:Optional[str]=None) -> dict:
    """
    POST /studentfee/pay/{invoice_id}
    Thao tác nhạy cảm -> nên yêu cầu Authorization.
    """
    async with httpx.AsyncClient(timeout=10) as client:
        return await _call(client.post(
            f"{config.STUDENTFEE_SVC_URL}/studentfee/pay/{invoice_id}",
            headers=_auth_headers(token),
        ))


