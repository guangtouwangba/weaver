"""Curriculum DTOs for API layer."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CurriculumStepDTO(BaseModel):
    """DTO for a single curriculum step."""
    
    id: str
    title: str
    source: str
    source_type: str = Field(alias="sourceType")
    page_range: Optional[str] = Field(None, alias="pageRange")
    duration: int  # in minutes

    class Config:
        populate_by_name = True


class CurriculumResponse(BaseModel):
    """Response DTO for curriculum."""
    
    id: UUID
    project_id: UUID = Field(alias="projectId")
    steps: List[CurriculumStepDTO]
    total_duration: int = Field(alias="totalDuration")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")

    class Config:
        populate_by_name = True


class SaveCurriculumRequest(BaseModel):
    """Request DTO for saving curriculum."""
    
    steps: List[CurriculumStepDTO]

