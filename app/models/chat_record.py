import uuid
from sqlalchemy import Column, UUID, Text, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from app.db.base_class import Base


class ChatRecord(Base):
    __tablename__ = "chat_history"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    file_id = Column(UUID(as_uuid=True), ForeignKey("file.id"), nullable=False)
    question = Column(Text)
    answer = Column(Text)
    sources = Column(JSONB)
    created_at = Column(DateTime, server_default=func.now())
    document = relationship("DocumentRecord", back_populates="chats")
    file = relationship("File", back_populates="chats")
    
