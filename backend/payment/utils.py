import os
from datetime import datetime
from typing import List, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError, ExpiredSignatureError


JWT_SECRET = os.getenv("JWT_SECRET", "default-secret")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

security = HTTPBearer(auto_error=False)


def decode_token(token: str):
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM], options={"verify_aud": False})
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    - Lấy Bearer token từ header
    - Decode -> claims
    - Bắt buộc có 'sub'
    - ✨ GẮN THÊM: claims['_raw_token'] = token để forward sang service khác
    - (Tuỳ chọn) claims['user_id'] = sub nếu các service khác đang đọc 'user_id'
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header"
        )
    token = credentials.credentials
    try:
        claims = decode_token(token)
        if "sub" not in claims:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token claims: missing 'sub'"
            )
        # giữ token gốc để forward cross-service
        claims["_raw_token"] = token
        # đồng bộ nếu nơi khác đang đọc user_id
        claims.setdefault("user_id", claims["sub"])
        return claims
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )