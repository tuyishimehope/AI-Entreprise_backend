from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import List, Optional

from app.schemas.document import DocumentRead, DocumentSchema


class ChatResponseSchema(BaseModel):
    id: UUID
    question: str
    answer: str
    sources: List[str]
    created_at: datetime
    document: DocumentSchema 

    model_config = ConfigDict(from_attributes=True)

class ChatBase(BaseModel):
    question: str
    answer: str
    sources: List[str]

class ChatCreate(ChatBase):
    document_id: UUID

class ChatRead(ChatBase):
    id: UUID
    created_at: datetime
    document_id: UUID
    document: Optional[DocumentRead] = None

    model_config = ConfigDict(from_attributes=True)