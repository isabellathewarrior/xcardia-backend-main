from fastapi import Depends, HTTPException, status
import requests
from fastapi.security import HTTPBearer
import logging

# Logging ayarları
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bearer_scheme = HTTPBearer()
AUTH_SERVICE_URL = "http://auth-service:8000"

def get_current_user(token=Depends(bearer_scheme)):
    try:
        logger.info(f"Auth service'e token doğrulama isteği gönderiliyor: {AUTH_SERVICE_URL}/verify-token")
        
        response = requests.get(
            f"{AUTH_SERVICE_URL}/verify-token",
            headers={"Authorization": f"Bearer {token.credentials}"},
            timeout=10  # 10 saniye timeout
        )
        
        logger.info(f"Auth service yanıtı: {response.status_code}")
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Auth service error: {response.status_code} - {response.text}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token verification failed: {response.status_code}"
            )
            
    except requests.exceptions.Timeout:
        logger.error("Auth service timeout")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth service timeout"
        )
    except requests.exceptions.ConnectionError:
        logger.error("Auth service connection error")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth service connection error"
        )
    except Exception as e:
        logger.error(f"Unexpected error in token verification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token verification failed"
        ) 