from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.exceptions import DocumentProcessingError
from app.models import DocumentUploadResponse
from app.services.document_service import document_service

router = APIRouter(prefix="/api/documents", tags=["documents"])

ALLOWED_EXTENSIONS = ("pdf", "txt", "docx", "pptx")


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession | None = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(400, "No filename provided")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            400,
            f"Unsupported file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(400, "File is empty")
    if len(content) > settings.max_file_size_mb * 1024 * 1024:
        raise HTTPException(400, f"File too large. Max {settings.max_file_size_mb}MB")

    try:
        result = await document_service.process_upload(file.filename, content, db)
    except DocumentProcessingError as exc:
        raise HTTPException(422, str(exc))

    return DocumentUploadResponse(**result)
