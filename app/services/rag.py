from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException
from app.models.document_record import DocumentRecord
from app.models.chat_record import ChatRecord
from sqlalchemy.orm import joinedload
import uuid


class RAGService:
    @staticmethod
    async def create_document_entry(
        db: AsyncSession,
        file_name: str,
        file_hash: str,
        chunks: list[str],
        embeddings: list[list[float]]
    ):
        """Creates a document record with cached embeddings to save OpenAI costs."""
        new_document = DocumentRecord(
            id=uuid.uuid4(),
            file_name=file_name,
            file_hash=file_hash,
            chunks=chunks,
            embeddings=embeddings,
            created_at=func.now()
        )
        db.add(new_document)
        await db.commit()
        await db.refresh(new_document)
        return new_document

    @staticmethod
    async def create_chat_entry(
        db: AsyncSession,
        session_id: UUID,
        query: str,
        answer: str,
        sources: list[str]
    ):
        new_chat = ChatRecord(
            id=uuid.uuid4(),
            session_id=session_id,
            question=query,
            answer=answer,
            sources=sources,
            created_at=func.now()
        )

        db.add(new_chat)
        await db.commit()
        await db.refresh(new_chat)
        return new_chat

    @staticmethod
    async def get_document_by_hash(db: AsyncSession, file_hash: str):
        """Helper to check if we've already paid to embed this file."""
        result = await db.execute(
            select(DocumentRecord).where(DocumentRecord.file_hash == file_hash)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_document_history(db: AsyncSession, doc_id: uuid.UUID):
        result = await db.execute(
            select(ChatRecord)
            # .where(ChatRecord.document_id == doc_id)
            .order_by(ChatRecord.created_at.asc())
        )
        return result.scalars().all()

    @staticmethod
    async def get_all_chats(db: AsyncSession, limit: int = 50):
        """
        Retrieves the global chat history. 
        Includes document titles via a JOIN to make the frontend useful.
        """
        stmt = (
            select(ChatRecord)
            # .options(joinedload(ChatRecord))  
            .order_by(ChatRecord.created_at.desc())
            .limit(limit)
        )

        result = await db.execute(stmt)
        return result.scalars().unique().all()

    @staticmethod
    async def get_existing_doc(db, file_hash):
        stmt = select(DocumentRecord).where(
            DocumentRecord.file_hash == file_hash)
        result = await db.execute(stmt)
        existing_doc = result.scalar_one_or_none()
        return existing_doc

    @staticmethod
    async def get_history(session_id,db):
        record = await db.execute(select(ChatRecord).where(ChatRecord.session_id == session_id))
        session =  record.scalars().all()

        return session