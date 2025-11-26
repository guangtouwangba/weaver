"""Vector store abstract interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List
from uuid import UUID


@dataclass
class SearchResult:
    """Vector search result."""

    chunk_id: UUID
    document_id: UUID
    content: str
    page_number: int
    similarity: float


class VectorStore(ABC):
    """Abstract vector store interface."""

    @abstractmethod
    async def search(
        self,
        query_embedding: List[float],
        project_id: UUID,
        limit: int = 5,
    ) -> List[SearchResult]:
        """Search for similar chunks."""
        pass

