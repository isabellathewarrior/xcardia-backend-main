from sqlalchemy import Column, Integer, String, Text, DateTime, func
from app.db.base import Base


class MessageModel(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    chat_id = Column(String, index=True, nullable=False)
    role = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def to_dict(self) -> dict:
        """
        Convert the message model to a dictionary.
        - **Returns**: A dictionary representation of the message model.
        """
        return {
            "id": str(self.id),
            "user_id": self.user_id,
            "chat_id": self.chat_id,
            "role": self.role,
            "content": self.content,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        } 