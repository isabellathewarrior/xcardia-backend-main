from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.xray_scan_evaluation_router import xray_scan_evaluation_router
from app.routers.openai_router import openai_router
from app.db.base import init_db

app = FastAPI(
    title="Xcardia AI Service",
    description="Service for X-Ray analysis and LLM-based interpretation.",
    version="1.0.0",
)

# CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    init_db()

app.include_router(xray_scan_evaluation_router)
app.include_router(openai_router)

@app.get("/")
async def root():
    return {"message": "Welcome to the Xcardia AI Service!"} 