# app/infrastructure/security.py

from fastapi.security import HTTPBearer
from fastapi import Depends, HTTPException, status
from app.infrastructure.auth import verify_token  # JWT decode eden fonksiyon

bearer_scheme = HTTPBearer(auto_error=False)

def get_current_user(token = Depends(bearer_scheme)):
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization token missing"
        )
    try:
        payload = verify_token(token.credentials)
        return payload
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )


