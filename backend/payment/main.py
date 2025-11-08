from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from payment.router import router

app = FastAPI(title="payment_svc", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_headers=["*"],
    allow_methods=["*"],
    allow_credentials=True
)

app.include_router(router)

@app.get("/healthz")
def healthz():
    return {"ok": True}

@app.get("/")
def root():
    return {"message": "Payment Service OK"}
