from sqlalchemy import Column, String, UUID, DateTime, func
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from sqlalchemy.dialects.postgresql import JSONB


class DocumentRecord(Base):
    __tablename__ = "documents"
    
    id = Column(UUID, primary_key=True)
    file_name = Column(String)
    file_path = Column(String)
    file_hash = Column(String)
    chunks = Column(JSONB)
    embeddings = Column(JSONB)
    s3_url = Column(String, nullable=True)
    vector_cache_path = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    chats = relationship("ChatRecord", back_populates="document")
