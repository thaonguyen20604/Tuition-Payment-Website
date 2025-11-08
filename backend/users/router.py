# # users/router.py
from fastapi import APIRouter, Depends, HTTPException
from decimal import Decimal
from .schemas import UserPublic, DebitRequest, DebitResponse, CreateUserIn
from .service import (
    create_user_service,
    get_user_by_id_service,
    get_user_by_username_service,
    get_me_service,
    debit_user_service,
    deposit_user_service,
)
from .utils import get_current_user



router = APIRouter(prefix="/user", tags=["users"])

# --- PUBLIC: không cần token ---
@router.post("/create", response_model=UserPublic)
def api_create_user(body: CreateUserIn):
    return create_user_service(body.dict())

# --- PROTECTED: require_auth gắn TRỰC TIẾP vào hàm ---
@router.get("/me", response_model=UserPublic)
def api_get_me(claims: dict = Depends(get_current_user)):
    return get_me_service(claims)

@router.get("/by-id/{user_id}", response_model=UserPublic)
def api_get_user_by_id(user_id: str, _: dict = Depends(get_current_user)):
    return get_user_by_id_service(user_id)

@router.get("/by-username/{username}", response_model=UserPublic)
def api_get_user_by_username(username: str, _: dict = Depends(get_current_user)):
    return get_user_by_username_service(username)

@router.post("/{user_id}/debit", response_model=DebitResponse)
def api_debit_user(user_id: str, body: DebitRequest, _: dict = Depends(get_current_user)):
    row = debit_user_service(user_id, Decimal(str(body.amount)))
    return {"new_balance": row["balance"]}

@router.post("/{user_id}/deposit")
def api_deposit_user(user_id: str, body: DebitRequest, _: dict = Depends(get_current_user)):
    """
    Nạp tiền thật vào tài khoản người dùng.
    """
    row = deposit_user_service(user_id, Decimal(str(body.amount)))
    return {"new_balance": row["balance"]}

# from fastapi import APIRouter, HTTPException, Depends, Query
# from users.schemas import UserCreate, UserPublic, UserUpdate, BalanceReq, UserList
# from users.utils import get_current_user

# from users.service import (
#     create_profile_service,
#     get_me_service,
#     get_user_by_username,
#     list_users_service,
#     update_profile_service,
#     credit_balance_service,
#     debit_balance_service,
#     delete_user_service,
# )

# router = APIRouter(prefix="/user", tags=["users"])

# @router.post("/create", response_model=UserPublic)
# def create_profile(body: UserCreate):
#     return create_profile_service(
#         username=body.username,
#         email=body.email,
#         name=body.name,
#         phone=body.phone,
#         gender=body.gender,
#     )

# @router.get("/me", response_model=UserPublic)
# def get_me(claims: dict = Depends(get_current_user)):
#     return get_me_service(username_sub=claims["sub"])

# @router.get("/{username}", response_model=UserPublic)
# def api_get_user_by_username(
#     username: str,
#     _: dict = Depends(get_current_user),   # ⬅️ bắt buộc phải đăng nhập/authorize
# ):
#     """
#     GET /users/by-username/{username}
#     MSSV = username
#     """
#     return get_user_by_username(username)



# @router.get("/all", response_model=UserList)
# def list_users(
#     _: dict = Depends(get_current_user),
#     limit: int = Query(100, ge=0, le=1000),
#     offset: int = Query(0, ge=0),
# ):
#     items = list_users_service(limit=limit, offset=offset)
#     return {"items": items, "limit": limit, "offset": offset}





# @router.put("/update", response_model=UserPublic)
# def update_me(body: UserUpdate, claims: dict = Depends(get_current_user)):
#     return update_profile_service(
#         username=claims["sub"],
#         email=body.email,
#         name=body.name,
#         phone=body.phone,
#         gender=body.gender,
#     )

# @router.post("/balance/credit", response_model=UserPublic)
# def credit_balance(body: BalanceReq, claims: dict = Depends(get_current_user)):
#     return credit_balance_service(username=claims["sub"], amount=body.amount)

# @router.post("/balance/debit", response_model=UserPublic)
# def debit_balance(body: BalanceReq, claims: dict = Depends(get_current_user)):
#     return debit_balance_service(username=claims["sub"], amount=body.amount)

# @router.delete("/delete", status_code=204)
# def delete_me(claims: dict = Depends(get_current_user)):
#     delete_user_service(username=claims["sub"])
#     return


# user_svc/router.py
# user_svc/router.py
# from fastapi import APIRouter, Depends, HTTPException
# from decimal import Decimal
# from .schemas import UserPublic, DebitRequest, DebitResponse, CreateUserIn
# from .service import (
#     create_user_service,
#     get_user_by_id_service,
#     get_user_by_username_service,
#     get_me_service,
#     debit_user_service,
# )
# from .utils import require_auth

# # # ✅ Public router: không yêu cầu token cho tạo profile từ auth_svc
# # public_router = APIRouter(prefix="/users", tags=["users-public"])

# # @public_router.post("/create", response_model=UserPublic)
# # def api_create_user(body: CreateUserIn):
# #     return create_user_service(body.dict())

# router = APIRouter(prefix="/user", tags=["users"])

# # --- PUBLIC: không cần token ---
# @router.post("/create", response_model=UserPublic)
# def api_create_user(body: CreateUserIn):
#     return create_user_service(body.dict())

# # --- PROTECTED: require_auth gắn TRỰC TIẾP vào hàm ---
# @router.get("/me", response_model=UserPublic)
# def api_get_me(claims: dict = Depends(require_auth)):
#     return get_me_service(claims)

# @router.get("/by-id/{user_id}", response_model=UserPublic)
# def api_get_user_by_id(user_id: str, _: dict = Depends(require_auth)):
#     return get_user_by_id_service(user_id)

# @router.get("/by-username/{username}", response_model=UserPublic)
# def api_get_user_by_username(username: str, _: dict = Depends(require_auth)):
#     return get_user_by_username_service(username)

# @router.post("/{user_id}/debit", response_model=DebitResponse)
# def api_debit_user(user_id: str, body: DebitRequest, _: dict = Depends(require_auth)):
#     row = debit_user_service(user_id, Decimal(str(body.amount)))
#     return {"new_balance": row["balance"]}

# # Thêm để tìm mã sinh viên thanh toán hộ
# @router.get("/find-by-username/{username}", response_model=UserPublic)
# def find_by_username(username: str):
#     user = get_user_by_username_service(username)
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")
#     return user
