from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os, base64
from .security import get_current_user

router = APIRouter()

# Anahtar örnek olarak sabit, prod ortamda güvenli şekilde saklanmalı
KEY = os.environ.get("HSM_AES_KEY", None)
if not KEY:
    KEY = AESGCM.generate_key(bit_length=128)
    # Uygulamada bu anahtar bir dosyada/gizli ortam değişkeninde tutulmalı

def get_aesgcm():
    return AESGCM(KEY)

class EncryptRequest(BaseModel):
    user_id: str

class EncryptResponse(BaseModel):
    pseudo_user_id: str

class DecryptRequest(BaseModel):
    pseudo_user_id: str

class DecryptResponse(BaseModel):
    user_id: str

@router.post("/encrypt", response_model=EncryptResponse)
def encrypt_user_id(req: EncryptRequest, current_user=Depends(get_current_user)):
    if req.user_id != str(current_user["user_id"]):
        raise HTTPException(status_code=403, detail="Sadece kendi user_id'nizi şifreleyebilirsiniz.")
    aesgcm = get_aesgcm()
    nonce = os.urandom(12)
    ct = aesgcm.encrypt(nonce, req.user_id.encode(), None)
    pseudo_user_id = base64.b64encode(nonce + ct).decode()
    return {"pseudo_user_id": pseudo_user_id}

@router.post("/decrypt", response_model=DecryptResponse)
def decrypt_user_id(req: DecryptRequest, current_user=Depends(get_current_user)):
    aesgcm = get_aesgcm()
    data = base64.b64decode(req.pseudo_user_id)
    nonce, ct = data[:12], data[12:]
    try:
        user_id = aesgcm.decrypt(nonce, ct, None)
        if user_id.decode() != str(current_user["user_id"]):
            raise HTTPException(status_code=403, detail="Sadece kendi user_id'nizi çözebilirsiniz.")
        return {"user_id": user_id.decode()}
    except Exception:
        raise HTTPException(status_code=400, detail="Decryption failed") 