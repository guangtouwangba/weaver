"""Documents API endpoints."""

import os
import tempfile
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.api.auth.supabase import UserContext, get_optional_user
from research_agent.api.deps import get_db, get_embedding_service
from research_agent.application.dto.document import (
    DocumentListResponse,
    DocumentResponse,
    DocumentUploadResponse,
)
from research_agent.application.services.async_cleanup_service import (
    fire_and_forget_cleanup,
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
from research_agent.domain.entities.task import TaskType
from research_agent.domain.services.chunking_service import ChunkingService
from research_agent.infrastructure.database.models import DocumentModel
from research_agent.infrastructure.database.repositories.chunk_repo_factory import (
    get_chunk_repository,
)
from research_agent.infrastructure.database.repositories.sqlalchemy_document_repo import (
    SQLAlchemyDocumentRepository,
)
from research_agent.infrastructure.database.repositories.sqlalchemy_highlight_repo import (
    SQLAlchemyHighlightRepository,
)
from research_agent.infrastructure.database.repositories.sqlalchemy_pending_cleanup_repo import (
    SQLAlchemyPendingCleanupRepository,
)
from research_agent.infrastructure.database.repositories.sqlalchemy_project_repo import (
    SQLAlchemyProjectRepository,
)
from research_agent.infrastructure.embedding.openrouter import OpenRouterEmbeddingService
from research_agent.infrastructure.storage.local import LocalStorageService
from research_agent.infrastructure.storage.supabase_storage import SupabaseStorageService
from research_agent.infrastructure.thumbnail import ThumbnailFactory
from research_agent.shared.exceptions import DocumentProcessingError, NotFoundError
from research_agent.shared.utils.logger import setup_logger
from research_agent.worker.service import TaskQueueService

logger = setup_logger(__name__)
router = APIRouter()
settings = get_settings()


# ============== Request/Response Models ==============


class PresignRequest(BaseModel):
    """Request for generating a presigned upload URL."""

    filename: str
    content_type: str | None = "application/pdf"


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
    content_type: str | None = "application/pdf"


class HighlightCreateRequest(BaseModel):
    """Request to create a highlight."""

    page_number: int = Field(..., alias="pageNumber")
    start_offset: int = Field(..., alias="startOffset")
    end_offset: int = Field(..., alias="endOffset")
    color: str  # yellow, green, blue, pink
    note: str | None = None
    rects: list[dict[str, float]] | None = None

    model_config = {"populate_by_name": True}


class HighlightUpdateRequest(BaseModel):
    """Request to update a highlight."""

    color: str | None = None
    note: str | None = None


class HighlightResponse(BaseModel):
    """Response model for highlight."""

    id: str
    document_id: str = Field(..., alias="documentId")
    page_number: int = Field(..., alias="pageNumber")
    start_offset: int = Field(..., alias="startOffset")
    end_offset: int = Field(..., alias="endOffset")
    color: str
    note: str | None = None
    rects: list[dict[str, float]] | None = None
    created_at: str = Field(..., alias="createdAt")
    updated_at: str = Field(..., alias="updatedAt")

    model_config = {"populate_by_name": True}


# ============== Helper Functions ==============


def get_supabase_storage() -> SupabaseStorageService | None:
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
    user: UserContext = Depends(get_optional_user),
) -> PresignResponse:
    """
    Generate a presigned URL for direct file upload to Supabase Storage.

    The client should:
    1. Call this endpoint to get a presigned URL
    2. Upload the file directly to the presigned URL (PUT request)
    3. Call /confirm endpoint to register the document
    """
    logger.info(
        f"[Presign] Request received: project_id={project_id}, "
        f"filename={request.filename}, content_type={request.content_type}"
    )

    # Check Supabase configuration
    logger.debug(
        f"[Presign] Supabase config check: "
        f"url={'set' if settings.supabase_url else 'not set'}, "
        f"key={'set' if settings.supabase_service_role_key else 'not set'}, "
        f"bucket={settings.storage_bucket}"
    )

    authorization_bypass = settings.auth_bypass_enabled
    # Verify project ownership if auth is enabled
    storage = get_supabase_storage()
    if not storage:
        error_msg = (
            "Supabase Storage not configured. "
            f"SUPABASE_URL={'set' if settings.supabase_url else 'NOT SET'}, "
            f"SUPABASE_SERVICE_ROLE_KEY={'set' if settings.supabase_service_role_key else 'NOT SET'}"
        )
        logger.error(f"[Presign] Configuration error: {error_msg}")
        raise HTTPException(status_code=501, detail=error_msg)

    # Determine user ID for path scoping
    user_id = user.user_id if user else "public"

    # Ownership Check
    if not authorization_bypass:
        # We need session to access DB
        async with AsyncSession(get_db.engine) as db_session:
            project_repo = SQLAlchemyProjectRepository(db_session)
            project = await project_repo.find_by_id(project_id)
            if not project:
                raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
            if project.user_id and project.user_id != user_id:
                raise HTTPException(status_code=403, detail="Not authorized")

    try:
        logger.info(
            f"[Presign] Creating signed upload URL for project {project_id} (user={user_id})"
        )
        result = await storage.create_signed_upload_url(
            project_id=str(project_id),
            filename=request.filename,
            user_id=user_id,
        )

        logger.info(
            f"[Presign] Successfully created presigned URL: "
            f"file_path={result.file_path}, "
            f"expires_at={result.expires_at}"
        )

        return PresignResponse(
            upload_url=result.upload_url,
            file_path=result.file_path,
            token=result.token,
            expires_at=result.expires_at.isoformat(),
        )
    except HTTPException:
        # Re-raise HTTPException as-is
        raise
    except Exception as e:
        error_detail = str(e)
        error_type = type(e).__name__

        logger.error(
            f"[Presign] Failed to create presigned URL: "
            f"project_id={project_id}, "
            f"filename={request.filename}, "
            f"error_type={error_type}, "
            f"error={error_detail}",
            exc_info=True,  # Include full stack trace
        )

        # Include more context in error message
        detail_msg = f"Failed to create presigned URL: {error_detail} (type: {error_type})"
        raise HTTPException(status_code=500, detail=detail_msg)


