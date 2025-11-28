"""Chat domain entity."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4


@dataclass
class ChatMessage:
    """Chat message entity."""

    project_id: UUID
    role: str  # 'user' or 'ai'
    content: str
    sources: Optional[List[Dict[str, Any]]] = None
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)

