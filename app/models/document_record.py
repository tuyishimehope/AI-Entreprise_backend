from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
import uuid

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.session import ChatSession


class DocumentRecord(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    file_name: Mapped[str]
    file_path: Mapped[str] = mapped_column(nullable=True)
    file_hash: Mapped[str] = mapped_column(index=True)
    chunks: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    embeddings: Mapped[JSONB] = mapped_column(JSONB, nullable=True)
    s3_url: Mapped[str] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    sessions: Mapped[List["ChatSession"]] = relationship(
        "ChatSession",
        back_populates="document",
        cascade="all, delete-orphan",
    )
