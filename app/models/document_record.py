from sqlalchemy import Column, String, UUID, DateTime, func
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from sqlalchemy.dialects.postgresql import JSONB


class DocumentRecord(Base):
    __tablename__ = "documents"
    id = Column(UUID, primary_key=True)
    filename = Column(String)
    file_hash = Column(String)
    chunks = JSONB()
    embeddings = JSONB
    s3_url = Column(String, nullable=True)
    vector_cache_path = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    chats = relationship("ChatRecord", back_populates="document")
