"""
Upload Route — POST /upload
"""

import os
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.config import settings
from app.models.schemas import ErrorResponse, UploadResponse
from app.services.rag_pipeline import get_rag_pipeline
from app.utils.logger import logger

router = APIRouter(prefix="/upload", tags=["Upload"])

MAX_BYTES = settings.MAX_FILE_SIZE_MB * 1024 * 1024


@router.post(
    "",
    response_model=UploadResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Upload a banking document for indexing",
)
async def upload_document(file: UploadFile = File(...)) -> UploadResponse:
    """
    Upload a **PDF**, **TXT**, or **DOCX** document to be ingested into the
    knowledge base. The file is chunked, embedded, and stored in ChromaDB.

    - Maximum file size: {MAX_FILE_SIZE_MB} MB
    - Supported types: pdf, txt, docx
    """
    # ── Validation ─────────────────────────────────────────────────────────────
    ext = Path(file.filename).suffix.lower().lstrip(".")
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '.{ext}'. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}",
        )

    content = await file.read()
    if len(content) > MAX_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds {settings.MAX_FILE_SIZE_MB} MB limit.",
        )
    if len(content) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")

    # ── Save to disk ───────────────────────────────────────────────────────────
    safe_name = f"{uuid.uuid4().hex}_{file.filename}"
    save_path = os.path.join(settings.UPLOAD_DIR, safe_name)
    with open(save_path, "wb") as f:
        f.write(content)

    logger.info(f"File saved: {safe_name} ({len(content)} bytes)")

    # ── Ingest into RAG pipeline ───────────────────────────────────────────────
    try:
        pipeline = get_rag_pipeline()
        chunks_indexed, collection_size = pipeline.ingest_document(save_path)

        return UploadResponse(
            message=f"Document '{file.filename}' successfully ingested.",
            filename=file.filename,
            chunks_indexed=chunks_indexed,
            collection_size=collection_size,
        )

    except ValueError as exc:
        os.remove(save_path)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    except Exception as exc:
        logger.error(f"Ingestion failed for {file.filename}: {exc}", exc_info=True)
        if os.path.exists(save_path):
            os.remove(save_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Document ingestion failed. Please try again.",
        )
