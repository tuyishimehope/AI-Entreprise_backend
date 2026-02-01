from fastapi import APIRouter, UploadFile, Depends, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.db.database import get_db
from app.schemas.chat import ChatRead
from app.services.ask_question import ChatQuestionService
from app.services.openai import OpenAIService
from app.services.chunks import ChunkService
from app.services.rag import RAGService
from app.core.config import settings
from app.services.file import FileService

router = APIRouter()


def get_chat_service():
    ai = OpenAIService(api_key=settings.OPENAI_API_KEY)
    chunks = ChunkService()
    return ChatQuestionService(ai_service=ai, chunk_service=chunks)


@router.post("/chat")
async def chat_endpoint(
    file_id: str = Form(...),
    question: str = Form(...),
    db: AsyncSession = Depends(get_db),
    service: ChatQuestionService = Depends(get_chat_service)
):
    return await service.process_and_ask(file_id, question, db)

@router.get("/history", response_model=List[ChatRead])
async def get_chats(db: AsyncSession = Depends(get_db)):
    return await RAGService.get_all_chats(db=db)

@router.post("/file")
async def upload_file(file: UploadFile, db: AsyncSession= Depends(get_db)):
    return await FileService.upload_file_service(file, db)

@router.get("/file/{file_id}")
async def get_file_content(file_id, db: AsyncSession = Depends(get_db)):
    return await FileService.get_file_id(file_id=file_id, db=db)