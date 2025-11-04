"""Pydantic schemas for TopicContent API requests and responses."""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from domain_models.topic_content import ContentSource, ContentStatus, ProcessingStatus


class TopicContentCreate(BaseModel):
    """Schema for creating a new topic content."""
    
    title: str = Field(..., min_length=1, max_length=500, description="Content title")
    description: Optional[str] = Field(None, description="Content description")
    source_type: ContentSource = Field(ContentSource.FILE_UPLOAD, description="Content source type")
    source_url: Optional[str] = Field(None, description="Source URL or file path")
    document_id: Optional[str] = Field(None, description="RAG document ID")
    author: Optional[str] = Field(None, max_length=200, description="Author")
    tags: List[str] = Field(default_factory=list, description="Content tags")


class TopicContentUpdate(BaseModel):
    """Schema for updating topic content."""
    
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    status: Optional[ContentStatus] = None
    understanding_level: Optional[int] = Field(None, ge=0, le=100, description="Understanding level 0-100")
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    last_viewed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class TopicContentResponse(BaseModel):
    """Schema for topic content API response."""
    
    id: UUID
    topic_id: UUID
    source_type: ContentSource
    
    # Content info
    title: str
    description: Optional[str]
    source_url: Optional[str]
    document_id: Optional[str]
    
    # Processing status
    processing_status: ProcessingStatus
    processing_error: Optional[str]
    
    # Status
    status: ContentStatus
    understanding_level: int
    
    # Metadata
    author: Optional[str]
    publish_date: Optional[datetime]
    word_count: Optional[int]
    estimated_time: Optional[int]
    
    # User interaction
    notes: Optional[str]
    highlights: List[str]
    tags: List[str]
    
    # Timestamps
    added_at: datetime
    last_viewed_at: Optional[datetime]
    completed_at: Optional[datetime]
    
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            UUID: str,
            datetime: lambda v: v.isoformat(),
        }
    )


class TopicContentListResponse(BaseModel):
    """Schema for listing multiple topic contents."""
    
    total: int
    contents: List[TopicContentResponse]


class TopicContentStats(BaseModel):
    """Schema for content statistics."""
    
    total: int
    pending: int
    reading: int
    understood: int
    questioned: int
    practiced: int
    avg_understanding: float

