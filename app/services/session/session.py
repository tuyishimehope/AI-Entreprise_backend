from typing import List
from uuid import UUID
from fastapi import UploadFile, HTTPException
import uuid
from app.services.document.document import DocumentService
from sqlalchemy import select,delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.session import ChatSession

from sqlalchemy.orm import selectinload


class ChatSessionService:

    @staticmethod
    async def create_session(file: UploadFile, db: AsyncSession) -> ChatSession:
        new_file = await DocumentService.upload_file(file, db)

        new_session = ChatSession(
            id=uuid.uuid4(),
            title=new_file.file_name,
            document_id=new_file.id,
        )

        db.add(new_session)
        await db.commit()
        await db.refresh(new_session)
        return new_session

    @staticmethod
    async def get_session(session_id: UUID, db: AsyncSession) -> ChatSession:
        query = (
            select(ChatSession)
            .where(ChatSession.id == session_id)
            .options(
                selectinload(ChatSession.document),
                selectinload(ChatSession.messages)
            )
        )
        result = await db.execute(query)
        session = result.scalar_one_or_none()

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return session

    @staticmethod
    async def get_sessions(db: AsyncSession) -> List[ChatSession]:
        result = await db.execute(select(ChatSession))
        return list(result.scalars().all())
    
    @staticmethod
    async def delete_session(db: AsyncSession, session_id: UUID) -> bool:
        """
        Deletes a session and its cascading relations.
        Returns True if deleted, False if not found.
        """
        result = await db.execute(
            delete(ChatSession).where(ChatSession.id == session_id)
        )
        
        if result._raw_all_rows == 0:
            raise HTTPException(
                status_code=404, 
                detail=f"Session {session_id} not found"
            )

        await db.commit()
        return True