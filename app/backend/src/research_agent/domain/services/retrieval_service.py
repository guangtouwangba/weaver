"""Retrieval service for RAG."""

from dataclasses import dataclass
from typing import List
from uuid import UUID

from research_agent.infrastructure.embedding.base import EmbeddingService
from research_agent.infrastructure.vector_store.base import SearchResult, VectorStore


@dataclass
class RetrievalConfig:
    """Retrieval configuration."""

    top_k: int = 5
    min_similarity: float = 0.0


class RetrievalService:
    """Service for retrieving relevant document chunks."""

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store: VectorStore,
        config: RetrievalConfig | None = None,
    ):
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.config = config or RetrievalConfig()

    async def retrieve(
        self,
        query: str,
        project_id: UUID,
        top_k: int | None = None,
    ) -> List[SearchResult]:
        """Retrieve relevant chunks for a query."""
        # Get query embedding
        query_embedding = await self.embedding_service.embed(query)

        # Search vector store
        results = await self.vector_store.search(
            query_embedding=query_embedding,
            project_id=project_id,
            limit=top_k or self.config.top_k,
        )

        # Filter by minimum similarity if configured
        if self.config.min_similarity > 0:
            results = [r for r in results if r.similarity >= self.config.min_similarity]

        return results

