# router.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from auth.schemas import LoginRequest, LoginResponse, SignupRequest, SignupResponse
from auth.service import login_auth, signup_auth
from auth.utils import decode_token

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()

@router.post("/login", response_model=LoginResponse)
def login(req: LoginRequest):
    return login_auth(req.username, req.password)

@router.post("/signup", response_model=SignupResponse)
def signup(req: SignupRequest):
    return signup_auth(username=req.username, email=req.email, name=req.name, password=req.password)

@router.get("/verify")
def verify(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        claims = decode_token(token)
        return {"valid": True, "claims": claims}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


