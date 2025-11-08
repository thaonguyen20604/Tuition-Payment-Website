# # users/service.py
# from typing import Optional, Dict, Any, List
# from fastapi import HTTPException

# from users.repo import (
#     create_user as repo_create_user,
#     find_user_by_username as repo_find_by_username,
#     find_user_by_email as repo_find_by_email,
#     update_user_profile as repo_update_profile,
#     update_user_balance as repo_update_balance,
#     list_users as repo_list_users,
#     delete_user_by_username as repo_delete_user,
# )

# def _ensure_user_exists_by_username(username: str) -> Dict[str, Any]:
#     user = repo_find_by_username(username)
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")
#     return user



# def _normalize_amount(amount: float) -> float:
#     try:
#         a = float(amount)
#     except Exception:
#         raise HTTPException(status_code=400, detail="Invalid amount")
#     if a <= 0:
#         raise HTTPException(status_code=400, detail="Amount must be positive")
#     return a

# # --------- CREATE / GET / LIST ----------
# def create_profile_service(
#     *,
#     username: str,
#     email: str,
#     name: str,
#     phone: Optional[str] = None,
#     gender: Optional[str] = None,
# ) -> Dict[str, Any]:
#     # Uniqueness guard
#     if repo_find_by_username(username):
#         raise HTTPException(status_code=409, detail="Username already exists")
#     if repo_find_by_email(email):
#         raise HTTPException(status_code=409, detail="Email already exists")

#     try:
#         user = repo_create_user(username, email, name, phone=phone, gender=gender)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Create user failed: {e}")
#     return user

# def get_me_service(*, username_sub: str) -> Dict[str, Any]:
#     return _ensure_user_exists_by_username(username_sub)

# def get_user_by_username(username: str) -> Dict[str, Any]:

#     user = repo_find_by_username(username)
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")
#     return user

# def list_users_service(*, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
#     if limit < 0 or offset < 0:
#         raise HTTPException(status_code=400, detail="limit/offset must be non-negative")
#     return repo_list_users(limit=limit, offset=offset)

# # --------- UPDATE PROFILE ----------
# def update_profile_service(*, username: str, name=None, phone=None, gender=None, email=None):
#     me = _ensure_user_exists_by_username(username)
#     updates = {}
#     if name is not None:   updates["name"] = name
#     if phone is not None:  updates["phone"] = phone
#     if gender is not None: updates["gender"] = gender

#     if email is not None and email != me.get("email"):
#         other = repo_find_by_email(email)
#         if other and other.get("username") != username:
#             raise HTTPException(status_code=409, detail="Email already exists")
#         updates["email"] = email

#     updated = repo_update_profile(username, updates)
#     if not updated:
#         raise HTTPException(status_code=500, detail="Update failed")
#     return updated


# # --------- BALANCE OPS ----------
# def credit_balance_service(*, username: str, amount: float) -> Dict[str, Any]:
#     a = _normalize_amount(amount)
#     user = _ensure_user_exists_by_username(username)
#     new_balance = float(user.get("balance", 0.0)) + a
#     updated = repo_update_balance(username, new_balance)
#     if not updated:
#         raise HTTPException(status_code=500, detail="Credit failed")
#     return updated

# def debit_balance_service(*, username: str, amount: float) -> Dict[str, Any]:
#     a = _normalize_amount(amount)
#     user = _ensure_user_exists_by_username(username)
#     current = float(user.get("balance", 0.0))
#     if current < a:
#         raise HTTPException(status_code=400, detail="Insufficient balance")
#     new_balance = current - a
#     updated = repo_update_balance(username, new_balance)
#     if not updated:
#         raise HTTPException(status_code=500, detail="Debit failed")
#     return updated

# # --------- DELETE ----------
# def delete_user_service(*, username: str) -> int:
#     _ensure_user_exists_by_username(username)
#     deleted = repo_delete_user(username)
#     if deleted <= 0:
#         raise HTTPException(status_code=500, detail="Delete failed")
#     return deleted

# user_svc/service.py
# user_svc/service.py
from decimal import Decimal
from fastapi import HTTPException
from typing import Dict, Any
from .repo import (
    get_user_by_id,
    find_user_by_username,
    update_balance_if_unchanged,
    create_user,
)

def create_user_service(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tạo profile: {username, email, name}
    Rely vào unique constraint DB; nếu trùng, trả 400 với message từ DB.
    """
    if not payload.get("username") or not payload.get("email") or not payload.get("name"):
        raise HTTPException(status_code=400, detail="Missing required fields")
    try:
        row = create_user(payload)
        return row
    except Exception as e:
        # ví dụ: duplicate key value violates unique constraint "users_username_key"
        raise HTTPException(status_code=400, detail=str(e))

def get_user_by_id_service(user_id: str) -> Dict[str, Any]:
    u = get_user_by_id(user_id)
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    return u

def get_me_service(claims: dict) -> Dict[str, Any]:
    user_id = claims.get("sub")
    if user_id:
        u = get_user_by_id(user_id)
        if u:
            return u
    username = claims.get("username")
    if username:
        u = find_user_by_username(username)
        if u:
            return u
    raise HTTPException(status_code=404, detail="User not found")

def get_user_by_username_service(username: str) -> Dict[str, Any]:
    u = find_user_by_username(username)
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    return u

def debit_user_service(user_id: str, amount: Decimal) -> Dict[str, Any]:
    if amount is None or amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid amount")

    u = get_user_by_id(user_id)
    if not u:
        raise HTTPException(status_code=404, detail="User not found")

    old_balance = Decimal(str(u["balance"]))
    if old_balance < amount:
        raise HTTPException(status_code=409, detail="Insufficient funds")

    new_balance = old_balance - amount
    row = update_balance_if_unchanged(user_id, old_balance, new_balance)
    if not row:
        raise HTTPException(status_code=409, detail="Balance changed, please retry")
    return row

# Thêm cho tìm mã sinh viên thanh toán hộ
def get_user_by_username_service(username: str):
    return find_user_by_username(username)

def deposit_user_service(user_id: str, amount: Decimal) -> Dict[str, Any]:
    """
    Nạp tiền thật vào tài khoản.
    """
    if amount is None or amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid amount")

    u = get_user_by_id(user_id)
    if not u:
        raise HTTPException(status_code=404, detail="User not found")

    old_balance = Decimal(str(u["balance"]))
    new_balance = old_balance + amount

    row = update_balance_if_unchanged(user_id, old_balance, new_balance)
    if not row:
        raise HTTPException(status_code=409, detail="Balance changed, please retry")

    return row
