from uuid import UUID
from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.session.session import ChatSessionService
from app.db.database import get_db
from app.schemas.session import SessionSchema

session_router = APIRouter(prefix="/session",tags=["session"])


@session_router.post("", status_code=201)
async def start_session(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    return await ChatSessionService.create_session(file, db)


@session_router.get("")
async def get_sessions(db: AsyncSession = Depends(get_db)):
    return await ChatSessionService.get_sessions(db)


@session_router.get("/{session_id}", response_model=SessionSchema)
async def get_session_content(session_id: UUID, db: AsyncSession = Depends(get_db)):
    return await ChatSessionService.get_session(session_id, db)

@session_router.delete("/{session_id}")
async def delete_session(session_id: UUID, db:AsyncSession = Depends(get_db)):
    return await ChatSessionService.delete_session(db, session_id)
