from fastapi import FastAPI, Request, Response, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from starlette.responses import StreamingResponse
import httpx

AUTH_BASE = "http://localhost:8001/auth"
USER_BASE = "http://localhost:8002"
STUDENTFEE_BASE = "http://localhost:8003/studentfee"
PAYMENT_BASE = "http://localhost:8004/payment"



USER_FWD_PREFIX = "/user"   # "" nếu user-svc không prefix

TIMEOUT_SECS = 30.0
ALLOWED_ORIGINS = [
    "http://localhost:5173", "http://127.0.0.1:5173",  # Vite
    "http://localhost:3000", "http://127.0.0.1:3000",
]

app = FastAPI(
    title="Simple API Gateway",
    version="1.0.0",
    swagger_ui_parameters={"persistAuthorization": True},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-Requested-With", "Origin"],
    expose_headers=["Authorization", "Content-Type", "Set-Cookie"],
    max_age=600,
)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(title=app.title, version=app.version, routes=app.routes)
    schema.setdefault("components", {}).setdefault("securitySchemes", {})["bearerAuth"] = {
        "type": "http", "scheme": "bearer", "bearerFormat": "JWT",
    }
    app.openapi_schema = schema
    return app.openapi_schema

app.openapi = custom_openapi

HOP_BY_HOP = {
    "connection","keep-alive","proxy-authenticate","proxy-authorization",
    "te","trailers","transfer-encoding","upgrade","accept-encoding",
    "host","content-length",
}
def _clean_headers(h: dict, block: set) -> dict:
    return {k: v for k, v in h.items() if k.lower() not in block}

async def _proxy(request: Request, upstream_url: str) -> Response:
    if request.method == "OPTIONS":
        return Response(status_code=204)

    fwd_headers = _clean_headers(dict(request.headers), HOP_BY_HOP)
    body = None if request.method in ("GET","HEAD") else await request.body()

    print("[GW]", request.method, upstream_url)
    async with httpx.AsyncClient(timeout=TIMEOUT_SECS, follow_redirects=False) as c:
        upstream = await c.request(
            method=request.method,
            url=upstream_url,
            params=request.query_params,
            content=body,
            headers=fwd_headers,
        )

    resp_headers = _clean_headers(dict(upstream.headers), HOP_BY_HOP)
    if upstream.status_code in (204, 304):
        return Response(status_code=upstream.status_code, headers=resp_headers)

    if upstream.is_stream_consumed:
        return Response(content=upstream.content, status_code=upstream.status_code, headers=resp_headers)

    return StreamingResponse(upstream.aiter_bytes(), status_code=upstream.status_code, headers=resp_headers)

# ===== AUTH =====
# Route *riêng* cho login: CHỈ POST để tránh gọi nhầm GET
@app.post("/auth/login", tags=["auth"])
async def gw_auth_login(request: Request, payload: dict = Body(...)):
    return await _proxy(request, f"{AUTH_BASE}/login")

# Các auth endpoint khác (nếu có)
@app.api_route("/auth/{path:path}",
               methods=["GET","PUT","PATCH","DELETE","OPTIONS","HEAD"],
               tags=["auth"])
async def gw_auth_rest(path: str, request: Request):
    return await _proxy(request, f"{AUTH_BASE}/{path}")

# ===== USER =====
@app.api_route("/user/{path:path}",
               methods=["GET","POST","PUT","PATCH","DELETE","OPTIONS","HEAD"],
               tags=["user"])
async def gw_user(path: str, request: Request):
    base = f"{USER_BASE}{USER_FWD_PREFIX}".rstrip("/")
    return await _proxy(request, f"{base}/{path}".rstrip("/"))

@app.get("/", tags=["gateway"])
def root():
    return {"message": "API Gateway running"}


# ===== STUDENTFEE =====
@app.api_route("/studentfee/{path:path}",
               methods=["GET","POST","PUT","PATCH","DELETE","OPTIONS","HEAD"],
               tags=["studentfee"])
async def gw_studentfee(path: str, request: Request):
    return await _proxy(request, f"{STUDENTFEE_BASE}/{path}".rstrip("/"))



# ===== PAYMENT =====
@app.api_route("/payment/{path:path}",
               methods=["GET","POST","PUT","PATCH","DELETE","OPTIONS","HEAD"],
               tags=["payment"])
async def gw_payment(path: str, request: Request):
    return await _proxy(request, f"{PAYMENT_BASE}/{path}".rstrip("/"))

