"""Document chunk domain entity."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4


@dataclass
class DocumentChunk:
    """Document chunk entity - represents a text chunk for RAG."""

    id: UUID = field(default_factory=uuid4)
    document_id: UUID | None = None
    project_id: UUID | None = None
    user_id: str | None = None
    chunk_index: int = 0
    content: str = ""
    page_number: int = 0
    embedding: list[float] | None = None
    metadata: dict[str, Any] | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def set_embedding(self, embedding: list[float]) -> None:
        """Set the embedding vector."""
        self.embedding = embedding

    @property
    def has_embedding(self) -> bool:
        """Check if chunk has embedding."""
        return self.embedding is not None and len(self.embedding) > 0