@router.post(
    "/projects/{project_id}/documents/confirm",
    response_model=DocumentUploadResponse,
    status_code=202,
)
async def confirm_upload(
    project_id: UUID,
    request: ConfirmUploadRequest,
    session: AsyncSession = Depends(get_db),
    user: UserContext = Depends(get_optional_user),
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
    # Verify project ownership
    from research_agent.api.deps import verify_project_ownership

    await verify_project_ownership(project_id, user.user_id, session)

    storage = get_supabase_storage()
    if not storage:
        raise HTTPException(status_code=501, detail="Supabase Storage not configured.")

    # Verify file exists in storage
    exists = await storage.file_exists(request.file_path)
    if not exists:
        raise HTTPException(
            status_code=400, detail=f"File not found in storage: {request.file_path}"
        )

    try:
        # Create document record with pending status
        from uuid import uuid4

        document_id = uuid4()

        document = DocumentModel(
            id=document_id,
            project_id=project_id,
            user_id=user.user_id,
            filename=request.filename,
            original_filename=request.filename,
            file_path=request.file_path,
            file_size=request.file_size,
            mime_type=request.content_type,
            status="pending",
        )
        session.add(document)
        await session.flush()

        # Generate thumbnail synchronously (if supported by ThumbnailFactory)
        file_extension = Path(request.filename).suffix.lower()
        if ThumbnailFactory.is_supported(extension=file_extension):
            try:
                local_file_path = request.file_path
                is_temp = False

                # If file is in Supabase (remote), download it first
                if "projects/" in request.file_path and storage:
                    logger.info(f"[THUMBNAIL] Downloading remote file: {request.file_path}")
                    content = await storage.download_file(request.file_path)

                    # Create temp file with correct extension
                    tmp_fd, tmp_path = tempfile.mkstemp(suffix=file_extension)
                    os.write(tmp_fd, content)
                    os.close(tmp_fd)

                    local_file_path = tmp_path
                    is_temp = True

                logger.info(f"[THUMBNAIL] Generating from: {local_file_path}")

                output_dir = (Path(settings.upload_dir) / "thumbnails").resolve()
                result = await ThumbnailFactory.generate(
                    file_path=local_file_path,
                    document_id=document_id,
                    output_dir=output_dir,
                    extension=file_extension,
                )

                # Cleanup temp file
                if is_temp and os.path.exists(local_file_path):
                    os.remove(local_file_path)

                if result.success and result.path:
                    document.thumbnail_path = result.path
                    document.thumbnail_status = "ready"
                    session.add(document)  # Update record
                    logger.info(f"✅ Thumbnail generated immediately for {document_id}")
                else:
                    logger.warning(f"⚠️ Thumbnail generation returned: {result.error}")

            except Exception as e:
                logger.warning(f"⚠️ Immediate thumbnail generation failed: {e}")
                if "is_temp" in locals() and is_temp and os.path.exists(local_file_path):
                    os.remove(local_file_path)
        else:
            logger.info(
                f"⏭️ Skipping thumbnail generation for {file_extension} file (not supported)"
            )

        # Schedule background processing task
        task_service = TaskQueueService(session)
        task = await task_service.push(
            task_type=TaskType.PROCESS_DOCUMENT,
            payload={
                "document_id": str(document_id),
                "project_id": str(project_id),
                "file_path": request.file_path,
                "user_id": user.user_id,  # Pass user ID for settings lookup
            },
            priority=0,
        )

        await session.commit()

        logger.info(
            f"✅ Document {document_id} scheduled for processing - "
            f"task_id={task.id}, task_type={task.task_type.value}, "
            f"environment={settings.environment}"
        )

        return DocumentUploadResponse(
            id=document_id,
            filename=request.filename,
            page_count=0,
            status="pending",
            thumbnail_url=f"/api/v1/documents/{document_id}/thumbnail"
            if document.thumbnail_status == "ready"
            else None,
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
    user: UserContext = Depends(get_optional_user),
) -> DocumentListResponse:
    """List all documents for a project."""
    # Verify project ownership
    if not settings.auth_bypass_enabled:
        project_repo = SQLAlchemyProjectRepository(session)
        project = await project_repo.find_by_id(project_id)
        if not project:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

        # Check if project belongs to user
        user_id = user.user_id if user else None
        if project.user_id and project.user_id != user_id:
            # If project has user_id but request user doesn't match (or is None)
            raise HTTPException(status_code=403, detail="Not authorized to access this project")

    document_repo = SQLAlchemyDocumentRepository(session)
    # ... (existing code, ensure user_scoped list if needed, but project is already scoped)
    use_case = ListDocumentsUseCase(document_repo)

    result = await use_case.execute(
        ListDocumentsInput(
            project_id=project_id,
            user_id=user.user_id if user else None,
        )
    )

    return DocumentListResponse(
        items=[
            DocumentResponse(
                id=item.id,
                project_id=item.project_id,
                filename=item.filename,
                file_size=item.file_size,
                page_count=item.page_count,
                status=item.status,
                thumbnail_url=f"/api/v1/documents/{item.id}/thumbnail"
                if item.thumbnail_status == "ready" or item.thumbnail_path
                else None,
                thumbnail_status=item.thumbnail_status,
                created_at=item.created_at,
            )
            for item in result.items
        ],
        total=result.total,
    )


@router.post(
    "/projects/{project_id}/documents",
    response_model=DocumentUploadResponse,
    status_code=201,
    deprecated=True,
    description="**DEPRECATED**: Use presigned URL upload flow instead (POST /presign -> PUT to upload_url -> POST /confirm). This synchronous endpoint blocks until processing completes and may timeout for large files.",
)
async def upload_document(
    project_id: UUID,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db),
    embedding_service: OpenRouterEmbeddingService = Depends(get_embedding_service),
    user: UserContext = Depends(get_optional_user),
) -> DocumentUploadResponse:
    """
    Upload a PDF document (DEPRECATED).

    **Warning**: This endpoint is deprecated. Use the presigned URL upload flow for better
    reliability and progress tracking:
    1. POST /projects/{project_id}/documents/presign - Get presigned upload URL
    2. PUT to upload_url - Upload file directly to storage
    3. POST /projects/{project_id}/documents/confirm - Confirm and start processing

    The new flow supports WebSocket notifications for real-time status updates.
    """
    # Debug logging
    logger.info(
        f"[Upload] Received upload request: project_id={project_id}, filename={file.filename}, content_type={file.content_type}"
    )
    logger.info(f"[Upload] User context: user_id={user.user_id}, is_anonymous={user.is_anonymous}")
    logger.info(f"[Upload] Auth bypass enabled: {settings.auth_bypass_enabled}")

    # Verify project ownership
    if not settings.auth_bypass_enabled:
        project_repo = SQLAlchemyProjectRepository(session)
        project = await project_repo.find_by_id(project_id)
        if not project:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

        user_id = user.user_id if user else None
        if project.user_id and project.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to access this project")

    # Validate file type
    allowed_extensions = (".pdf", ".txt")
    if not file.filename or not file.filename.lower().endswith(allowed_extensions):
        raise HTTPException(
            status_code=400, detail=f"Only {', '.join(allowed_extensions)} files are supported"
        )

    # Get file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Seek back to start

    # Create dependencies
    document_repo = SQLAlchemyDocumentRepository(session)
    chunk_repo = get_chunk_repository(session)
    storage = LocalStorageService(settings.upload_dir)
    chunking_service = ChunkingService()

    # Determine user ID for path scoping
    user_id = user.user_id if user else "public"

    use_case = UploadDocumentUseCase(
        document_repo=document_repo,
        chunk_repo=chunk_repo,
        storage=storage,
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
                user_id=user_id,
            )
        )

        return DocumentUploadResponse(
            id=result.id,
            filename=result.filename,
            page_count=result.page_count,
            status=result.status,
            message="Document uploaded and processed successfully",
            thumbnail_url=f"/api/v1/documents/{result.id}/thumbnail"
            if result.thumbnail_status == "ready"
            else None,
        )

    except DocumentProcessingError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    session: AsyncSession = Depends(get_db),
    user: UserContext = Depends(get_optional_user),
) -> DocumentResponse:
    """Get document details by ID."""
    document_repo = SQLAlchemyDocumentRepository(session)
    document = await document_repo.find_by_id(document_id)

    if not document:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found")

    # Verify ownership
    if not settings.auth_bypass_enabled:
        project_repo = SQLAlchemyProjectRepository(session)
        project = await project_repo.find_by_id(document.project_id)

        if project:
            user_id = user.user_id if user else None
            # Only enforce if project has an owner
            if project.user_id and project.user_id != user_id:
                raise HTTPException(
                    status_code=403, detail="Not authorized to access this document"
                )

    return DocumentResponse(
        id=document.id,
        project_id=document.project_id,
        filename=document.filename,
        file_size=document.file_size,
        page_count=document.page_count,
        status=document.status.value,
        graph_status=getattr(document, "graph_status", None),
        summary=getattr(document, "summary", None),
        thumbnail_url=f"/api/v1/documents/{document.id}/thumbnail"
        if document.thumbnail_status == "ready" or document.thumbnail_path
        else None,
        thumbnail_status=document.thumbnail_status,
        created_at=document.created_at,
    )


