"""Vector store abstract interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
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
        query_embedding: list[float],
        project_id: UUID,
        limit: int = 5,
        document_id: UUID | None = None,
    ) -> list[SearchResult]:
        """Search for similar chunks.

        Args:
            query_embedding: Vector embedding of the query
            project_id: Project UUID to filter by
            limit: Maximum number of results to return
            document_id: Optional document UUID to filter by

        Returns:
            List of SearchResult sorted by similarity
        """
        pass

    async def hybrid_search(
        self,
        query_embedding: list[float],
        query_text: str,
        project_id: UUID,
        limit: int = 5,
        vector_weight: float = 0.7,
        keyword_weight: float = 0.3,
        k: int = 20,
        document_id: UUID | None = None,
    ) -> list[SearchResult]:
        """Hybrid search combining vector similarity and keyword matching.

        Default implementation falls back to vector-only search.
        Subclasses can override to provide true hybrid search.

        Args:
            query_embedding: Vector embedding of the query
            query_text: Original query text for keyword search
            project_id: Project UUID to filter by
            limit: Maximum number of results to return
            vector_weight: Weight for vector search (0-1)
            keyword_weight: Weight for keyword search (0-1)
            k: Number of results to retrieve from each method before fusion
            document_id: Optional document UUID to filter by

        Returns:
            List of SearchResult sorted by fused score
        """
        # Default: fall back to vector-only search
        return await self.search(
            query_embedding=query_embedding,
            project_id=project_id,
            limit=limit,
            document_id=document_id,
        )
