from typing import Optional
from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime


class DocumentSchema(BaseModel):
    id: UUID
    file_name: str
    file_path: str
    chunks: Optional[list[str]]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentRead(DocumentSchema):
    pass


class DocumentCreate(DocumentSchema):
    file_hash: str
