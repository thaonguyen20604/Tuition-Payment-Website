# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from users.router import router as user_router

def create_app() -> FastAPI:
    app = FastAPI(title="User Service")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(user_router, tags=["users"])

    @app.get("/")
    def root():
        return {"message": "User Service OK"}

    return app

app = create_app()
