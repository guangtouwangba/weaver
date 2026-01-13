"""Chat domain entities."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4


@dataclass
class ChatMessage:
    """
    Chat message entity.

    Attributes:
        project_id: The project this message belongs to
        role: 'user' or 'ai'
        content: The message content
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
    sources: Optional[List[Dict[str, Any]]] = None
    context_refs: Optional[Dict[str, Any]] = None  # {url_ids: [], node_ids: [], nodes: []}
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)
