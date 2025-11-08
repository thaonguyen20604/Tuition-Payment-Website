import os
from datetime import datetime
from typing import List, Dict
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError


JWT_SECRET = os.getenv("JWT_SECRET", "default-secret")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

security = HTTPBearer(auto_error=False)

def decode_token(token: str):
    return jwt.decode(
        token,
        JWT_SECRET,
        algorithms=[JWT_ALGORITHM],
        options={"verify_aud": False}
    )

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
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
        return claims
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )


# Tính tổng học phí từ invoice_items
def calc_total_amount(invoice_items: List[Dict]) -> float:
    return sum(item.get("amount", 0) for item in invoice_items)