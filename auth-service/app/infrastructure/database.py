from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.domain.models import Base
import os

SQLALCHEMY_DATABASE_URL = os.environ["DATABASE_URL"]

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Veritabanı tablosunun oluşturulması
def init_db():
    Base.metadata.create_all(bind=engine)