@router.get("/documents/{document_id}/file")
async def get_document_file(
    document_id: UUID,
    session: AsyncSession = Depends(get_db),
    user: UserContext = Depends(get_optional_user),
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

    # Verify ownership
    if not settings.auth_bypass_enabled:
        project_repo = SQLAlchemyProjectRepository(session)
        project = await project_repo.find_by_id(document.project_id)

        if project:
            user_id = user.user_id if user else None
            if project.user_id and project.user_id != user_id:
                raise HTTPException(
                    status_code=403, detail="Not authorized to access this document"
                )

    # Check if file is stored in Supabase Storage (path starts with "projects/")
    if (
        document.file_path.startswith("projects/")
        or "projects/" in document.file_path
        and not Path(document.file_path).is_absolute()
    ):
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
            raise HTTPException(status_code=404, detail="Document file not found on server")

    return FileResponse(
        path=str(file_path),
        filename=document.filename,
        media_type=document.mime_type or "application/octet-stream",
    )


@router.get("/documents/{document_id}/thumbnail")
async def get_document_thumbnail(
    document_id: UUID,
    session: AsyncSession = Depends(get_db),
    user: UserContext = Depends(get_optional_user),
):
    """
    Get the thumbnail image for a document.

    Returns the thumbnail as a WebP image if available.
    """
    document_repo = SQLAlchemyDocumentRepository(session)
    document = await document_repo.find_by_id(document_id)

    logger.info(f"[DEBUG] Get thumbnail request: {document_id}")

    if not document:
        logger.warning(f"[DEBUG] Document not found: {document_id}")
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found")

    # Verify ownership
    if not settings.auth_bypass_enabled:
        project_repo = SQLAlchemyProjectRepository(session)
        project = await project_repo.find_by_id(document.project_id)

        if project:
            user_id = user.user_id if user else None
            # Allow thumbnail access if public? No, strict.
            if project.user_id and project.user_id != user_id:
                raise HTTPException(
                    status_code=403, detail="Not authorized to access this document"
                )

    logger.info(f"[DEBUG] DB Thumbnail path: {document.thumbnail_path}")

    if not document.thumbnail_path:
        raise HTTPException(status_code=404, detail="Thumbnail not available")

    thumbnail_path = Path(document.thumbnail_path)
    if not thumbnail_path.exists():
        logger.error(f"[DEBUG] File not found at: {thumbnail_path}")
        detail_msg = f"Thumbnail file not found at: {thumbnail_path} (Absolute? {thumbnail_path.is_absolute()})"
        raise HTTPException(status_code=404, detail=detail_msg)

    logger.info(f"[DEBUG] Serving thumbnail from: {thumbnail_path}")

    return FileResponse(
        path=str(thumbnail_path),
        media_type="image/webp",
    )


@router.get("/documents/{document_id}/chunks")
async def get_document_chunks(
    document_id: UUID,
    session: AsyncSession = Depends(get_db),
    user: UserContext = Depends(get_optional_user),
):
    """Get parsed text chunks for a document (for text preview/debugging)."""
    document_repo = SQLAlchemyDocumentRepository(session)
    chunk_repo = get_chunk_repository(session)

    # Verify document exists
    document = await document_repo.find_by_id(document_id)
    if not document:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found")

    # Verify ownership
    if not settings.auth_bypass_enabled:
        project_repo = SQLAlchemyProjectRepository(session)
        project = await project_repo.find_by_id(document.project_id)
        if project:
            user_id = user.user_id if user else None
            if project.user_id and project.user_id != user_id:
                raise HTTPException(
                    status_code=403, detail="Not authorized to access this document"
                )

    # Get chunks
    chunks = await chunk_repo.find_by_document(document_id)

    return {
        "document_id": str(document_id),
        "filename": document.filename,
        "chunks": [
            {
                "chunk_index": chunk.chunk_index,
                "page_number": chunk.metadata.get("page_number", 0) if chunk.metadata else 0,
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
    user: UserContext = Depends(get_optional_user),
) -> None:
    """
    Delete a document and its file from storage.

    This uses an async cleanup pattern:
    1. Record pending cleanup (fallback queue)
    2. Delete database records (chunks + document) - synchronous
    3. Fire-and-forget file cleanup - asynchronous

    Benefits:
    - Fast response time (~50ms vs ~500ms)
    - Files are eventually cleaned up even if async task fails
    - Better user experience
    """
    document_repo = SQLAlchemyDocumentRepository(session)
    chunk_repo = get_chunk_repository(session)
    cleanup_repo = SQLAlchemyPendingCleanupRepository(session)
    local_storage = LocalStorageService(settings.upload_dir)
    supabase_storage = get_supabase_storage()

    # Get document first to check file path
    document = await document_repo.find_by_id(document_id)
    if not document:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found")

    # Verify ownership
    if not settings.auth_bypass_enabled:
        project_repo = SQLAlchemyProjectRepository(session)
        project = await project_repo.find_by_id(document.project_id)
        if project:
            user_id = user.user_id if user else None
            if project.user_id and project.user_id != user_id:
                raise HTTPException(
                    status_code=403, detail="Not authorized to delete this document"
                )

    file_path = document.file_path
    project_id = document.project_id
    cleanup_id = None

    # Step 1: Record pending cleanup (fallback queue)
    if file_path:
        try:
            pending = await cleanup_repo.add(
                file_path=file_path,
                storage_type="both",
                document_id=document_id,
                project_id=project_id,
            )
            cleanup_id = pending.id
            logger.info(f"[DeleteDocument] Recorded pending cleanup: {cleanup_id}")
        except Exception as e:
            logger.warning(f"[DeleteDocument] Failed to record pending cleanup: {e}")

    # Step 2: Delete database records (synchronous - must succeed)
    # Step 2: Delete database records (synchronous - must succeed)
    # We use repository directly instead of UseCase since we want to handle cleanup separately
    try:
        # Delete chunks
        deleted_chunks = await chunk_repo.delete_by_document(document_id)
        logger.info(f"[DeleteDocument] Deleted {deleted_chunks} chunks for document {document_id}")

        # Delete document record
        await document_repo.delete(document_id)
        logger.info(f"[DeleteDocument] Deleted document record: {document_id}")

        # Commit the transaction
        await session.commit()
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        logger.error(f"[DeleteDocument] Failed to delete document: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {e}")

    # Step 3: Fire-and-forget file cleanup (asynchronous)
    if file_path:
        fire_and_forget_cleanup(
            file_path=file_path,
            local_storage=local_storage,
            supabase_storage=supabase_storage,
            cleanup_id=cleanup_id,
        )
        logger.info(f"[DeleteDocument] Scheduled async file cleanup for: {file_path}")


# ============== Highlight Endpoints ==============


def get_highlight_repo(session: AsyncSession = Depends(get_db)) -> SQLAlchemyHighlightRepository:
    """Get highlight repository."""
    return SQLAlchemyHighlightRepository(session)


@router.get("/documents/{document_id}/highlights", response_model=list[HighlightResponse])
async def list_highlights(
    document_id: UUID,
    session: AsyncSession = Depends(get_db),
    highlight_repo: SQLAlchemyHighlightRepository = Depends(get_highlight_repo),
    user: UserContext = Depends(get_optional_user),
) -> list[HighlightResponse]:
    """List all highlights for a document."""
    # Verify document exists
    document_repo = SQLAlchemyDocumentRepository(session)
    document = await document_repo.find_by_id(document_id)
    if not document:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found")

    # Verify ownership
    if not settings.auth_bypass_enabled:
        project_repo = SQLAlchemyProjectRepository(session)
        project = await project_repo.find_by_id(document.project_id)
        if project:
            user_id = user.user_id if user else None
            if project.user_id and project.user_id != user_id:
                raise HTTPException(
                    status_code=403, detail="Not authorized to access this document"
                )

    highlights = await highlight_repo.find_by_document(document_id, user_id=user.user_id)
    return [
        HighlightResponse(
            id=str(h.id),
            document_id=str(h.document_id),
            page_number=h.page_number,
            start_offset=h.start_offset,
            end_offset=h.end_offset,
            color=h.color,
            note=h.note,
            rects=h.rects.get("rects") if h.rects and isinstance(h.rects, dict) else None,
            created_at=h.created_at.isoformat(),
            updated_at=h.updated_at.isoformat(),
        )
        for h in highlights
    ]


@router.post(
    "/documents/{document_id}/highlights", response_model=HighlightResponse, status_code=201
)
async def create_highlight(
    document_id: UUID,
    request: HighlightCreateRequest,
    session: AsyncSession = Depends(get_db),
    highlight_repo: SQLAlchemyHighlightRepository = Depends(get_highlight_repo),
    user: UserContext = Depends(get_optional_user),
) -> HighlightResponse:
    """Create a new highlight."""
    # Verify document exists
    document_repo = SQLAlchemyDocumentRepository(session)
    document = await document_repo.find_by_id(document_id)
    if not document:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found")

    # Verify ownership
    if not settings.auth_bypass_enabled:
        project_repo = SQLAlchemyProjectRepository(session)
        project = await project_repo.find_by_id(document.project_id)
        if project:
            user_id = user.user_id if user else None
            if project.user_id and project.user_id != user_id:
                raise HTTPException(
                    status_code=403, detail="Not authorized to modify this document"
                )

    # Validate color
    valid_colors = ["yellow", "green", "blue", "pink"]
    if request.color not in valid_colors:
        raise HTTPException(
            status_code=400, detail=f"Invalid color. Must be one of: {', '.join(valid_colors)}"
        )

    # Convert rects list to dict format for JSONB storage
    rects_dict = None
    if request.rects:
        rects_dict = {"rects": request.rects}

    try:
        highlight = await highlight_repo.create(
            document_id=document_id,
            page_number=request.page_number,
            start_offset=request.start_offset,
            end_offset=request.end_offset,
            color=request.color,
            note=request.note,
            rects=rects_dict,
            user_id=user.user_id,
        )

        # Extract rects from JSONB format
        rects_list = None
        if highlight.rects and isinstance(highlight.rects, dict):
            rects_list = highlight.rects.get("rects")

        return HighlightResponse(
            id=str(highlight.id),
            document_id=str(highlight.document_id),
            page_number=highlight.page_number,
            start_offset=highlight.start_offset,
            end_offset=highlight.end_offset,
            color=highlight.color,
            note=highlight.note,
            rects=rects_list,
            created_at=highlight.created_at.isoformat(),
            updated_at=highlight.updated_at.isoformat(),
        )
    except HTTPException:
        # Re-raise HTTPException as-is
        raise
    except Exception as e:
        logger.error(
            f"Failed to create highlight: document_id={document_id}, "
            f"error_type={type(e).__name__}, error={str(e)}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=f"Failed to create highlight: {str(e)}")


@router.put("/documents/{document_id}/highlights/{highlight_id}", response_model=HighlightResponse)
async def update_highlight(
    document_id: UUID,
    highlight_id: UUID,
    request: HighlightUpdateRequest,
    session: AsyncSession = Depends(get_db),
    highlight_repo: SQLAlchemyHighlightRepository = Depends(get_highlight_repo),
) -> HighlightResponse:
    """Update a highlight."""
    # Verify document exists
    document_repo = SQLAlchemyDocumentRepository(session)
    document = await document_repo.find_by_id(document_id)
    if not document:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found")

    # Validate color if provided
    if request.color:
        valid_colors = ["yellow", "green", "blue", "pink"]
        if request.color not in valid_colors:
            raise HTTPException(
                status_code=400, detail=f"Invalid color. Must be one of: {', '.join(valid_colors)}"
            )

    highlight = await highlight_repo.update(
        highlight_id=highlight_id,
        color=request.color,
        note=request.note,
    )

    if not highlight:
        raise HTTPException(status_code=404, detail=f"Highlight {highlight_id} not found")

    if highlight.document_id != document_id:
        raise HTTPException(
            status_code=400,
            detail=f"Highlight {highlight_id} does not belong to document {document_id}",
        )

    await session.commit()

    return HighlightResponse(
        id=str(highlight.id),
        document_id=str(highlight.document_id),
        page_number=highlight.page_number,
        start_offset=highlight.start_offset,
        end_offset=highlight.end_offset,
        color=highlight.color,
        note=highlight.note,
        rects=highlight.rects.get("rects")
        if highlight.rects and isinstance(highlight.rects, dict)
        else None,
        created_at=highlight.created_at.isoformat(),
        updated_at=highlight.updated_at.isoformat(),
    )


@router.delete("/documents/{document_id}/highlights/{highlight_id}", status_code=204)
async def delete_highlight(
    document_id: UUID,
    highlight_id: UUID,
    session: AsyncSession = Depends(get_db),
    highlight_repo: SQLAlchemyHighlightRepository = Depends(get_highlight_repo),
) -> None:
    """Delete a highlight."""
    # Verify document exists
    document_repo = SQLAlchemyDocumentRepository(session)
    document = await document_repo.find_by_id(document_id)
    if not document:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found")

    # Verify highlight exists and belongs to document
    highlight = await highlight_repo.find_by_id(highlight_id)
    if not highlight:
        raise HTTPException(status_code=404, detail=f"Highlight {highlight_id} not found")

    if highlight.document_id != document_id:
        raise HTTPException(
            status_code=400,
            detail=f"Highlight {highlight_id} does not belong to document {document_id}",
        )

    await highlight_repo.delete(highlight_id)
    await session.commit()


# ===================
# Comments API
# ===================


class CommentCreateRequest(BaseModel):
    """Request model for creating a comment."""

    content: str = Field(..., min_length=1)
    parent_id: UUID | None = None
    page_number: int | None = None
    highlight_id: UUID | None = None
    author_name: str = Field(default="Anonymous", max_length=255)


class CommentUpdateRequest(BaseModel):
    """Request model for updating a comment."""

    content: str = Field(..., min_length=1)


class CommentResponse(BaseModel):
    """Response model for a comment."""

    id: UUID
    document_id: UUID
    parent_id: UUID | None
    page_number: int | None
    highlight_id: UUID | None
    content: str
    author_name: str
    created_at: str
    updated_at: str
    reply_count: int = 0

    model_config = {"from_attributes": True}


class CommentListResponse(BaseModel):
    """Response model for listing comments."""

    comments: list[CommentResponse]
    total: int


def get_comment_repo(session: AsyncSession = Depends(get_db)):
    """Dependency for getting comment repository."""
    from research_agent.infrastructure.database.repositories.sqlalchemy_comment_repo import (
        SQLAlchemyCommentRepository,
    )

    return SQLAlchemyCommentRepository(session)


@router.get("/documents/{document_id}/comments", response_model=CommentListResponse)
async def list_comments(
    document_id: UUID,
    session: AsyncSession = Depends(get_db),
    comment_repo=Depends(get_comment_repo),
    user: UserContext = Depends(get_optional_user),
) -> CommentListResponse:
    """List all top-level comments for a document."""
    # Verify document exists
    document_repo = SQLAlchemyDocumentRepository(session)
    document = await document_repo.find_by_id(document_id)
    if not document:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found")

    comments = await comment_repo.list_by_document(document_id, user_id=user.user_id)
    total = await comment_repo.count_by_document(document_id, user_id=user.user_id)

    response_comments = []
    for c in comments:
        replies = await comment_repo.list_replies(c.id)
        response_comments.append(
            CommentResponse(
                id=c.id,
                document_id=c.document_id,
                parent_id=c.parent_id,
                page_number=c.page_number,
                highlight_id=c.highlight_id,
                content=c.content,
                author_name=c.author_name,
                created_at=c.created_at.isoformat(),
                updated_at=c.updated_at.isoformat(),
                reply_count=len(replies),
            )
        )

    return CommentListResponse(comments=response_comments, total=total)


@router.post("/documents/{document_id}/comments", response_model=CommentResponse, status_code=201)
async def create_comment(
    document_id: UUID,
    request: CommentCreateRequest,
    session: AsyncSession = Depends(get_db),
    comment_repo=Depends(get_comment_repo),
    user: UserContext = Depends(get_optional_user),
) -> CommentResponse:
    """Create a new comment."""
    from uuid import uuid4

    from research_agent.infrastructure.database.models import CommentModel

    # Verify document exists
    document_repo = SQLAlchemyDocumentRepository(session)
    document = await document_repo.find_by_id(document_id)
    if not document:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found")

    # Verify parent exists if provided
    if request.parent_id:
        parent = await comment_repo.find_by_id(request.parent_id)
        if not parent:
            raise HTTPException(
                status_code=404, detail=f"Parent comment {request.parent_id} not found"
            )

    comment = CommentModel(
        id=uuid4(),
        document_id=document_id,
        parent_id=request.parent_id,
        page_number=request.page_number,
        highlight_id=request.highlight_id,
        content=request.content,
        author_name=request.author_name,
        user_id=user.user_id,
    )

    created = await comment_repo.create(comment)
    await session.commit()

    return CommentResponse(
        id=created.id,
        document_id=created.document_id,
        parent_id=created.parent_id,
        page_number=created.page_number,
        highlight_id=created.highlight_id,
        content=created.content,
        author_name=created.author_name,
        created_at=created.created_at.isoformat(),
        updated_at=created.updated_at.isoformat(),
        reply_count=0,
    )


@router.get(
    "/documents/{document_id}/comments/{comment_id}/replies", response_model=list[CommentResponse]
)
async def list_comment_replies(
    document_id: UUID,
    comment_id: UUID,
    session: AsyncSession = Depends(get_db),
    comment_repo=Depends(get_comment_repo),
) -> list[CommentResponse]:
    """List replies to a comment."""
    # Verify document exists
    document_repo = SQLAlchemyDocumentRepository(session)
    document = await document_repo.find_by_id(document_id)
    if not document:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found")

    replies = await comment_repo.list_replies(comment_id)

    return [
        CommentResponse(
            id=r.id,
            document_id=r.document_id,
            parent_id=r.parent_id,
            page_number=r.page_number,
            highlight_id=r.highlight_id,
            content=r.content,
            author_name=r.author_name,
            created_at=r.created_at.isoformat(),
            updated_at=r.updated_at.isoformat(),
            reply_count=0,
        )
        for r in replies
    ]


@router.put("/documents/{document_id}/comments/{comment_id}", response_model=CommentResponse)
async def update_comment(
    document_id: UUID,
    comment_id: UUID,
    request: CommentUpdateRequest,
    session: AsyncSession = Depends(get_db),
    comment_repo=Depends(get_comment_repo),
) -> CommentResponse:
    """Update a comment."""
    # Verify document exists
    document_repo = SQLAlchemyDocumentRepository(session)
    document = await document_repo.find_by_id(document_id)
    if not document:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found")

    comment = await comment_repo.find_by_id(comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail=f"Comment {comment_id} not found")

    comment.content = request.content
    updated = await comment_repo.update(comment)
    await session.commit()

    replies = await comment_repo.list_replies(comment_id)

    return CommentResponse(
        id=updated.id,
        document_id=updated.document_id,
        parent_id=updated.parent_id,
        page_number=updated.page_number,
        highlight_id=updated.highlight_id,
        content=updated.content,
        author_name=updated.author_name,
        created_at=updated.created_at.isoformat(),
        updated_at=updated.updated_at.isoformat(),
        reply_count=len(replies),
    )


@router.delete("/documents/{document_id}/comments/{comment_id}", status_code=204)
async def delete_comment(
    document_id: UUID,
    comment_id: UUID,
    session: AsyncSession = Depends(get_db),
    comment_repo=Depends(get_comment_repo),
) -> None:
    """Delete a comment and all its replies."""
    # Verify document exists
    document_repo = SQLAlchemyDocumentRepository(session)
    document = await document_repo.find_by_id(document_id)
    if not document:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found")

    comment = await comment_repo.find_by_id(comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail=f"Comment {comment_id} not found")

    await comment_repo.delete(comment_id)
    await session.commit()
