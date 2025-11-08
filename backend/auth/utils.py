import os
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import jwt, JWTError
from config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRE_MINUTES

_pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(plain: str) -> str:
    return _pwd_ctx.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_ctx.verify(plain, hashed)


def create_access_token(data: Dict[str, Any]) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=JWT_EXPIRE_MINUTES)
    to_encode.update({
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "iss": "auth_svc"
    })
    token = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    print(f"[AuthService] Created token for user={data.get('sub')}, exp={expire.isoformat()}")
    print(f"[AuthService] Token payload: {to_encode}")
    print("Auth JWT_SECRET startswith:", JWT_SECRET[:10], "len=", len(JWT_SECRET))
    return token

def decode_token(token: str):
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])


