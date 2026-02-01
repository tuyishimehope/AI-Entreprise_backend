from sqlalchemy import Column, String, UUID, DateTime, func
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class File(Base):
    __tablename__ = "file"

    id = Column(UUID, primary_key=True)
    filename = Column(String)
    file_path = Column(String)
    created_at = Column(DateTime, server_default=func.now())
    chats = relationship("ChatRecord", back_populates="file")

