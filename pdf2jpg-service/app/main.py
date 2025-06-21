from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from fastapi.security import HTTPBearer
import pymupdf4llm
import os
import glob
import shutil
from PIL import Image
from typing import Optional
from app.domain.models import Base
from app.infrastructure.database import engine
from app.application.routes import router  # 📌 Router en baştan eklensin
from fastapi import Depends
os.makedirs("temp", exist_ok=True) 
# Initialize DB
def init_db():
    Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Xcardia Project",
    description="XCARDIA : pdf2image-service",
    version="1.0.0",  # ← BURADA VİRGÜL GEREKİYOR
    openapi_tags=[{"name": "PDF", "description": "PDF dönüşüm işlemleri"}],
    dependencies=[Depends(HTTPBearer())]
)
# ✅ Router'ı uygulamaya ekle (erken eklenmeli)
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

# Klasörler
UPLOAD_DIR = "uploads"
OUTPUT_DIR = "output_images"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_next_image_number(output_folder):
    existing_files = glob.glob(os.path.join(output_folder, 'heart_xray*.jpg'))
    
    if not existing_files:
        return 1
    
    numbers = []
    for file in existing_files:
        try:
            num = int(os.path.basename(file).split('heart_xray')[1].split('.')[0])
            numbers.append(num)
        except:
            continue
    
    return max(numbers) + 1 if numbers else 1

def process_pdf(pdf_path: str, output_folder: str) -> str:
    next_number = get_next_image_number(output_folder)
    
    # Extract images from PDF
    pymupdf4llm.to_markdown(
        doc=pdf_path,
        pages=[0],
        write_images=True,
        image_path=output_folder,
        image_format="jpg",
        dpi=300
    )
    
    # Find JPG files
    jpg_files = [f for f in os.listdir(output_folder) if f.endswith('.jpg')]
    
    if len(jpg_files) > 1:
        # Combine all images
        images = [Image.open(os.path.join(output_folder, f)) for f in jpg_files]
        total_height = sum(img.height for img in images)
        max_width = max(img.width for img in images)
        combined_image = Image.new('RGB', (max_width, total_height), 'white')
        
        current_height = 0
        for img in images:
            combined_image.paste(img, (0, current_height))
            current_height += img.height
        
        # Save combined image
        output_filename = f'heart_xray{next_number}.jpg'
        output_path = os.path.join(output_folder, output_filename)
        combined_image.save(output_path)
        
        # Clean up temporary files
        for f in jpg_files:
            os.remove(os.path.join(output_folder, f))
        
        return output_filename
    else:
        # Rename single image
        if jpg_files:
            old_path = os.path.join(output_folder, jpg_files[0])
            new_filename = f'heart_xray{next_number}.jpg'
            new_path = os.path.join(output_folder, new_filename)
            os.rename(old_path, new_path)
            return new_filename
        return None

@app.post("/upload-pdf/")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")
    
    # Save PDF
    pdf_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(pdf_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        # Process PDF
        output_filename = process_pdf(pdf_path, OUTPUT_DIR)
        
        if output_filename:
            return {
                "message": "PDF processed successfully",
                "output_file": output_filename,
                "output_path": os.path.join(OUTPUT_DIR, output_filename)
            }
        else:
            raise HTTPException(status_code=500, detail="Image processing failed")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/")
async def root():
    return {"message": "Welcome to FastAPI!"}