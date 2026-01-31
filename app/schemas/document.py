from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class DocumentSchema(BaseModel):
    id: UUID
    filename: str
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentBase(BaseModel):
    filename: str


class DocumentCreate(DocumentBase):
    file_hash: str


class DocumentRead(DocumentBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
