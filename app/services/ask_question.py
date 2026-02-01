import hashlib
import numpy as np
from fastapi import HTTPException
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.openai import OpenAIService
from app.services.chunks import ChunkService
from app.services.document_processor import DocumentProcessor
from app.services.rag import RAGService
from app.services.file import FileService


class ChatQuestionService:
    def __init__(self, ai_service: OpenAIService, chunk_service: ChunkService):
        self.ai = ai_service
        self.chunks = chunk_service

    async def process_and_ask(self, file_id, question: str, db: AsyncSession) -> Dict[str, Any]:
        file_data = await FileService.get_file_id(file_id=file_id, db=db)
        content = file_data.get("content")
        filename = file_data.get("filename")
        file_path = file_data.get("file_path")
        encoded_data = content.encode('utf-8') # type: ignore
        file_hash = hashlib.md5(encoded_data).hexdigest() 

        existing_doc = await RAGService.get_existing_doc(db, file_hash)

        if existing_doc:
            # CACHE HIT: Reconstruct chunks/embeddings from DB
            # Note: This assumes you stored 'chunks' and 'embeddings' in DocumentRecord
            my_chunks = existing_doc.chunks
            chunk_embeddings = np.array(existing_doc.embeddings)
            doc_id = existing_doc.id
        else:
            # CACHE MISS: Do the heavy lifting (and pay OpenAI)
            extension = filename.split(".")[-1].lower() # type: ignore
            text_data = DocumentProcessor.extract_text(file_path, extension) # type: ignore
            my_chunks = self.chunks.simple_chunker(text=text_data)

            # OpenAI call for document body (Expensive)
            embeddings_list = self.ai.get_embeddings(my_chunks)
            chunk_embeddings = np.array(embeddings_list)

            # Persist the new document so we never pay for it again
            new_doc = await RAGService.create_document_entry(
                db=db,
                filename=filename, # type: ignore
                file_hash=file_hash,
                chunks=my_chunks,
                embeddings=embeddings_list
            )
            doc_id = new_doc.id

        q_emb_list = self.ai.get_embeddings([question])
        question_embedding = q_emb_list[0]

        relevant_texts = self.chunks.get_most_relevant_chunks(
            question_vector=question_embedding,
            chunk_vectors=chunk_embeddings,
            chunks=my_chunks
        )

        context = "\n\n".join(relevant_texts)
        try:
            answer = self.ai.ask_question_about_document(context, question)
        except Exception as e:
            print(f"AI Generation failed: {e}")
            raise HTTPException(
                status_code=500, detail="The AI failed to generate a response.")

        if not answer:
            raise HTTPException(
                status_code=422, detail="AI returned an empty response.")

        chat_entry = await RAGService.create_chat_entry(
            db=db,
            doc_id=doc_id,  # type: ignore
            file_id=file_id,
            query=question,
            answer=answer,
            sources=relevant_texts
        )

        return {
            "id": chat_entry.id,
            "question": question,
            "answer": answer,
            "sources": relevant_texts,
            "file_id": file_id,
            "document_id": doc_id,
        }
