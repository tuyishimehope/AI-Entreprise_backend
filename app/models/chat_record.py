import uuid
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import Text, DateTime, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.session import ChatSession


class ChatRecord(Base):
    __tablename__ = "chat_history"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("chat_sessions.id", ondelete="CASCADE")
    )

    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    sources: Mapped[Optional[list]] = mapped_column(
        JSONB, server_default="[]"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    session: Mapped["ChatSession"] = relationship(
        "ChatSession", back_populates="messages"
    )
