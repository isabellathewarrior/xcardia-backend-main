from fastapi import APIRouter, HTTPException, File, UploadFile
from fastapi.responses import JSONResponse
import io
import skimage.io
from app.repositories.xray_scan_evaluation_repository import XRayScanEvaluationRepository


xray_scan_evaluation_router = APIRouter(
    prefix="/xray_scan_evaluation",
    tags=["xray_scan_evaluation"],
    responses={404: {"description": "Not found"}},
)

@xray_scan_evaluation_router.post(
    '/evaluate',
    summary="Evaluate X-ray scan",
    description="Evaluate X-ray scan and provide diagnosis",
    response_description="Evaluation successful",
    status_code=200,
    responses={
        200: {"description": "Evaluation successful"},
        400: {"description": "Invalid input"},
        500: {"description": "Internal server error"}
    }
)
async def evaluate_xray_scan(xray_scan_upload: UploadFile = File(...)):
    """
    Evaluate X-ray scan and provide diagnosis.
    - **xray_scan**: The X-ray scan file to be evaluated.
    - **Returns**: A JSON response with the evaluation result.
    - **Raises**: 400 if the input is invalid, 500 for internal server errors.
    """
    evaluater = XRayScanEvaluationRepository()
    try:
        # Read the image file
        image_bytes = await xray_scan_upload.read()
        xray_scan = skimage.io.imread(io.BytesIO(image_bytes))
        if xray_scan is None:
            raise ValueError("Error: Image is not valid.")
        result = evaluater.evaluate_xray_scan(xray_scan)
        # Convert the result to a JSON response
        return JSONResponse(content=result, status_code=200)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error") 