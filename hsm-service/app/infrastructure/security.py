from fastapi import Depends, HTTPException, status
import requests
from fastapi.security import HTTPBearer
bearer_scheme = HTTPBearer()
AUTH_SERVICE_URL = "http://auth-service:8000"

def get_current_user(token=Depends(bearer_scheme)):
    try:
        response = requests.get(
            f"{AUTH_SERVICE_URL}/verify-token",
            headers={"Authorization": f"Bearer {token.credentials}"}
        )
        response.raise_for_status()
        return response.json()
    except:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token verification failed"
        ) 