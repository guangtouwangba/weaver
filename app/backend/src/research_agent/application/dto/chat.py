"""Chat DTOs for API requests/responses."""

from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel

# =============================================================================
# Chat Message DTOs
# =============================================================================


class ContextNode(BaseModel):
    """Context node from canvas."""

    id: str
    title: str
    content: str


class ChatMessageRequest(BaseModel):
    """Request DTO for sending a chat message."""

    message: str
    document_id: Optional[UUID] = None  # Optional: limit to specific document
    context_node_ids: Optional[List[str]] = (
        None  # Optional: explicit context from canvas nodes (DB lookup)
    )
    context_nodes: Optional[List[ContextNode]] = None  # Optional: explicit context content (direct)
    context_url_ids: Optional[List[str]] = None  # Optional: URL content IDs for video/article context


class SourceReference(BaseModel):
    """Source reference in chat response."""

    document_id: UUID
    page_number: int
    snippet: str
    similarity: float
    char_start: Optional[int] = None  # Character start position for citation
    char_end: Optional[int] = None  # Character end position
    paragraph_index: Optional[int] = None  # Paragraph index
    sentence_index: Optional[int] = None  # Sentence index for precise citation


class Citation(BaseModel):
    """Citation in chat response."""

    document_id: UUID
    page_number: int
    char_start: int
    char_end: int
    paragraph_index: Optional[int] = None
    sentence_index: Optional[int] = None
    snippet: str = ""  # Quoted text snippet


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
    context_refs: Optional[Dict[str, Any]] = None  # {url_ids: [], node_ids: [], nodes: []}
    created_at: str


class ChatHistoryResponse(BaseModel):
    """Response DTO for chat history."""

    messages: List[HistoryMessage]
