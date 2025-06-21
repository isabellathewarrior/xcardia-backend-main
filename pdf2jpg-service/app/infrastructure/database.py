import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# PostgreSQL bağlantı URL'sini ortam değişkeninden al
DATABASE_URL = os.environ["DATABASE_URL"]

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Veritabanı tablolarının oluşturulması
# Not: Bu, uygulamanın başlangıcında bir kerelik bir işlem olmalıdır.
from app.domain.models import ConversionLog
Base.metadata.create_all(bind=engine)
