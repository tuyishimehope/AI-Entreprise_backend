from uuid import UUID
from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.session.session import ChatSessionService
from app.db.database import get_db

session_router = APIRouter(tags=["session"])


@session_router.post("/session")
async def start_session(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    return await ChatSessionService.create_session(file, db)


@session_router.get("/session")
async def get_sessions(db: AsyncSession = Depends(get_db)):
    return await ChatSessionService.get_sessions(db)


@session_router.get("/session/{session_id}")
async def get_session_content(session_id: UUID, db: AsyncSession = Depends(get_db)):
    return await ChatSessionService.get_session(session_id, db)
