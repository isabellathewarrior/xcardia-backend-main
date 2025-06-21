from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.infrastructure.database import SessionLocal
from app.domain.services import convert_pdf_to_jpg
from app.domain.models import ConversionLog
import shutil
import os
import uuid
import requests
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
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["user_id"]
    user_email = current_user["email"]

    # Authorization header'dan token'ı al
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    token = auth_header.split(" ")[1]

    # Dosya adını ve yolu oluştur
    filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = f"/app/temp/{filename}"

    print(f"Processing PDF: {file.filename} -> {file_path}")

    # PDF dosyasını diske kaydet
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        print(f"PDF saved to: {file_path}")
    except Exception as e:
        print(f"Error saving PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Error saving PDF: {str(e)}")

    try:
        # PDF'i JPG'e dönüştür
        print("Converting PDF to JPG...")
        image_paths = convert_pdf_to_jpg(file_path)
        print(f"Conversion result: {image_paths}")

        if not image_paths:
            print("No images generated from PDF")
            raise HTTPException(status_code=500, detail="No images generated from PDF")

        # HSM Service'e kullanıcı ID'sini şifrelet
        print("Encrypting user_id with HSM...")
        hsm_encrypt_url = "http://hsm-service:8000/encrypt"
        hsm_headers = {"Authorization": f"Bearer {token}"}
        hsm_payload = {"user_id": str(user_id)}
        
        try:
            hsm_response = requests.post(hsm_encrypt_url, json=hsm_payload, headers=hsm_headers)
            hsm_response.raise_for_status()
            pseudo_user_id = hsm_response.json()["pseudo_user_id"]
            print(f"User_id encrypted: {pseudo_user_id}")
        except requests.exceptions.RequestException as e:
            print(f"HSM Service error: {e}")
            raise HTTPException(status_code=500, detail=f"HSM Service error: {str(e)}")

        # AI Service'e image'ları ve şifrelenmiş kullanıcı ID'sini gönder
        print("Sending to AI Service...")
        ai_service_url = "http://ai-service:8000/openai/interpret_xray_scan"
        
        # İlk image'ı AI Service'e gönder
        ai_result = None
        if image_paths:
            with open(image_paths[0], "rb") as img_file:
                files = {"xray_scan_upload": (os.path.basename(image_paths[0]), img_file, "image/jpeg")}
                data = {
                    "content": "Bu X-ray görüntüsünü analiz et ve detaylı bir rapor hazırla.",
                    "user_id": pseudo_user_id,
                    "chat_id": f"chat_{uuid.uuid4()}"
                }
                ai_headers = {"Authorization": f"Bearer {token}"}
                
                try:
                    print(f"Sending image {image_paths[0]} to AI Service...")
                    ai_response = requests.post(ai_service_url, files=files, data=data, headers=ai_headers)
                    ai_response.raise_for_status()
                    ai_result = ai_response.json()
                    print("AI Service response received")
                except requests.exceptions.RequestException as e:
                    print(f"AI Service error: {e}")
                    raise HTTPException(status_code=500, detail=f"AI Service error: {str(e)}")

        # AI sonucunu HSM ile decrypt et (eğer AI sonucu varsa)
        decrypted_ai_result = None
        if ai_result and "user_id" in ai_result:
            try:
                print("Decrypting AI result...")
                hsm_decrypt_url = "http://hsm-service:8000/decrypt"
                hsm_decrypt_payload = {"pseudo_user_id": ai_result["user_id"]}
                hsm_decrypt_response = requests.post(hsm_decrypt_url, json=hsm_decrypt_payload, headers=hsm_headers)
                hsm_decrypt_response.raise_for_status()
                decrypted_user_id = hsm_decrypt_response.json()["user_id"]
                
                # AI sonucunu güncelle
                decrypted_ai_result = ai_result.copy()
                decrypted_ai_result["user_id"] = decrypted_user_id
                print("AI result decrypted successfully")
            except requests.exceptions.RequestException as e:
                print(f"Decrypt error: {e}")
                # Decrypt başarısız olursa orijinal sonucu kullan
                decrypted_ai_result = ai_result

        # Log kaydı oluştur
        print("Creating log entry...")
        conversion_log = ConversionLog(
            user_id=user_id, 
            user_email=user_email,
            filename=file.filename, 
            jpg_output_path=", ".join(image_paths),
            converted_at=datetime.utcnow()
        )
        db.add(conversion_log)
        db.commit()
        print("Log entry created")

        return JSONResponse(content={
            "message": "Conversion and AI evaluation successful",
            "user": user_email,
            "images": [
                f"http://localhost:8001/download/{os.path.basename(p)}"
                for p in image_paths
            ],
            "ai_evaluation": decrypted_ai_result if image_paths else None
        })
    except Exception as e:
        print(f"Error in convert_pdf: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Cleaned up: {file_path}")


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
