"""DTOs for URL content extraction."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, field_validator


class URLExtractRequest(BaseModel):
    """Request to extract content from a URL."""

    url: str
    force: bool = False  # Force re-extraction even if cached
    project_id: UUID | None = None  # Associate with a project for persistence

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL format."""
        if not v:
            raise ValueError("URL is required")
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        if len(v) > 2048:
            raise ValueError("URL is too long (max 2048 characters)")
        return v.strip()


class URLExtractResponse(BaseModel):
    """Response containing extracted URL content."""

    id: UUID
    url: str
    normalized_url: str
    platform: str  # youtube, bilibili, douyin, web
    content_type: str  # video, article, link

    # Extracted content
    title: str | None = None
    content: str | None = None
    thumbnail_url: str | None = None

    # Metadata
    meta_data: dict[str, Any] = {}

    # Status
    status: str  # pending, processing, completed, failed
    error_message: str | None = None

    # Timestamps
    created_at: datetime
    updated_at: datetime
    extracted_at: datetime | None = None

    # Project association
    project_id: UUID | None = None

    class Config:
        from_attributes = True


class URLContentListResponse(BaseModel):
    """Response for listing URL contents."""

    items: list["URLExtractResponse"]
    total: int


class URLExtractStatusResponse(BaseModel):
    """Lightweight response for polling extraction status."""

    id: UUID
    status: str
    error_message: str | None = None
    title: str | None = None
    thumbnail_url: str | None = None

