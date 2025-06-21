from fastapi import Depends, HTTPException, Request, status
import requests
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import os
from typing import Dict, Any

bearer_scheme = HTTPBearer()
AUTH_SERVICE_URL = "http://auth-service:8000"

def get_current_user(token: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    try:
        response = requests.get(
            f"{AUTH_SERVICE_URL}/verify-token",
            headers={"Authorization": f"Bearer {token.credentials}"}
        )
        response.raise_for_status()
        user_data = response.json()
        user_data['token'] = token.credentials
        return user_data
    except requests.exceptions.HTTPError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=e.response.text
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token verification failed"
        )

def get_current_user_jwt(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> Dict[str, Any]:
    """
    JWT token'dan kullanıcı bilgilerini çıkarır
    """
    try:
        # JWT secret key - gerçek uygulamada environment variable'dan alınmalı
        secret_key = os.environ.get("JWT_SECRET_KEY", "your-secret-key")
        
        # Token'ı decode et
        payload = jwt.decode(credentials.credentials, secret_key, algorithms=["HS256"])
        
        # Token'ı da ekle
        payload["token"] = credentials.credentials
        
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication error: {str(e)}") 