from uuid import UUID
import uuid
from app.services.document.document import DocumentService
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.session import ChatSession
from fastapi import UploadFile, HTTPException


class ChatSessionService():

    @staticmethod
    async def create_session(file: UploadFile, db: AsyncSession):

        new_file = await DocumentService.upload_file(file, db)

        new_session = ChatSession(
            id=uuid.uuid4(),
            title=new_file.file_name,
            created_at=func.now(),
            document_id=new_file.id,
        )

        db.add(new_session)
        await db.commit()

        await db.refresh(new_session)

        return new_session

    @staticmethod
    async def get_sessions(db: AsyncSession):
        result = await db.execute(select(ChatSession))
        return result.scalars().all()

    @staticmethod
    async def get_session(session_id: UUID, db: AsyncSession):
        result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
        session = result.scalars().all()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return session
