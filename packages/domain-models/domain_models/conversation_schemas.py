"""Pydantic schemas for Conversation and Message API."""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


# ============ Conversation Schemas ============

class ConversationCreate(BaseModel):
    """Schema for creating a new conversation."""
    
    topic_id: UUID = Field(..., description="Topic UUID")
    title: Optional[str] = Field(None, max_length=200, description="Conversation title")


class ConversationUpdate(BaseModel):
    """Schema for updating a conversation."""
    
    title: Optional[str] = Field(None, max_length=200, description="Conversation title")


class ConversationResponse(BaseModel):
    """Schema for conversation API response."""
    
    id: UUID
    topic_id: UUID
    title: Optional[str]
    message_count: int
    created_at: datetime
    updated_at: datetime
    last_message_at: Optional[datetime]
    
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            UUID: str,
            datetime: lambda v: v.isoformat(),
        }
    )


class ConversationListResponse(BaseModel):
    """Schema for listing multiple conversations."""
    
    total: int
    conversations: List[ConversationResponse]


# ============ Message Schemas ============

class MessageCreate(BaseModel):
    """Schema for creating a new message."""
    
    conversation_id: UUID = Field(..., description="Conversation UUID")
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., min_length=1, description="Message content")
    sources: Optional[List[dict]] = Field(None, description="Source documents (for assistant messages)")


class MessageResponse(BaseModel):
    """Schema for message API response."""
    
    id: UUID
    conversation_id: UUID
    role: str
    content: str
    sources: Optional[List[str]]  # Simplified for basic version
    created_at: datetime
    
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            UUID: str,
            datetime: lambda v: v.isoformat(),
        }
    )


class MessageListResponse(BaseModel):
    """Schema for listing multiple messages."""
    
    total: int
    messages: List[MessageResponse]

