"""Chat DTOs for API requests/responses."""

from typing import Any
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
    document_id: UUID | None = None  # Optional: limit to specific document
    context_node_ids: list[str] | None = (
        None  # Optional: explicit context from canvas nodes (DB lookup)
    )
    context_nodes: list[ContextNode] | None = None  # Optional: explicit context content (direct)
    context_url_ids: list[str] | None = None  # Optional: URL content IDs for video/article context


class SourceReference(BaseModel):
    """Source reference in chat response."""

    document_id: UUID
    page_number: int
    snippet: str
    similarity: float
    char_start: int | None = None  # Character start position for citation
    char_end: int | None = None  # Character end position
    paragraph_index: int | None = None  # Paragraph index
    sentence_index: int | None = None  # Sentence index for precise citation


class Citation(BaseModel):
    """Citation in chat response."""

    document_id: UUID
    page_number: int
    char_start: int
    char_end: int
    paragraph_index: int | None = None
    sentence_index: int | None = None
    snippet: str = ""  # Quoted text snippet


class StreamChunk(BaseModel):
    """Streaming response chunk."""

    type: str  # "token" | "sources" | "done" | "error"
    content: str | None = None
    sources: list[SourceReference] | None = None


class HistoryMessage(BaseModel):
    """Chat history message DTO."""

    id: UUID
    role: str
    content: str
    sources: list[dict[str, Any]] | None = None
    context_refs: dict[str, Any] | None = None  # {url_ids: [], node_ids: [], nodes: []}
    created_at: str


class ChatHistoryResponse(BaseModel):
    """Response DTO for chat history."""

    messages: list[HistoryMessage]
