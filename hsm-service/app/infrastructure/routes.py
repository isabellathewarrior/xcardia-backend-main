from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os, base64
from .security import get_current_user

router = APIRouter()

# Anahtar oluştur - her zaman bytes olarak
KEY = AESGCM.generate_key(bit_length=128)

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
    try:
        aesgcm = get_aesgcm()
        nonce = os.urandom(12)
        ct = aesgcm.encrypt(nonce, req.user_id.encode(), None)
        pseudo_user_id = base64.b64encode(nonce + ct).decode()
        return {"pseudo_user_id": pseudo_user_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Encryption failed: {str(e)}")

@router.post("/decrypt", response_model=DecryptResponse)
def decrypt_user_id(req: DecryptRequest, current_user=Depends(get_current_user)):
    try:
        aesgcm = get_aesgcm()
        data = base64.b64decode(req.pseudo_user_id)
        nonce, ct = data[:12], data[12:]
        user_id = aesgcm.decrypt(nonce, ct, None)
        if user_id.decode() != str(current_user["user_id"]):
            raise HTTPException(status_code=403, detail="Sadece kendi user_id'nizi çözebilirsiniz.")
        return {"user_id": user_id.decode()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Decryption failed: {str(e)}") 