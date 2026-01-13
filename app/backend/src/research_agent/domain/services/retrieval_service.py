"""Retrieval service for unified resource chunks."""

from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID

from research_agent.config import get_settings
from research_agent.domain.entities.resource import ResourceType
from research_agent.domain.repositories.chunk_repo import ChunkRepository, ChunkSearchResult
from research_agent.infrastructure.embedding.base import EmbeddingService
from research_agent.infrastructure.vector_store.base import SearchResult, VectorStore


@dataclass
class RetrievalConfig:
    """Retrieval configuration."""

    top_k: int | None = None  # If None, will use settings.retrieval_top_k
    min_similarity: float | None = None  # If None, will use settings.retrieval_min_similarity
    use_hybrid_search: bool = False  # Enable hybrid search (vector + keyword)
    vector_weight: float = 0.7  # Weight for vector search in hybrid mode
    keyword_weight: float = 0.3  # Weight for keyword search in hybrid mode

    def __post_init__(self):
        """Initialize from settings if not explicitly provided."""
        settings = get_settings()
        if self.top_k is None:
            self.top_k = settings.retrieval_top_k
        if self.min_similarity is None:
            self.min_similarity = settings.retrieval_min_similarity


class RetrievalService:
    """Service for retrieving relevant resource chunks.
    
    This service supports unified retrieval across all resource types
    (documents, videos, web pages, notes) with optional type filtering.
    """

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
        document_id: UUID | None = None,
        resource_type: Optional[ResourceType] = None,
        resource_id: Optional[UUID] = None,
    ) -> List[SearchResult]:
        """Retrieve relevant chunks for a query.
        
        Args:
            query: Search query text
            project_id: Project to search within
            top_k: Maximum number of results (overrides config)
            document_id: Legacy parameter - filter by document ID
            resource_type: Filter by resource type (document, video, etc.)
            resource_id: Filter by specific resource ID
            
        Returns:
            List of SearchResult sorted by similarity
        """
        # Get query embedding
        query_embedding = await self.embedding_service.embed(query)

        # Use resource_id if provided, otherwise fall back to document_id for compatibility
        effective_resource_id = resource_id or document_id

        # Search vector store
        if self.config.use_hybrid_search:
            results = await self.vector_store.hybrid_search(
                query_embedding=query_embedding,
                query_text=query,
                project_id=project_id,
                limit=top_k or self.config.top_k,
                vector_weight=self.config.vector_weight,
                keyword_weight=self.config.keyword_weight,
                document_id=effective_resource_id,
            )
        else:
            results = await self.vector_store.search(
                query_embedding=query_embedding,
                project_id=project_id,
                limit=top_k or self.config.top_k,
                document_id=effective_resource_id,
            )

        # Filter by minimum similarity if configured, but allow all chunks if scoped to a resource
        # (This supports "Summarize this document" type queries where similarity might be low)
        if self.config.min_similarity > 0 and not effective_resource_id:
            results = [r for r in results if r.similarity >= self.config.min_similarity]

        return results


class UnifiedRetrievalService:
    """Unified retrieval service using ChunkRepository.
    
    This service uses the ChunkRepository interface for retrieval,
    supporting both pgvector and Qdrant backends with unified
    resource chunk storage.
    """

    def __init__(
        self,
        embedding_service: EmbeddingService,
        chunk_repository: ChunkRepository,
        config: RetrievalConfig | None = None,
    ):
        self.embedding_service = embedding_service
        self.chunk_repository = chunk_repository
        self.config = config or RetrievalConfig()

    async def retrieve(
        self,
        query: str,
        project_id: UUID,
        top_k: int | None = None,
        resource_type: Optional[ResourceType] = None,
        resource_id: Optional[UUID] = None,
    ) -> List[ChunkSearchResult]:
        """Retrieve relevant chunks for a query.
        
        Args:
            query: Search query text
            project_id: Project to search within
            top_k: Maximum number of results (overrides config)
            resource_type: Filter by resource type (document, video, etc.)
            resource_id: Filter by specific resource ID
            
        Returns:
            List of ChunkSearchResult sorted by similarity
        """
        # Get query embedding
        query_embedding = await self.embedding_service.embed(query)

        # Search using chunk repository
        if self.config.use_hybrid_search:
            results = await self.chunk_repository.hybrid_search(
                query_embedding=query_embedding,
                query_text=query,
                project_id=project_id,
                limit=top_k or self.config.top_k,
                vector_weight=self.config.vector_weight,
                keyword_weight=self.config.keyword_weight,
                resource_type=resource_type,
                resource_id=resource_id,
            )
        else:
            results = await self.chunk_repository.search(
                query_embedding=query_embedding,
                project_id=project_id,
                limit=top_k or self.config.top_k,
                resource_type=resource_type,
                resource_id=resource_id,
            )

        # Filter by minimum similarity if configured, but allow all chunks if scoped to a resource
        if self.config.min_similarity > 0 and not resource_id:
            results = [r for r in results if r.similarity >= self.config.min_similarity]

        return results

    async def retrieve_by_types(
        self,
        query: str,
        project_id: UUID,
        resource_types: List[ResourceType],
        top_k: int | None = None,
    ) -> List[ChunkSearchResult]:
        """Retrieve chunks from multiple resource types.
        
        Useful for queries like "search in documents and videos".
        
        Args:
            query: Search query text
            project_id: Project to search within
            resource_types: List of resource types to search
            top_k: Maximum number of results per type
            
        Returns:
            Combined list of ChunkSearchResult sorted by similarity
        """
        all_results = []
        per_type_limit = (top_k or self.config.top_k) // len(resource_types) + 1

        for resource_type in resource_types:
            results = await self.retrieve(
                query=query,
                project_id=project_id,
                top_k=per_type_limit,
                resource_type=resource_type,
            )
            all_results.extend(results)

        # Sort by similarity and limit
        all_results.sort(key=lambda r: r.similarity, reverse=True)
        return all_results[: top_k or self.config.top_k]

    def format_context(self, results: List[ChunkSearchResult]) -> str:
        """Format search results as context for LLM.
        
        Args:
            results: List of search results
            
        Returns:
            Formatted context string with source attribution
        """
        if not results:
            return ""

        context_parts = []
        for i, result in enumerate(results, 1):
            context_parts.append(f"[Source {i}] {result.to_context()}")

        return "\n\n".join(context_parts)
