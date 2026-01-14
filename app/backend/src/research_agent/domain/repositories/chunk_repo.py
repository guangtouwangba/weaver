"""Chunk repository interface for unified resource chunks."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from research_agent.domain.entities.resource import ResourceType
from research_agent.domain.entities.resource_chunk import ResourceChunk


@dataclass
class ChunkSearchResult:
    """Search result from chunk repository."""

    chunk_id: UUID
    resource_id: UUID
    resource_type: ResourceType
    content: str
    similarity: float
    metadata: dict[str, Any]

    def to_context(self) -> str:
        """Format result for LLM context with source attribution."""
        source_info = f"[{self.resource_type.value}] {self.metadata.get('title', 'Untitled')}"

        if self.resource_type == ResourceType.DOCUMENT:
            page = self.metadata.get("page_number")
            if page:
                source_info += f" (Page {page})"
        elif self.resource_type in (ResourceType.VIDEO, ResourceType.AUDIO):
            start_time = self.metadata.get("start_time")
            if start_time is not None:
                minutes = int(start_time // 60)
                seconds = int(start_time % 60)
                source_info += f" ({minutes}:{seconds:02d})"

        return f"{source_info}\n{self.content}"


class ChunkRepository(ABC):
    """Abstract chunk repository interface for unified resource chunks.

    This interface supports both legacy DocumentChunk operations and new
    ResourceChunk operations for unified storage and retrieval.
    """

    # =========================================================================
    # ResourceChunk operations (new unified interface)
    # =========================================================================

    @abstractmethod
    async def save_batch(self, chunks: list[ResourceChunk]) -> list[ResourceChunk]:
        """Save multiple resource chunks.

        Args:
            chunks: List of ResourceChunk entities to save

        Returns:
            List of saved ResourceChunk entities
        """
        pass

    @abstractmethod
    async def find_by_resource(self, resource_id: UUID) -> list[ResourceChunk]:
        """Find all chunks for a resource.

        Args:
            resource_id: UUID of the parent resource

        Returns:
            List of ResourceChunk entities ordered by chunk_index
        """
        pass

    @abstractmethod
    async def delete_by_resource(self, resource_id: UUID) -> int:
        """Delete all chunks for a resource.

        Args:
            resource_id: UUID of the parent resource

        Returns:
            Number of chunks deleted
        """
        pass

    @abstractmethod
    async def search(
        self,
        query_embedding: list[float],
        project_id: UUID,
        limit: int = 5,
        resource_type: ResourceType | None = None,
        resource_id: UUID | None = None,
    ) -> list[ChunkSearchResult]:
        """Search for similar chunks using vector similarity.

        Args:
            query_embedding: Vector embedding of the query
            project_id: Project UUID to filter by
            limit: Maximum number of results to return
            resource_type: Optional filter by resource type
            resource_id: Optional filter by specific resource

        Returns:
            List of ChunkSearchResult sorted by similarity (descending)
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
        resource_type: ResourceType | None = None,
        resource_id: UUID | None = None,
    ) -> list[ChunkSearchResult]:
        """Hybrid search combining vector similarity and keyword matching.

        Default implementation falls back to vector-only search.
        Subclasses can override to provide true hybrid search with RRF fusion.

        Args:
            query_embedding: Vector embedding of the query
            query_text: Original query text for keyword search
            project_id: Project UUID to filter by
            limit: Maximum number of results to return
            vector_weight: Weight for vector search (0-1)
            keyword_weight: Weight for keyword search (0-1)
            resource_type: Optional filter by resource type
            resource_id: Optional filter by specific resource

        Returns:
            List of ChunkSearchResult sorted by fused score
        """
        # Default: fall back to vector-only search
        return await self.search(
            query_embedding=query_embedding,
            project_id=project_id,
            limit=limit,
            resource_type=resource_type,
            resource_id=resource_id,
        )

    # =========================================================================
    # Legacy DocumentChunk operations (for backward compatibility)
    # =========================================================================

    async def find_by_document(self, document_id: UUID) -> list[ResourceChunk]:
        """Find all chunks for a document (legacy compatibility).

        This is an alias for find_by_resource for backward compatibility.
        """
        return await self.find_by_resource(document_id)

    async def delete_by_document(self, document_id: UUID) -> int:
        """Delete all chunks for a document (legacy compatibility).

        This is an alias for delete_by_resource for backward compatibility.
        """
        return await self.delete_by_resource(document_id)
