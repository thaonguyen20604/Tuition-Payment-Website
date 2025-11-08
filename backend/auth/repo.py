# repo.py
from typing import Optional, Dict, Any, List
from auth.db import get_supabase_client

SCHEMA = "auth_svc"
TABLE = "accounts"

def _tb(): #tạo 1 query builder cho bảng auth_svc.accounts
    return get_supabase_client().schema(SCHEMA).table(TABLE)

def _first_or_none(data: Optional[List[Dict]]) -> Optional[Dict[str, Any]]:
    if isinstance(data, list) and data:
        return data[0]
    return None

def find_auth_by_username(username: str) -> Optional[Dict[str, Any]]: #login
    res = (
        _tb()
        .select("id, username, password_hash, external_user_id")
        .eq("username", username)
        .limit(1)
        .execute()
    )
    return _first_or_none(res.data)

def create_auth(username: str, password_hash: str, external_user_id: str) -> Dict[str, Any]:
    res = (
        _tb()
        .insert(
            {
                "username": username,
                "password_hash": password_hash,
                "external_user_id": external_user_id, #id tham chiếu sang user-service (giữ cho đúng mô hình microservice: auth và user tách biệt).
            },
            returning="representation",  
        )
        .execute()
    )
    return res.data[0]
