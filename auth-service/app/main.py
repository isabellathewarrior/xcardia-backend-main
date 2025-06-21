from fastapi import FastAPI
from app.application.routes import router
from app.infrastructure.database import init_db
from fastapi.middleware.cors import CORSMiddleware
from common_config import CORS_ORIGINS  # Ortak CORS yapılandırmasını buraya import ediyoruz
from fastapi.security import OAuth2PasswordBearer

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,  # Ortak yapılandırmadaki origin'leri kullanıyoruz
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "Authorization", "Content-Type"],  )
@app.on_event("startup")
def on_startup():
    init_db()

app.include_router(router)
