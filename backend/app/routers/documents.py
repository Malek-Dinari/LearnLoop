from fastapi import APIRouter, UploadFile, File, HTTPException

from app.config import settings
from app.models import DocumentUploadResponse
from app.services.document_service import document_service

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(400, "No filename provided")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ("pdf", "txt"):
        raise HTTPException(400, "Only PDF and TXT files are supported")

    content = await file.read()
    if len(content) > settings.max_file_size_mb * 1024 * 1024:
        raise HTTPException(400, f"File too large. Max {settings.max_file_size_mb}MB")

    result = await document_service.process_upload(file.filename, content)
    return DocumentUploadResponse(**result)
