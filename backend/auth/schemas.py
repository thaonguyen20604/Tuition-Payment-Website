# schemas.py
from pydantic import BaseModel, EmailStr

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    message: str
    username: str
    access_token: str
    token_type: str = "bearer"

class SignupRequest(BaseModel):
    username: str
    email: EmailStr
    name: str
    password: str

class SignupResponse(BaseModel):
    message: str
    username: str
