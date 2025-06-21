from fastapi import FastAPI
from .infrastructure.routes import router

app = FastAPI()

app.include_router(router, prefix="/api", tags=["hsm"]) 