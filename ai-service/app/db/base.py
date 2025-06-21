from sqlalchemy import Column, DateTime, Integer, create_engine, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from app.db.db_config import get_db_connection_string


# Create the database engine
try:
    DB_CONNECTION_STRING = get_db_connection_string()
    engine = create_engine(DB_CONNECTION_STRING)
except SQLAlchemyError as e:
    print(e)


# Create a configured session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Base class for SQLAlchemy models
class Base:
    __abstract__ = True
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


Base = declarative_base(cls=Base)


# Dependency to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine) 