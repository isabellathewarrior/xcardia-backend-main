import os
import glob
from PIL import Image
import pymupdf4llm 
from app.domain.models import ConversionLog
from app.domain.exceptions import PDFConversionError, UnsupportedFileTypeError
import uuid 
from sqlalchemy.orm import Session
from app.domain.models import ConversionLog
import shutil

Image.MAX_IMAGE_PIXELS = 300000000

OUTPUT_DIR = "/app/temp"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def convert_pdf_to_jpg(file_path: str):
    if not file_path.endswith(".pdf"):
        raise UnsupportedFileTypeError(file_path)

    try:
        # Her PDF için benzersiz bir alt klasör oluştur
        unique_id = str(uuid.uuid4())
        pdf_temp_dir = os.path.join(OUTPUT_DIR, unique_id)
        os.makedirs(pdf_temp_dir, exist_ok=True)

        def get_next_image_number(output_folder):
            existing_files = glob.glob(os.path.join(output_folder, 'heart_xray_*.jpg'))
            if not existing_files:
                return 0
            numbers = []
            for file in existing_files:
                try:
                    num = int(os.path.basename(file).split('heart_xray_')[1].split('.')[0])
                    numbers.append(num)
                except:
                    continue
            return max(numbers) + 1 if numbers else 0

        next_number = get_next_image_number(OUTPUT_DIR)

        # PDF'ten JPG çıkart (sadece bu alt klasöre)
        pymupdf4llm.to_markdown(
            doc=file_path,
            pages=[0],
            write_images=True,
            image_path=pdf_temp_dir,
            image_format="jpg",
            dpi=300
        )

        # Sadece bu alt klasördeki JPG'leri bul
        jpg_files = sorted([f for f in os.listdir(pdf_temp_dir) if f.endswith('.jpg')])
        jpg_paths = [os.path.join(pdf_temp_dir, f) for f in jpg_files]

        if not jpg_paths:
            shutil.rmtree(pdf_temp_dir)
            raise PDFConversionError("No JPG images extracted from PDF.")

        # Eğer birden fazla JPG varsa, hepsini alt alta birleştir
        if len(jpg_paths) > 1:
            images = [Image.open(p) for p in jpg_paths]
            total_height = sum(img.height for img in images)
            max_width = max(img.width for img in images)
            combined_image = Image.new('RGB', (max_width, total_height), 'white')
            current_height = 0
            for img in images:
                combined_image.paste(img, (0, current_height))
                current_height += img.height
            output_filename = f"heart_xray_{next_number}.jpg"
            output_path = os.path.join(OUTPUT_DIR, output_filename)
            combined_image.save(output_path)
            # Geçici JPG'leri sil
            for p in jpg_paths:
                os.remove(p)
            shutil.rmtree(pdf_temp_dir)
            return [output_path]
        else:
            # Sadece bir JPG varsa, onu ana temp klasörüne taşı
            old_path = jpg_paths[0]
            new_filename = f"heart_xray_{next_number}.jpg"
            new_path = os.path.join(OUTPUT_DIR, new_filename)
            os.rename(old_path, new_path)
            shutil.rmtree(pdf_temp_dir)
            return [new_path]

    except Exception as e:
        raise PDFConversionError(str(e))

def get_all_logs(db: Session):
 return db.query(ConversionLog).order_by(ConversionLog.converted_at.desc()).all()
