import uuid
import shutil
from pathlib import Path
from fastapi.responses import FileResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from pypdf import PdfReader
from fastapi import HTTPException
from app.models.document_record import DocumentRecord
import hashlib
from fastapi import UploadFile

UPLOAD_DIR = Path("app/storage")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class DocumentService:
    @staticmethod
    async def get_file_hash(file: UploadFile):
        hasher = hashlib.md5()

        chunk_size = 64 * 1024
        while chunk := await file.read(chunk_size):
            hasher.update(chunk)

        await file.seek(0)
        return hasher.hexdigest()

    @staticmethod
    async def upload_file(file: UploadFile, db: AsyncSession):

        file_id = uuid.uuid4()
        unique_filename = f"{file_id}_{file.filename}"
        dest_path = UPLOAD_DIR / unique_filename

        with dest_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        new_file = DocumentRecord(
            id=file_id,
            file_name=file.filename,
            file_path=str(dest_path),
            file_hash=await DocumentService.get_file_hash(file),
            created_at=func.now()
        )

        db.add(new_file)
        await db.commit()
        await db.refresh(new_file)
        return new_file

    @staticmethod
    async def get_file(file_id, db: AsyncSession):
        result = await db.execute(select(DocumentRecord).where(DocumentRecord.id == file_id))
        file_record = result.scalars().first()

        if not file_record:
            print("file_record", file_record)
            raise HTTPException(status_code=404, detail="File not found")

        text_content = ""
        try:
            reader = PdfReader(file_record.file_path)  # type: ignore
            for page in reader.pages:
                text_content += page.extract_text() + "\n"
        except Exception as e:
            raise ValueError(f"Could not read PDF: {e}")

        return {
            "file_name": file_record.file_name,
            "content": text_content,
            "file_path": file_record.file_path
        }
        
    @staticmethod
    async def get_file_content(file_id, db: AsyncSession):
        result = await db.execute(select(DocumentRecord).where(DocumentRecord.id == file_id))
        file_record = result.scalars().first()

        if not file_record:
            print("file_record", file_record)
            raise HTTPException(status_code=404, detail="File not found")

        text_content = ""
        try:
            reader = PdfReader(file_record.file_path)  # type: ignore
            for page in reader.pages:
                text_content += page.extract_text() + "\n"
        except Exception as e:
            raise ValueError(f"Could not read PDF: {e}")

        return FileResponse(
            filename=file_record.file_name,
            path=file_record.file_path
        )

    @staticmethod
    async def get_all_files(db: AsyncSession):
        result = await db.execute(select(DocumentRecord))
        return result.scalars().all()