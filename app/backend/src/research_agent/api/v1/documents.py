"""Documents API endpoints."""

import logging
from io import BytesIO
from pathlib import Path
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, RedirectResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.api.deps import get_db, get_embedding_service
from research_agent.application.dto.document import (
    DocumentListResponse,
    DocumentResponse,
    DocumentUploadResponse,
)
from research_agent.application.use_cases.document.delete_document import (
    DeleteDocumentInput,
    DeleteDocumentUseCase,
)
from research_agent.application.use_cases.document.list_documents import (
    ListDocumentsInput,
    ListDocumentsUseCase,
)
from research_agent.application.use_cases.document.upload_document import (
    UploadDocumentInput,
    UploadDocumentUseCase,
)
from research_agent.config import get_settings
from research_agent.domain.services.chunking_service import ChunkingService
from research_agent.infrastructure.database.repositories.sqlalchemy_chunk_repo import (
    SQLAlchemyChunkRepository,
)
from research_agent.infrastructure.database.repositories.sqlalchemy_document_repo import (
    SQLAlchemyDocumentRepository,
)
from research_agent.infrastructure.embedding.openrouter import OpenRouterEmbeddingService
from research_agent.infrastructure.pdf.pymupdf import PyMuPDFParser
from research_agent.infrastructure.storage.local import LocalStorageService
from research_agent.infrastructure.storage.supabase_storage import SupabaseStorageService
from research_agent.infrastructure.database.models import DocumentModel
from research_agent.domain.entities.task import TaskType
from research_agent.worker.service import TaskQueueService
from research_agent.shared.exceptions import NotFoundError, PDFProcessingError

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()


# ============== Request/Response Models ==============

class PresignRequest(BaseModel):
    """Request for generating a presigned upload URL."""
    filename: str
    content_type: Optional[str] = "application/pdf"


class PresignResponse(BaseModel):
    """Response containing presigned upload URL."""
    upload_url: str
    file_path: str
    token: str
    expires_at: str


class ConfirmUploadRequest(BaseModel):
    """Request to confirm a successful upload."""
    file_path: str
    filename: str
    file_size: int
    content_type: Optional[str] = "application/pdf"


# ============== Helper Functions ==============

def get_supabase_storage() -> Optional[SupabaseStorageService]:
    """Get Supabase storage service if configured."""
    if settings.supabase_url and settings.supabase_service_role_key:
        return SupabaseStorageService(
            supabase_url=settings.supabase_url,
            service_role_key=settings.supabase_service_role_key,
            bucket_name=settings.storage_bucket,
        )
    return None


# ============== Presigned URL Endpoints ==============

@router.post("/projects/{project_id}/documents/presign", response_model=PresignResponse)
async def get_presigned_upload_url(
    project_id: UUID,
    request: PresignRequest,
) -> PresignResponse:
    """
    Generate a presigned URL for direct file upload to Supabase Storage.
    
    The client should:
    1. Call this endpoint to get a presigned URL
    2. Upload the file directly to the presigned URL (PUT request)
    3. Call /confirm endpoint to register the document
    """
    storage = get_supabase_storage()
    if not storage:
        raise HTTPException(
            status_code=501,
            detail="Supabase Storage not configured. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY."
        )
    
    try:
        result = await storage.create_signed_upload_url(
            project_id=str(project_id),
            filename=request.filename,
        )
        
        return PresignResponse(
            upload_url=result.upload_url,
            file_path=result.file_path,
            token=result.token,
            expires_at=result.expires_at.isoformat(),
        )
    except Exception as e:
        logger.error(f"Failed to create presigned URL: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create presigned URL: {str(e)}")


