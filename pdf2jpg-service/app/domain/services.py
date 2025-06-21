import os
import glob
from PIL import Image
import fitz  # PyMuPDF
from app.domain.models import ConversionLog
from app.domain.exceptions import PDFConversionError, UnsupportedFileTypeError
import uuid 
from sqlalchemy.orm import Session
from app.domain.models import ConversionLog
import shutil

Image.MAX_IMAGE_PIXELS = 300000000

# Docker container içinde doğru yollar
OUTPUT_DIR = "/app/temp"
TEMP_DIR = "/app/temp"
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

def convert_pdf_to_jpg(file_path: str):
    if not file_path.endswith(".pdf"):
        raise UnsupportedFileTypeError(file_path)

    try:
        # Her PDF için benzersiz bir alt klasör oluştur
        unique_id = str(uuid.uuid4())
        pdf_temp_dir = os.path.join(TEMP_DIR, unique_id)
        os.makedirs(pdf_temp_dir, exist_ok=True)

        def get_next_image_number(output_folder):
            existing_files = glob.glob(os.path.join(output_folder, 'heart_xray_*.jpg'))
            if not existing_files:
                return 1
            numbers = []
            for file in existing_files:
                try:
                    num = int(os.path.basename(file).split('heart_xray_')[1].split('.')[0])
                    numbers.append(num)
                except:
                    continue
            return max(numbers) + 1 if numbers else 1

        next_number = get_next_image_number(OUTPUT_DIR)

        # PDF'i aç
        pdf_document = fitz.open(file_path)
        
        # İlk sayfayı al
        page = pdf_document[0]
        
        # Sayfayı yüksek kalitede görsel olarak render et
        mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for higher quality
        pix = page.get_pixmap(matrix=mat)
        
        # Görseli kaydet
        output_filename = f"heart_xray_{next_number}.jpg"
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        
        # Pixmap'i PIL Image'e dönüştür
        img_data = pix.tobytes("jpeg")
        with open(output_path, "wb") as f:
            f.write(img_data)
        
        # PDF'i kapat
        pdf_document.close()
        
        # Geçici klasörü temizle
        shutil.rmtree(pdf_temp_dir)
        
        return [output_path]

    except Exception as e:
        # Hata durumunda temizlik yap
        if 'pdf_temp_dir' in locals() and os.path.exists(pdf_temp_dir):
            shutil.rmtree(pdf_temp_dir)
        if 'pdf_document' in locals():
            pdf_document.close()
        raise PDFConversionError(str(e))

def get_all_logs(db: Session):
 return db.query(ConversionLog).order_by(ConversionLog.converted_at.desc()).all()
