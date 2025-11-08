# # users/repo.py
# from typing import Optional, Dict, Any, List, Tuple
# from decimal import Decimal
# from users.db import get_supabase_client

# SCHEMA = "user_svc"
# TABLE  = "users"

# def _tb():
#     return get_supabase_client().schema(SCHEMA).table(TABLE)

# def _normalize_row(row: Dict[str, Any]) -> Dict[str, Any]:
#     bal = row.get("balance", 0)
#     if isinstance(bal, Decimal):
#         row["balance"] = float(bal)
#     elif isinstance(bal, (int, float)):
#         row["balance"] = float(bal)
#     else:
#         try:
#             row["balance"] = float(bal or 0)
#         except Exception:
#             row["balance"] = 0.0
#     return row

# def _first_or_none(data: Optional[List[Dict]]) -> Optional[Dict[str, Any]]:
#     if isinstance(data, list) and data:
#         return _normalize_row(data[0])
#     return None

# # ---------- Create / Read ----------
# def create_user(
#     username: str,
#     email: str,
#     name: str,
#     phone: Optional[str] = None,
#     gender: Optional[str] = None,
# ) -> Dict[str, Any]:
#     payload = {"username": username, "email": email, "name": name}
#     if phone is not None:
#         payload["phone"] = phone
#     if gender is not None:
#         payload["gender"] = gender

#     res = _tb().insert(payload, returning="representation").execute()
#     if not res.data:
#         raise RuntimeError("Insert returned no data")
#     return _normalize_row(res.data[0])

# def find_user_by_username(username: str) -> Optional[Dict[str, Any]]:
#     res = (
#         _tb()
#         .select("id, username, email, name, phone, gender, balance, created_at")
#         .eq("username", username)
#         .limit(1)
#         .execute()
#     )
#     return _first_or_none(res.data)

# def find_user_by_email(email: str) -> Optional[Dict[str, Any]]:
#     res = (
#         _tb()
#         .select("id, username, email, name, phone, gender, balance, created_at")
#         .eq("email", email)
#         .limit(1)
#         .execute()
#     )
#     return _first_or_none(res.data)


# # ---------- Update ----------
# def update_user_profile(username: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
#     if not updates:
#         return find_user_by_username(username)
#     res = (
#         _tb()
#         .update(updates, returning="representation")
#         .eq("username", username)
#         .execute()
#     )
#     return _first_or_none(res.data)

# def update_user_balance(username: str, new_balance: float) -> Optional[Dict[str, Any]]:
#     res = (
#         _tb()
#         .update({"balance": new_balance}, returning="representation")
#         .eq("username", username)
#         .execute()
#     )
#     return _first_or_none(res.data)

# # ---------- List / Delete ----------
# def list_users(limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
#     # Supabase chưa có offset native => dùng range
#     start = offset
#     end = offset + limit - 1 if limit > 0 else None
#     q = _tb().select("*").order("created_at", desc=True)
#     if end is not None:
#         q = q.range(start, end)
#     res = q.execute()
#     data = res.data or []
#     return [_normalize_row(r) for r in data]

# def delete_user_by_username(username: str) -> int:
#     res = _tb().delete().eq("username", username).execute()
#     # res.data là danh sách record đã xóa (nếu returning), Supabase Python client có thể không trả count
#     # Trả về số bản ghi xóa ước lượng
#     return len(res.data or [])


# user_svc/repo.py
# user_svc/repo.py
from typing import Optional, Dict, Any
from decimal import Decimal
from .db import get_supabase_client

SCHEMA = "user_svc"
TABLE  = "users"

def _tb():
    return get_supabase_client().schema(SCHEMA).table(TABLE)

def _first(data):
    return data[0] if isinstance(data, list) and data else None

def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    res = (_tb()
           .select("id, username, email, name, phone, gender, balance, created_at")
           .eq("id", user_id).limit(1).execute())
    return _first(res.data)

def find_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    res = (_tb()
           .select("id, username, email, name, phone, gender, balance, created_at")
           .eq("username", username).limit(1).execute())
    return _first(res.data)

def create_user(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    data = {username, email, name}
    balance để DB default = 0.00
    """
    res = (_tb()
           .insert(
               {
                   "username": data["username"],
                   "email": data["email"],
                   "name": data["name"],
                    
               },
               returning="representation",
           )
           .execute())
    return res.data[0]

def update_balance_if_unchanged(user_id: str, old_balance: Decimal, new_balance: Decimal) -> Optional[Dict[str, Any]]:
    res = (_tb()
           .update({"balance": str(new_balance)}, returning="representation")
           .eq("id", user_id)
           .eq("balance", str(old_balance))
           .execute())
    return _first(res.data)
