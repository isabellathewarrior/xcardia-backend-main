from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.infrastructure.database import SessionLocal
from app.domain.services import register_user, login_user
from app.application.schemas import UserCreate, Token , UserLogin
from fastapi import Request
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends
from fastapi import APIRouter, Depends, HTTPException
from app.infrastructure.security import get_current_user  
from app.infrastructure.auth import create_access_token
router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/register", response_model=Token)
def register(user: UserCreate, db: Session = Depends(get_db)):
    try:
        user = register_user(
            db,
            name=user.name,
            surname=user.surname,
            email=user.email,
            phone_number=user.phone_number,
            password=user.password
        )
        token_data = {"sub": user.email}
        token = create_access_token(data=token_data)
        return {"access_token": token, "token_type": "bearer"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
   
@router.post("/login", response_model=Token)
def login(user: UserLogin, db: Session = Depends(get_db)):
    try:
        token = login_user(db, email=user.email, password=user.password)
        return {"access_token": token, "token_type": "bearer"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    

@router.get("/verify-token", summary="Verify JWT token", tags=["Auth"])
def verify_token_endpoint(current_user: dict = Depends(get_current_user)):
    """
    JWT token'ı doğrular ve token içeriğinden kullanıcı bilgilerini döner.
    """
    return {
        "user_id": current_user.get("user_id"),
        "email": current_user.get("sub")
    }