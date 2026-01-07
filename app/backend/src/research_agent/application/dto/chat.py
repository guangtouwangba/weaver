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
    session_id: Optional[UUID] = None  # Optional: associate with a session
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


class ChatMessageResponse(BaseModel):
    """Response DTO for chat message."""

    answer: str
    sources: List[SourceReference]
    session_id: Optional[UUID] = None  # The session this message belongs to
    citations: Optional[List[Citation]] = None  # Citations for long context mode
    rag_mode: Optional[str] = None  # "traditional" | "long_context" | "hybrid"
    context_tokens: Optional[int] = None  # Number of tokens used in context


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
    session_id: Optional[UUID] = None
    sources: Optional[List[Dict[str, Any]]] = None
    context_refs: Optional[Dict[str, Any]] = None  # {url_ids: [], node_ids: [], nodes: []}
    created_at: str


class ChatHistoryResponse(BaseModel):
    """Response DTO for chat history."""

    messages: List[HistoryMessage]


# =============================================================================
# Chat Session DTOs
# =============================================================================


class CreateSessionRequest(BaseModel):
    """Request DTO for creating a chat session."""

    title: str = "New Conversation"
    is_shared: bool = True  # True = shared session, False = private session


class UpdateSessionRequest(BaseModel):
    """Request DTO for updating a chat session."""

    title: str


class SessionResponse(BaseModel):
    """Response DTO for a chat session."""

    id: UUID
    project_id: UUID
    title: str
    is_shared: bool
    message_count: int
    created_at: str
    updated_at: str
    last_message_at: Optional[str] = None


class SessionListResponse(BaseModel):
    """Response DTO for listing chat sessions."""

    items: List[SessionResponse]
    total: int
