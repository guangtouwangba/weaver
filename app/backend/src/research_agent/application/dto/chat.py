"""Chat DTOs for API requests/responses."""

from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel


class ChatMessageRequest(BaseModel):
    """Request DTO for sending a chat message."""

    message: str
    document_id: Optional[UUID] = None  # Optional: limit to specific document


class SourceReference(BaseModel):
    """Source reference in chat response."""

    document_id: UUID
    page_number: int
    snippet: str
    similarity: float


class ChatMessageResponse(BaseModel):
    """Response DTO for chat message."""

    answer: str
    sources: List[SourceReference]


class StreamChunk(BaseModel):
    """Streaming response chunk."""

    type: str  # "token" | "sources" | "done" | "error"
    content: Optional[str] = None
    sources: Optional[List[SourceReference]] = None


class HistoryMessage(BaseModel):
    """Chat history message DTO."""

    id: UUID
    role: str
    content: str
    sources: Optional[List[Dict[str, Any]]] = None
    created_at: str


class ChatHistoryResponse(BaseModel):
    """Response DTO for chat history."""

    messages: List[HistoryMessage]
