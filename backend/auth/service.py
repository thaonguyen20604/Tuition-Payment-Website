# service.py
import os
from fastapi import HTTPException, status
from auth.utils import create_access_token, verify_password, hash_password
from auth.repo import find_auth_by_username, create_auth
from auth.schemas import LoginResponse, SignupResponse
import httpx
from typing import Optional

USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://localhost:8002/user")

# def login_auth(username: str, password: str) -> LoginResponse:
#     auth = find_auth_by_username(username)
#     if not auth or not verify_password(password, auth["password_hash"]):
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid credentials"
#         )

#     token_data = {
#         "sub": auth["username"],                 # username
#         "user_id": auth.get("external_user_id")  # id bên user-service (nếu có)
#     }
#     access_token = create_access_token(token_data)
#     return LoginResponse(message="Login successful", username=username, access_token=access_token)
def login_auth(username: str, password: str) -> LoginResponse:
    print(f"[AuthService] Login attempt: {username}")
    auth = find_auth_by_username(username)
    if not auth:
        print("[AuthService] User not found in auth table")
    if not auth or not verify_password(password, auth["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token_data = {
        "sub": auth["external_user_id"],
        "username": auth.get("username"),
    }
    print(f"[AuthService] Login success, token_data={token_data}")
    access_token = create_access_token(token_data)
    return LoginResponse(message="Login successful", username=username, access_token=access_token)


def signup_auth(username: str, email: str, name: str, password: str) -> SignupResponse:
    if find_auth_by_username(username):
        raise HTTPException(status_code=400, detail="Username already exists")

    # tạo profile ở user-service
    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.post(
                f"{USER_SERVICE_URL}/create",
                json={"username": username, "email": email, "name": name}
            )
            r.raise_for_status()
            user = r.json()  # {"id": "...", ...}
    except httpx.HTTPError as e:
        raise HTTPException(status_code=400, detail=f"User service failed: {e}")

    pwd_hash = hash_password(password)
    _ = create_auth(username=username, password_hash=pwd_hash, external_user_id=user["id"])
    return SignupResponse(message="Signup successful", username=username)


# def signup_auth(
#     username: str,
#     email: str,
#     name: str,
#     password: str,
#     phone: Optional[str] = None,
#     gender: Optional[str] = None,   # truyền nguyên xi
# ) -> SignupResponse:
#     if find_auth_by_username(username):
#         raise HTTPException(status_code=409, detail="Username already exists")

#     # tạo profile ở user-service (thêm phone, gender nếu có)
#     payload = {"username": username, "email": email, "name": name}
#     if phone is not None:
#         payload["phone"] = phone
#     if gender is not None:
#         payload["gender"] = gender

#     try:
#         with httpx.Client(timeout=10.0) as client:
#             r = client.post(f"{USER_SERVICE_URL}/create", json=payload)
#             r.raise_for_status()
#             user = r.json()  # {"id": "...", ...}
#     except httpx.HTTPError as e:
#         raise HTTPException(status_code=400, detail=f"User service failed: {e}") from e

#     pwd_hash = hash_password(password)
#     create_auth(username=username, password_hash=pwd_hash, external_user_id=user["id"])
#     return SignupResponse(message="Signup successful", username=username)



# VALID_GENDERS = {"Nam", "Nữ"}  # khớp CHECK (gender in ('Nam','Nữ'))

# def signup_auth(
#     username: str,
#     email: str,
#     name: str,
#     password: str,
#     phone: Optional[str] = None,
#     gender: Optional[str] = None,
# ) -> SignupResponse:
#     """
#     Flow:
#       1) Check trùng username ở auth_svc.accounts
#       2) Gọi user-service tạo profile (user_svc.users)
#       3) Tạo account ở auth_svc.accounts (external_user_id = user.id)
#       4) Nếu (3) fail -> xóa user vừa tạo (bồi hoàn)
#     """

#     # 0) Validate input theo schema
#     if gender is not None and gender not in VALID_GENDERS:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Giới tính không hợp lệ (chỉ 'Nam' hoặc 'Nữ')"
#         )

#     # 1) Check username trùng ở AUTH
#     if find_auth_by_username(username):
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")

#     # 2) Tạo profile ở USER SERVICE
#     user_id: Optional[str] = None
#     try:
#         payload = {
#             "username": username,
#             "email": email,
#             "name": name,
#             "phone": phone,     # nullable
#             "gender": gender,   # nullable hoặc 'Nam'/'Nữ'
#         }
#         with httpx.Client(timeout=10.0) as client:
#             r = client.post(f"{USER_SERVICE_URL}/create", json=payload)
#             if r.status_code == status.HTTP_409_CONFLICT:
#                 # trùng username/email theo unique của user_svc.users
#                 msg = r.json().get("detail", "User already exists")
#                 raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=msg)
#             r.raise_for_status()
#             user = r.json()  # kỳ vọng {"id": "...", ...}
#             user_id = user.get("id")
#             if not user_id:
#                 raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="User service returned no id")
#     except HTTPException:
#         raise
#     except httpx.HTTPError as e:
#         raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"User service failed: {e}")

#     # 3) Tạo bản ghi AUTH
#     try:
#         pwd_hash = hash_password(password)
#         _ = create_auth(username=username, password_hash=pwd_hash, external_user_id=user_id)
#     except Exception as e:
#         # 4) Bồi hoàn: xóa user vừa tạo nếu tạo auth thất bại
#         try:
#             if user_id:
#                 with httpx.Client(timeout=10.0) as client:
#                     client.delete(f"{USER_SERVICE_URL}/{user_id}")  # user-svc nên có DELETE /user/{id}
#         except Exception:
#             pass  # ghi log nếu cần
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Create auth failed: {e}")

#     return SignupResponse(message="Signup successful", username=username)