from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
    email: str
    name: str


class UserCreate(BaseModel):
    name: str
    surname: str
    email: EmailStr
    phone_number: str
    password: str
    confirm_password: str  # frontend kontrol edecek

class UserResponse(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: str

class UserLogin(BaseModel):
    email: str
    password: str

