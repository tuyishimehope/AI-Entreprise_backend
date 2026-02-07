from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import List, Optional

class DocumentMinimalRead(BaseModel):
    id: UUID
    file_name: str
    model_config = ConfigDict(from_attributes=True)

class ChatRecordRead(BaseModel):
    id: UUID
    question: str
    answer: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class SessionSchema(BaseModel):
    id: UUID
    document_id: UUID
    title: str
    created_at: datetime
    document: Optional[DocumentMinimalRead] = None 
    messages: List[ChatRecordRead] = [] 

    model_config = ConfigDict(from_attributes=True)