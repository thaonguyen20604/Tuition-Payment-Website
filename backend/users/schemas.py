# # users/schemas.py
# from pydantic import BaseModel, EmailStr, Field
# from typing import Optional, List

# class UserCreate(BaseModel):
#     username: str = Field(min_length=3)
#     email: EmailStr
#     name: str
#     phone: Optional[str] = None
#     gender: Optional[str] = None

# class UserUpdate(BaseModel):
#     name: Optional[str] = None
#     email: Optional[EmailStr] = None
#     phone: Optional[str] = None
#     gender: Optional[str] = None


# class BalanceReq(BaseModel):
#     amount: float

# class UserPublic(BaseModel):
#     id: str
#     username: str
#     email: EmailStr
#     name: str
#     balance: float
#     created_at: Optional[str] = None
#     phone: Optional[str] = None
#     gender: Optional[str] = None

# class UserList(BaseModel):
#     items: List[UserPublic]
#     limit: int
#     offset: int


# user_svc/schemas.py
# user_svc/schemas.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from decimal import Decimal
from typing import Annotated
from pydantic import Field

Money = Annotated[Decimal, Field(max_digits=18, decimal_places=2)]

class CreateUserIn(BaseModel):
    username: str
    email: EmailStr
    name: str

class UserPublic(BaseModel):
    id: str
    username: str
    email: EmailStr
    name: str
    balance: Money
    created_at: Optional[str] = None
    phone: Optional[str] = None
    gender: Optional[str] = None

class DebitRequest(BaseModel):
    amount: Annotated[Decimal, Field(gt=0, max_digits=18, decimal_places=2)]

class DebitResponse(BaseModel):
    new_balance: Money

