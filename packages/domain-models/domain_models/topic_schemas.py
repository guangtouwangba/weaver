"""Pydantic schemas for Topic API requests and responses."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from domain_models.topic import GoalType, TopicStatus


class TopicCreate(BaseModel):
    """Schema for creating a new topic."""

    name: str = Field(..., min_length=1, max_length=200, description="Topic name")
    goal_type: GoalType = Field(..., description="Learning goal type")
    description: Optional[str] = Field(None, description="Optional topic description")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "量价关系",
                    "goal_type": "practice",
                    "description": "学习量价关系的理论和实战应用"
                }
            ]
        }
    }


class TopicUpdate(BaseModel):
    """Schema for updating an existing topic."""

    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Topic name")
    goal_type: Optional[GoalType] = Field(None, description="Learning goal type")
    description: Optional[str] = Field(None, description="Topic description")
    status: Optional[TopicStatus] = Field(None, description="Topic status")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "量价关系（更新）",
                    "status": "completed"
                }
            ]
        }
    }


class TopicResponse(BaseModel):
    """Schema for topic API response."""

    id: UUID = Field(..., description="Topic UUID")
    name: str = Field(..., description="Topic name")
    goal_type: GoalType = Field(..., description="Learning goal type")
    description: Optional[str] = Field(None, description="Topic description")
    status: TopicStatus = Field(..., description="Topic status")
    completion_progress: float = Field(..., ge=0.0, le=100.0, description="Completion percentage")
    total_contents: int = Field(..., ge=0, description="Total number of contents")
    understood_contents: int = Field(..., ge=0, description="Number of understood contents")
    practiced_contents: int = Field(..., ge=0, description="Number of practiced contents")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            UUID: str,  # Automatically convert UUID to string in JSON
            datetime: lambda v: v.isoformat(),  # ISO format for datetime
        },
        json_schema_extra={
            "examples": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "name": "量价关系",
                    "goal_type": "practice",
                    "description": "学习量价关系的理论和实战应用",
                    "status": "learning",
                    "completion_progress": 45.5,
                    "total_contents": 10,
                    "understood_contents": 8,
                    "practiced_contents": 5,
                    "created_at": "2024-11-03T10:00:00",
                    "updated_at": "2024-11-03T15:30:00"
                }
            ]
        }
    )


class TopicProgressUpdate(BaseModel):
    """Schema for updating topic progress statistics."""

    total_contents: int = Field(..., ge=0, description="Total number of contents")
    understood_contents: int = Field(..., ge=0, description="Number of understood contents")
    practiced_contents: int = Field(..., ge=0, description="Number of practiced contents")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "total_contents": 10,
                    "understood_contents": 8,
                    "practiced_contents": 5
                }
            ]
        }
    }


class TopicListResponse(BaseModel):
    """Schema for listing multiple topics."""

    total: int = Field(..., description="Total number of topics")
    topics: list[TopicResponse] = Field(..., description="List of topics")


class TopicStatistics(BaseModel):
    """Schema for topic statistics."""

    total: int = Field(..., description="Total number of topics")
    learning: int = Field(..., description="Number of topics in learning status")
    completed: int = Field(..., description="Number of completed topics")
    paused: int = Field(..., description="Number of paused topics")
    archived: int = Field(0, description="Number of archived topics")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "total": 15,
                    "learning": 8,
                    "completed": 5,
                    "paused": 2,
                    "archived": 0
                }
            ]
        }
    }

