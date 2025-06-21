from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.domain.models import User
from app.infrastructure.auth import create_access_token
from app.domain.exceptions import UserAlreadyExistsError, UserNotFoundError

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password, password_hash):
    return pwd_context.verify(plain_password, password_hash)

def register_user(db: Session, name: str, surname: str, email: str, phone_number: str, password: str):
    user = db.query(User).filter(User.email == email).first()
    if user:
        raise UserAlreadyExistsError(email)

    password_hash = hash_password(password)
    new_user = User(
        name=name,
        surname=surname,
        email=email,
        phone_number=phone_number,
        password_hash=password_hash  # ✅ DÜZGÜN ALAN ADI
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


from app.domain.exceptions import UserAlreadyExistsError, UserNotFoundError, IncorrectPasswordError

def login_user(db: Session, email: str, password: str):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise UserNotFoundError(email)
    if not verify_password(password, user.password_hash):
        raise IncorrectPasswordError(email)
    
    token_data = {"sub": user.email, "user_id": user.id}
    token = create_access_token(data=token_data)
    return token

