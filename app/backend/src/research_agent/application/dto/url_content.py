"""DTOs for URL content extraction."""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, HttpUrl, field_validator


class URLExtractRequest(BaseModel):
    """Request to extract content from a URL."""

    url: str
    force: bool = False  # Force re-extraction even if cached

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
    title: Optional[str] = None
    content: Optional[str] = None
    thumbnail_url: Optional[str] = None

    # Metadata
    meta_data: Dict[str, Any] = {}

    # Status
    status: str  # pending, processing, completed, failed
    error_message: Optional[str] = None

    # Timestamps
    created_at: datetime
    updated_at: datetime
    extracted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class URLExtractStatusResponse(BaseModel):
    """Lightweight response for polling extraction status."""

    id: UUID
    status: str
    error_message: Optional[str] = None
    title: Optional[str] = None
    thumbnail_url: Optional[str] = None

