from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class ConversionLog(Base):
    __tablename__ = "conversion_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)  # UUID ya da masked id 
    user_email = Column(String, index=True)  
    filename = Column(String)
    jpg_output_path = Column(String)  # important
    converted_at = Column(DateTime, default=datetime.utcnow)

