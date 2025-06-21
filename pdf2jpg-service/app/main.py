from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from fastapi import Depends
from app.domain.models import Base
from app.infrastructure.database import engine
from app.application.routes import router

# Initialize DB
def init_db():
    Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Xcardia Project",
    description="XCARDIA : pdf2image-service",
    version="1.0.0",
    openapi_tags=[{"name": "PDF", "description": "PDF dönüşüm işlemleri"}],
    dependencies=[Depends(HTTPBearer())]
)

# Router'ı uygulamaya ekle
app.include_router(router)

@app.on_event("startup")
def on_startup():
    init_db()

# CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Welcome to FastAPI!"}