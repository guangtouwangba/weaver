"""Document DTOs for API requests/responses."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    """Response DTO for a document."""

    id: UUID
    project_id: UUID
    filename: str
    file_size: int
    page_count: int
    status: str
    graph_status: Optional[str] = None
    summary: Optional[str] = None  # Document summary (generated during processing)
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    """Response DTO for document list."""

    items: list[DocumentResponse]
    total: int


class DocumentUploadResponse(BaseModel):
    """Response DTO for document upload."""

    id: UUID
    filename: str
    page_count: int
    status: str
    message: str
    task_id: Optional[UUID] = None  # Async task ID for tracking processing status
