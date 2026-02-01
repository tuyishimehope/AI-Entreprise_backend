import os
import uuid
import shutil
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.file import File
from pypdf import PdfReader
from fastapi import HTTPException

UPLOAD_DIR = Path("app/storage")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class FileService:

    @staticmethod
    async def upload_file_service(file, db: AsyncSession):

        file_id = uuid.uuid4()
        unique_filename = f"{file_id}_{file.filename}"
        dest_path = UPLOAD_DIR / unique_filename

        with dest_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        new_file = File(
            id=file_id,
            filename=file.filename,
            file_path=str(dest_path)
        )

        db.add(new_file)
        await db.commit()
        await db.refresh(new_file)
        return new_file

    @staticmethod
    async def get_file_id(file_id, db: AsyncSession):
        result = await db.execute(select(File).where(File.id == file_id))
        file_record = result.scalars().first()

        if not file_record:
            print("file_record", file_record)
            raise HTTPException(status_code=404, detail="File not found")
        
        text_content = ""
        try:
            reader = PdfReader(file_record.file_path) # type: ignore
            for page in reader.pages:
                text_content += page.extract_text() + "\n"
        except Exception as e:
            raise ValueError(f"Could not read PDF: {e}")

        return {
            "filename": file_record.filename,
            "content": text_content,
            "file_path": file_record.file_path
        }
