"""Chat domain entities."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4


@dataclass
class ChatSession:
    """
    Chat session entity for managing multiple conversations per project.

    Supports both shared sessions (visible to all devices) and private sessions
    (visible only to the user/device that created them).

    Attributes:
        project_id: The project this session belongs to
        title: Session title (editable by user)
        user_id: None for shared sessions, UUID for private sessions
        is_shared: True for shared sessions, False for private sessions
        id: Unique session identifier
        created_at: When the session was created
        updated_at: When the session was last modified
        last_message_at: Timestamp of the last message (for sorting)
    """

    project_id: UUID
    title: str = "New Conversation"
    user_id: Optional[UUID] = None  # None = shared session
    is_shared: bool = True  # True = shared, False = private
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_message_at: Optional[datetime] = None


@dataclass
class ChatMessage:
    """
    Chat message entity.

    Attributes:
        project_id: The project this message belongs to
        role: 'user' or 'ai'
        content: The message content
        session_id: The session this message belongs to (optional for backward compatibility)
        sources: RAG sources referenced in the response (for AI messages)
        context_refs: Context references attached to the message (for user messages)
            - url_ids: List of URL content IDs
            - node_ids: List of canvas node IDs
            - nodes: List of direct node content {id, title, content}
        id: Unique message identifier
        created_at: When the message was created
    """

    project_id: UUID
    role: str  # 'user' or 'ai'
    content: str
    session_id: Optional[UUID] = None
    sources: Optional[List[Dict[str, Any]]] = None
    context_refs: Optional[Dict[str, Any]] = None  # {url_ids: [], node_ids: [], nodes: []}
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)
