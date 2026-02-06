import uuid
from datetime import datetime
from typing import List, TYPE_CHECKING

from sqlalchemy import ForeignKey, func, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.chat_record import ChatRecord
    from app.models.document_record import DocumentRecord


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE")
    )
    title: Mapped[str] = mapped_column(default="New Financial Chat")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    document: Mapped["DocumentRecord"] = relationship(
        "DocumentRecord", back_populates="sessions"
    )
    messages: Mapped[List["ChatRecord"]] = relationship(
        "ChatRecord",
        back_populates="session",
        cascade="all, delete-orphan",
    )
