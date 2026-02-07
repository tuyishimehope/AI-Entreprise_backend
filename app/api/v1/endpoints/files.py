from typing import List
import uuid
from fastapi import APIRouter
from app.services.document.document import DocumentService
from fastapi import APIRouter, UploadFile, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db

files_router = APIRouter(tags=["files"])


from fastapi import APIRouter, UploadFile, Depends, Path as PathParam
from fastapi.responses import FileResponse
from app.schemas.document import DocumentRead

files_router = APIRouter(prefix="/files", tags=["Documents"])

@files_router.post("", response_model=DocumentRead, status_code=201)
async def upload_document(file: UploadFile, db: AsyncSession = Depends(get_db)):
    return await DocumentService.upload_file(file, db)

@files_router.get("/{file_id}/download")
async def download_file(file_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    record = await DocumentService.get_file_content(file_id, db)
    return FileResponse(path=record.file_path, filename=record.file_name)

@files_router.get("", response_model=List[DocumentRead])
async def list_documents(db: AsyncSession = Depends(get_db)):
    return await DocumentService.get_all_files(db)