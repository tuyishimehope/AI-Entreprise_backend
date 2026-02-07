import uuid
import hashlib
import aiofiles
import os
from pathlib import Path
from typing import List

from fastapi import HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pypdf import PdfReader

from app.models.document_record import DocumentRecord
from app.schemas.document import DocumentCreate, DocumentRead, DocumentSchema

UPLOAD_DIR = Path("app/storage")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class DocumentService:

    @staticmethod
    async def get_file_hash(file: UploadFile) -> str:
        hasher = hashlib.md5()
        await file.seek(0)
        while chunk := await file.read(64 * 1024):
            hasher.update(chunk)
        await file.seek(0)
        return hasher.hexdigest()

    @staticmethod
    def _sync_extract_text(file_path: str) -> str:
        """Isolated sync worker for CPU-bound PDF parsing."""
        try:
            reader = PdfReader(file_path)
            return "\n".join([p.extract_text() for p in reader.pages if p.extract_text()])
        except Exception as e:
            raise ValueError(f"Internal PDF parsing error: {str(e)}")

    @staticmethod
    async def upload_file(file: UploadFile, db: AsyncSession):
        file_hash = await DocumentService.get_file_hash(file)

        existing = await db.execute(select(DocumentRecord).where(DocumentRecord.file_hash == file_hash))
        if duplicate := existing.scalar_one_or_none():
            return duplicate

        file_id = uuid.uuid4()
        extension = Path(file.filename).suffix if file.filename else ".pdf"
        dest_path = UPLOAD_DIR / f"{file_id}{extension}"

        try:
            content = await file.read()
            async with aiofiles.open(dest_path, "wb") as buffer:
                await buffer.write(content)

            extracted_text = await run_in_threadpool(DocumentService._sync_extract_text, str(dest_path))

            new_file = DocumentRecord(
                id=file_id,
                file_name=file.filename,
                file_path=str(dest_path),
                file_hash=file_hash,
                chunks=[extracted_text] if extracted_text else []
            )

            db.add(new_file)
            await db.commit()
            await db.refresh(new_file)
            return new_file

        except Exception as e:
            if dest_path.exists():
                os.remove(dest_path)
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(
                status_code=500, detail=f"Upload failed: {str(e)}")

    @staticmethod
    async def get_file_content(file_id: uuid.UUID, db: AsyncSession):
        result = await db.execute(select(DocumentRecord).where(DocumentRecord.id == file_id))
        record = result.scalar_one_or_none()
        if not record:
            raise HTTPException(status_code=404, detail="Document not found")

        return record

    @staticmethod
    async def get_record(file_id: uuid.UUID, db: AsyncSession):
        result = await db.execute(select(DocumentRecord).where(DocumentRecord.id == file_id))
        record = result.scalar_one_or_none()
        if not record:
            raise HTTPException(status_code=404, detail="Document not found")

        text_content = ""
        try:
            reader = PdfReader(record.file_path)  # type: ignore
            for page in reader.pages:
                text_content += page.extract_text() + "\n"
        except Exception as e:
            raise ValueError(f"Could not read PDF: {e}")

        return {
            "file_name": record.file_name,
            "content": text_content,
            "file_path": record.file_path
        }

    @staticmethod
    async def get_all_files(db: AsyncSession) -> List[DocumentRecord]:
        result = await db.execute(select(DocumentRecord))
        return list(result.scalars().all())
