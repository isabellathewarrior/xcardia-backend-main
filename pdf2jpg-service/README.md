
# PDF to JPG FastAPI Microservice

This microservice provides an API endpoint to convert PDF files to JPG images using pymupdf4llm.

## Usage

1. Install dependencies:
    pip install -r requirements.txt

2. Start the service:
    uvicorn app.main:app --reload

3. Send a PDF file to the `/` endpoint to get JPG images.

- Uploaded PDFs are stored in `uploads/`
- Output JPGs are stored in `output_images/`

## Dependencies
- fastapi
- uvicorn
- pymupdf4llm
- pillow
- python-multipart