@router.post("/projects/{project_id}/documents/confirm", response_model=DocumentUploadResponse, status_code=202)
async def confirm_upload(
    project_id: UUID,
    request: ConfirmUploadRequest,
    session: AsyncSession = Depends(get_db),
) -> DocumentUploadResponse:
    """
    Confirm a successful file upload and schedule async processing.
    
    This endpoint should be called after the file has been uploaded to Supabase Storage.
    It will:
    1. Verify the file exists in storage
    2. Create a document record with 'pending' status
    3. Schedule a background task for processing
    
    Returns 202 Accepted - processing happens asynchronously.
    """
    storage = get_supabase_storage()
    if not storage:
        raise HTTPException(
            status_code=501,
            detail="Supabase Storage not configured."
        )
    
    # Verify file exists in storage
    exists = await storage.file_exists(request.file_path)
    if not exists:
        raise HTTPException(
            status_code=400,
            detail=f"File not found in storage: {request.file_path}"
        )
    
    try:
        # Create document record with pending status
        from uuid import uuid4
        document_id = uuid4()
        
        document = DocumentModel(
            id=document_id,
            project_id=project_id,
            filename=request.filename,
            original_filename=request.filename,
            file_path=request.file_path,
            file_size=request.file_size,
            mime_type="application/pdf",
            status="pending",
        )
        session.add(document)
        await session.flush()
        
        # Schedule background processing task
        task_service = TaskQueueService(session)
        await task_service.push(
            task_type=TaskType.PROCESS_DOCUMENT,
            payload={
                "document_id": str(document_id),
                "project_id": str(project_id),
                "file_path": request.file_path,
            },
            priority=0,
        )
        
        await session.commit()
        
        logger.info(f"Document {document_id} scheduled for processing")
        
        return DocumentUploadResponse(
            id=document_id,
            filename=request.filename,
            page_count=0,
            status="pending",
            message="Document uploaded successfully. Processing scheduled.",
        )
        
    except Exception as e:
        logger.error(f"Failed to schedule document processing: {e}")
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to schedule processing: {str(e)}")


# ============== Standard Document Endpoints ==============

@router.get("/projects/{project_id}/documents", response_model=DocumentListResponse)
async def list_documents(
    project_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> DocumentListResponse:
    """List all documents for a project."""
    document_repo = SQLAlchemyDocumentRepository(session)
    use_case = ListDocumentsUseCase(document_repo)

    result = await use_case.execute(ListDocumentsInput(project_id=project_id))

    return DocumentListResponse(
        items=[
            DocumentResponse(
                id=item.id,
                project_id=item.project_id,
                filename=item.filename,
                file_size=item.file_size,
                page_count=item.page_count,
                status=item.status,
                created_at=item.created_at,
            )
            for item in result.items
        ],
        total=result.total,
    )


@router.post("/projects/{project_id}/documents", response_model=DocumentUploadResponse, status_code=201)
async def upload_document(
    project_id: UUID,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db),
    embedding_service: OpenRouterEmbeddingService = Depends(get_embedding_service),
) -> DocumentUploadResponse:
    """Upload a PDF document."""
    # Validate file type
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    # Get file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Seek back to start

    # Create dependencies
    document_repo = SQLAlchemyDocumentRepository(session)
    chunk_repo = SQLAlchemyChunkRepository(session)
    storage = LocalStorageService(settings.upload_dir)
    pdf_parser = PyMuPDFParser()
    chunking_service = ChunkingService()

    use_case = UploadDocumentUseCase(
        document_repo=document_repo,
        chunk_repo=chunk_repo,
        storage=storage,
        pdf_parser=pdf_parser,
        embedding_service=embedding_service,
        chunking_service=chunking_service,
    )

    try:
        result = await use_case.execute(
            UploadDocumentInput(
                project_id=project_id,
                filename=file.filename,
                file_content=file.file,
                file_size=file_size,
            )
        )

        return DocumentUploadResponse(
            id=result.id,
            filename=result.filename,
            page_count=result.page_count,
            status=result.status,
            message="Document uploaded and processed successfully",
        )

    except PDFProcessingError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> DocumentResponse:
    """Get document details by ID."""
    document_repo = SQLAlchemyDocumentRepository(session)
    document = await document_repo.find_by_id(document_id)

    if not document:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found")

    return DocumentResponse(
        id=document.id,
        project_id=document.project_id,
        filename=document.filename,
        file_size=document.file_size,
        page_count=document.page_count,
        status=document.status.value,
        created_at=document.created_at,
    )


