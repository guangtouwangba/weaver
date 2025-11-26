"""Documents API endpoints."""

from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
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
from research_agent.shared.exceptions import NotFoundError, PDFProcessingError

router = APIRouter()
settings = get_settings()


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
) -> FileResponse:
    """Get the PDF file for a document."""
    document_repo = SQLAlchemyDocumentRepository(session)
    document = await document_repo.find_by_id(document_id)

    if not document:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found")

    file_path = Path(document.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="PDF file not found on server")

    return FileResponse(
        path=str(file_path),
        filename=document.filename,
        media_type="application/pdf",
    )


@router.delete("/documents/{document_id}", status_code=204)
async def delete_document(
    document_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> None:
    """Delete a document."""
    document_repo = SQLAlchemyDocumentRepository(session)
    chunk_repo = SQLAlchemyChunkRepository(session)
    storage = LocalStorageService(settings.upload_dir)

    use_case = DeleteDocumentUseCase(
        document_repo=document_repo,
        chunk_repo=chunk_repo,
        storage=storage,
    )

    try:
        await use_case.execute(DeleteDocumentInput(document_id=document_id))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
