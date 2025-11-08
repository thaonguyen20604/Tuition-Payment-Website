from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from studentfee.router import router as studentfee_router

def create_app() -> FastAPI:
    app = FastAPI(title="StudentFee Service")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(studentfee_router, tags=["studentfee"])

    @app.get("/")
    def root():
        return {"message": "StudentFee Service OK"}

    return app

app = create_app()
