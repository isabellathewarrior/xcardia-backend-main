from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.infrastructure.database import SessionLocal
from app.domain.services import convert_pdf_to_jpg
from app.domain.models import ConversionLog
import shutil
import os
import uuid
from datetime import datetime
from fastapi import Security 
from app.infrastructure.security import get_current_user
from fastapi.responses import FileResponse
router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/convert/")
async def convert_pdf(  
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user) 
):
    user_id = current_user["user_id"]
    user_email = current_user["email"]

    # Dosya adını ve yolu oluştur
    filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = f"/app/temp/{filename}"

    # PDF dosyasını diske kaydet
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        # PDF'i JPG'e dönüştür
        image_paths = convert_pdf_to_jpg(file_path)

        # Log kaydı oluştur
        conversion_log = ConversionLog(
            user_id=user_id, 
            user_email=user_email,
            filename=file.filename, 
            jpg_output_path=", ".join(image_paths),
            converted_at=datetime.utcnow()
        )
        db.add(conversion_log)
        db.commit()

        return JSONResponse(content={
            "message": "Conversion successful",
            "user": user_email,
            "images": [
                f"http://localhost:8001/download/{os.path.basename(p)}"
                for p in image_paths
            ]
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


@router.get("/logs/")
def get_logs(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    user_id = str(current_user["user_id"])

    logs = (
        db.query(ConversionLog)
        .filter(ConversionLog.user_id == user_id)
        .order_by(ConversionLog.converted_at.desc())
        .all()
    )
    return logs

@router.get("/download/{filename}", tags=["PDF"])
async def download_image(filename: str):
    # Docker container içinde doğru yol
    file_path = os.path.join("/app/temp", filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"File {filename} not found")

    # Dosya boyutunu kontrol et
    file_size = os.path.getsize(file_path)
    if file_size == 0:
        raise HTTPException(status_code=500, detail="File is empty")

    return FileResponse(
        path=file_path, 
        filename=filename, 
        media_type='image/jpeg',
        headers={
            "Cache-Control": "no-cache",
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Length": str(file_size)
        }
    )
