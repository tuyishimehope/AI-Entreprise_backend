from uuid import UUID
from fastapi import APIRouter, Depends, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.db.database import get_db
from app.schemas.chat import ChatRead
from app.services.chat.ask import ChatQuestionService
from app.services.llm.openai import OpenAIService
from app.services.chat.chunks import ChunkService
from app.services.rag import RAGService
from app.core.config import settings


router = APIRouter()


def get_chat_service():
    ai = OpenAIService(api_key=settings.OPENAI_API_KEY)
    chunks = ChunkService()
    return ChatQuestionService(ai_service=ai, chunk_service=chunks)


@router.post("/chat")
async def chat_endpoint(
    file_id: str = Form(...),
    question: str = Form(...),
    session_id: str = Form(...),
    db: AsyncSession = Depends(get_db),
    service: ChatQuestionService = Depends(get_chat_service)
):
    return await service.process_and_ask(file_id, session_id, question, db)


@router.get("/history", response_model=List[ChatRead])
async def get_chats(db: AsyncSession = Depends(get_db)):
    return await RAGService.get_all_chats(db=db)


@router.get("/history/{session_id}")
async def get_history(session_id: UUID, db: AsyncSession = Depends(get_db)):
    return await RAGService.get_history(session_id, db)
