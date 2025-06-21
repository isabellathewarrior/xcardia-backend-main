from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

# Token için doğrulama / reuse from auth-service
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: str

class UserBase(BaseModel):
    email: str
    name: str

class UserResponse(UserBase):
    id: int

    class Config:
        orm_mode = True

# PDF dönüşüm sonucu model 
class PDFConversionResponse(BaseModel):
    message: str
    user: str  # email
    images: List[str]  # Dönüştürülen JPG dosya yolları

#  PDF log response
class ConversionLog(BaseModel):
    id: int
    user_email: str
    filename: str
    converted_at: datetime

    class Config:
        orm_mode = True
