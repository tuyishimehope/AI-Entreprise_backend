import hashlib
from typing import AsyncGenerator, Dict, Any, List
from uuid import UUID
from fastapi.responses import StreamingResponse
import numpy as np
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.llm.openai import OpenAIService
from app.services.chat.chunks import ChunkService
from app.services.chat.document_processor import DocumentProcessor
from app.services.rag import RAGService
from app.services.document.document import DocumentService


class ChatQuestionService:
    """
    Orchestrates:
    - document retrieval & caching
    - embedding & semantic search
    - RAG-based LLM generation
    - persistence of chat history
    """

    def __init__(
        self,
        ai_service: OpenAIService,
        chunk_service: ChunkService,
    ) -> None:
        self.ai = ai_service
        self.chunks = chunk_service

    async def process_and_ask(
        self,
        file_id: str,
        session_id: str,
        question: str,
        db: AsyncSession,
    ) :
        """
        Main RAG entrypoint:
        - loads or caches document
        - retrieves relevant chunks
        - queries LLM
        - persists result
        """

        document = await self._load_document(UUID(file_id), db)
        cached_doc = await self._get_or_create_cached_doc(
            db=db,
            document=document,
        )

        question_embedding = self._embed_question(question)

        relevant_chunks = self._retrieve_relevant_chunks(
            question_embedding=question_embedding,
            chunks=cached_doc["chunks"],
            embeddings=cached_doc["embeddings"],
        )

        context = "\n\n".join(relevant_chunks)

        generator = self._generate_answer(
            db=db,
            session_id=UUID(session_id),
            sources=relevant_chunks,
            context=context,
            question=question,
        )
        # document_id=cached_doc["doc_id"],

        # await self._persist_chat(
        #     db=db,
        #     session_id=UUID(session_id),
        #     question=question,
        #     answer=text_data,
        #     sources=relevant_chunks,
        #     document_id=cached_doc["doc_id"],
        # )
        return StreamingResponse(generator, media_type="text/plain")

    async def _load_document(
        self,
        file_id: UUID,
        db: AsyncSession,
    ) -> Dict[str, Any]:
        file_data = await DocumentService.get_record(
            file_id=file_id,
            db=db,
        )

        if not file_data or not file_data.get("content"):
            raise HTTPException(
                status_code=404,
                detail="Document not found or empty.",
            )

        content: str = file_data["content"]
        file_hash = hashlib.md5(content.encode("utf-8")).hexdigest()

        return {
            "file_name": file_data["file_name"],
            "file_path": file_data["file_path"],
            "file_hash": file_hash,
        }

    async def _get_or_create_cached_doc(
        self,
        db: AsyncSession,
        document: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Ensures document embeddings are computed once and cached forever.
        """

        existing_doc = await RAGService.get_existing_doc(
            db=db,
            file_hash=document["file_hash"],
        )

        if existing_doc:
            return {
                "doc_id": existing_doc.id,
                "chunks": existing_doc.chunks,
                "embeddings": np.array(existing_doc.embeddings),
            }

        # Cache miss → extract, chunk, embed
        extracted_text = self._extract_text(
            file_name=document["file_name"],
        )

        chunks = self.chunks.simple_chunker(text=extracted_text)

        embeddings = self.ai.get_embeddings(chunks)

        new_doc = await RAGService.create_document_entry(
            db=db,
            file_name=document["file_name"],
            file_hash=document["file_hash"],
            chunks=chunks,
            embeddings=embeddings,
        )

        return {
            "doc_id": new_doc.id,
            "chunks": chunks,
            "embeddings": np.array(embeddings),
        }

    def _extract_text(self, file_name: str) -> str:
        extension = file_name.split(".")[-1].lower()
        return DocumentProcessor.extract_text(
            extension=extension,
            filename=file_name
        )

    def _embed_question(self, question: str) -> np.ndarray:
        embeddings = self.ai.get_embeddings([question])
        if not embeddings:
            raise HTTPException(
                status_code=422,
                detail="Failed to embed question.",
            )
        return np.array(embeddings[0])

    def _retrieve_relevant_chunks(
        self,
        question_embedding: np.ndarray,
        chunks: List[str],
        embeddings: np.ndarray,
    ) -> List[str]:
        return self.chunks.get_most_relevant_chunks(
            question_vector=question_embedding,
            chunk_vectors=embeddings,
            chunks=chunks,
        )

    async def _generate_answer(
        self,
        db: AsyncSession,
        session_id: UUID,
        sources: List[str],
        # document_id: str,
        context: str,
        question: str,
    ) -> AsyncGenerator[str, None]:
        try:
            full_answer = ""
            generator = self.ai.ask_question_about_document(
                db,
                session_id,
                sources,
                context_text=context,
                user_question=question,
            )
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail="LLM generation failed.",
            ) from exc

        if not generator:
            raise HTTPException(400, detail="No answer generated")

        async for chunk in generator:
            full_answer += chunk
            yield chunk
        
        await RAGService.create_chat_entry(
            db=db,
            session_id=session_id,
            query=question,
            answer=full_answer,
            sources=sources,
        )


    async def _persist_chat(
        self,
        db: AsyncSession,
        session_id: UUID,
        question: str,
        answer: str,
        sources: List[str],
        document_id: str,
    ) -> Dict[str, Any]:
        chat_entry = await RAGService.create_chat_entry(
            db=db,
            session_id=session_id,
            query=question,
            answer=answer,
            sources=sources,
        )

        return {
            "id": chat_entry.id,
            "question": question,
            "answer": answer,
            "sources": sources,
            "document_id": document_id,
        }
