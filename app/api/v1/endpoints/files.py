from fastapi import APIRouter
from app.services.document.document import DocumentService
from fastapi import APIRouter, UploadFile, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db

files_router = APIRouter(tags=["files"])


@files_router.post("/file")
async def upload_document(file: UploadFile, db: AsyncSession = Depends(get_db)):
    return await DocumentService.upload_file(file, db)


@files_router.get("/file/{file_id}")
async def get_file(file_id, db: AsyncSession = Depends(get_db)):
    return await DocumentService.get_file_content(file_id=file_id, db=db)


@files_router.get("/file")
async def get_files(db: AsyncSession = Depends(get_db)):
    return await DocumentService.get_all_files(db)
