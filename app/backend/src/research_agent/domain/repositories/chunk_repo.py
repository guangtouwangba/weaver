"""Document chunk repository interface."""

from abc import ABC, abstractmethod
from typing import List
from uuid import UUID

from research_agent.domain.entities.chunk import DocumentChunk


class ChunkRepository(ABC):
    """Abstract chunk repository interface."""

    @abstractmethod
    async def save_batch(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """Save multiple chunks."""
        pass

    @abstractmethod
    async def find_by_document(self, document_id: UUID) -> List[DocumentChunk]:
        """Find all chunks for a document."""
        pass

    @abstractmethod
    async def delete_by_document(self, document_id: UUID) -> int:
        """Delete all chunks for a document. Returns count deleted."""
        pass