@router.get("/documents/{document_id}/file")
async def get_document_file(
    document_id: UUID,
    session: AsyncSession = Depends(get_db),
):
    """
    Get the PDF file for a document.
    
    If the file is stored in Supabase Storage, returns a redirect to a signed URL.
    Otherwise, returns the file directly from local storage.
    """
    document_repo = SQLAlchemyDocumentRepository(session)
    document = await document_repo.find_by_id(document_id)

    if not document:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found")

    # Check if file is stored in Supabase Storage (path starts with "projects/")
    if document.file_path.startswith("projects/") and not Path(document.file_path).is_absolute():
        storage = get_supabase_storage()
        if storage:
            try:
                # Generate a signed download URL
                result = await storage.create_signed_download_url(
                    file_path=document.file_path,
                    expires_in_seconds=3600,  # 1 hour
                )
                # Redirect to the signed URL
                return RedirectResponse(url=result.signed_url, status_code=302)
            except Exception as e:
                logger.error(f"Failed to create signed download URL: {e}")
                # Fall through to try local storage
    
    # Try local storage
    file_path = Path(document.file_path)
    if not file_path.exists():
        # Also try with upload_dir prefix
        file_path = Path(settings.upload_dir) / document.file_path
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="PDF file not found on server")

    return FileResponse(
        path=str(file_path),
        filename=document.filename,
        media_type="application/pdf",
    )


@router.get("/documents/{document_id}/chunks")
async def get_document_chunks(
    document_id: UUID,
    session: AsyncSession = Depends(get_db),
):
    """Get parsed text chunks for a document (for text preview/debugging)."""
    document_repo = SQLAlchemyDocumentRepository(session)
    chunk_repo = SQLAlchemyChunkRepository(session)
    
    # Verify document exists
    document = await document_repo.find_by_id(document_id)
    if not document:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found")
    
    # Get chunks
    chunks = await chunk_repo.find_by_document(document_id)
    
    return {
        "document_id": str(document_id),
        "filename": document.filename,
        "chunks": [
            {
                "chunk_index": chunk.chunk_index,
                "page_number": chunk.page_number,
                "content": chunk.content,
            }
            for chunk in chunks
        ],
        "total": len(chunks),
    }


@router.delete("/documents/{document_id}", status_code=204)
async def delete_document(
    document_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> None:
    """Delete a document and its file from storage."""
    document_repo = SQLAlchemyDocumentRepository(session)
    chunk_repo = SQLAlchemyChunkRepository(session)
    local_storage = LocalStorageService(settings.upload_dir)

    # Get document first to check file path
    document = await document_repo.find_by_id(document_id)
    if not document:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found")

    # Delete from Supabase Storage if file is stored there
    # file_path could be:
    # - "projects/{project_id}/{uuid}.pdf" (Supabase Storage)
    # - "data/uploads/projects/{project_id}/{uuid}.pdf" (Local storage)
    supabase_storage = get_supabase_storage()
    if supabase_storage and document.file_path:
        # Extract the Supabase path if it's a local path
        storage_path = document.file_path
        if "projects/" in storage_path and not storage_path.startswith("projects/"):
            # Convert local path to Supabase path
            # e.g., "data/uploads/projects/..." -> "projects/..."
            idx = storage_path.find("projects/")
            storage_path = storage_path[idx:]
        
        if storage_path.startswith("projects/"):
            try:
                logger.info(f"Attempting to delete from Supabase Storage: {storage_path}")
                await supabase_storage.delete_file(storage_path)
                logger.info(f"Deleted file from Supabase Storage: {storage_path}")
            except Exception as e:
                logger.warning(f"Failed to delete from Supabase Storage: {e}")

    use_case = DeleteDocumentUseCase(
        document_repo=document_repo,
        chunk_repo=chunk_repo,
        storage=local_storage,
    )

    try:
        await use_case.execute(DeleteDocumentInput(document_id=document_id))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
