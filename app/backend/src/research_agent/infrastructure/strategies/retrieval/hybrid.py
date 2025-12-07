"""
Hybrid Retrieval Strategy.

Combines vector similarity search with keyword search for improved recall.
"""

from typing import Any, List
from uuid import UUID

from langchain_core.documents import Document

from research_agent.domain.entities.config import RetrievalConfig
from research_agent.domain.strategies.base import IRetrievalStrategy, RetrievalResult
from research_agent.infrastructure.embedding.base import EmbeddingService
from research_agent.infrastructure.vector_store.pgvector import PgVectorStore
from research_agent.shared.utils.logger import logger


class HybridRetrievalStrategy(IRetrievalStrategy):
    """
    Hybrid retrieval strategy combining vector and keyword search.

    Uses Reciprocal Rank Fusion (RRF) to merge results from both search methods.
    """

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store: PgVectorStore,
        vector_weight: float = 0.7,
        keyword_weight: float = 0.3,
    ):
        """
        Initialize hybrid retrieval strategy.

        Args:
            embedding_service: Service for generating embeddings
            vector_store: PGVector store (must support hybrid_search)
            vector_weight: Weight for vector search results (0-1)
            keyword_weight: Weight for keyword search results (0-1)
        """
        self._embedding_service = embedding_service
        self._vector_store = vector_store
        self._vector_weight = vector_weight
        self._keyword_weight = keyword_weight

    @property
    def name(self) -> str:
        return "hybrid"

    async def retrieve(
        self,
        query: str,
        project_id: UUID,
        config: RetrievalConfig,
        **kwargs: Any,
    ) -> RetrievalResult:
        """
        Retrieve documents using hybrid (vector + keyword) search.

        Args:
            query: Search query
            project_id: Project scope
            config: Retrieval configuration
            **kwargs: Additional parameters
                - vector_weight: Override default vector weight
                - keyword_weight: Override default keyword weight

        Returns:
            RetrievalResult with merged and ranked documents
        """
        vector_weight = kwargs.get("vector_weight", self._vector_weight)
        keyword_weight = kwargs.get("keyword_weight", self._keyword_weight)

        logger.info(
            f"[HybridRetrieval] Searching with top_k={config.top_k}, "
            f"vector_weight={vector_weight}, keyword_weight={keyword_weight}"
        )

        # Get query embedding
        query_embedding = await self._embedding_service.embed(query)

        # Perform hybrid search
        results = await self._vector_store.hybrid_search(
            query_embedding=query_embedding,
            query_text=query,
            project_id=project_id,
            limit=config.top_k,
            vector_weight=vector_weight,
            keyword_weight=keyword_weight,
            k=config.top_k * 4,  # Retrieve more for better fusion
        )

        # Filter by minimum similarity if configured
        if config.min_similarity > 0:
            results = [r for r in results if r.similarity >= config.min_similarity]

        # Convert to LangChain documents
        documents = [
            Document(
                page_content=result.content,
                metadata={
                    "chunk_id": str(result.chunk_id),
                    "document_id": str(result.document_id),
                    "page_number": result.page_number,
                    "similarity": result.similarity,
                    "search_type": "hybrid",
                },
            )
            for result in results
        ]

        logger.info(f"[HybridRetrieval] Retrieved {len(documents)} documents")

        return RetrievalResult(
            documents=documents,
            metadata={
                "query": query,
                "top_k": config.top_k,
                "min_similarity": config.min_similarity,
                "vector_weight": vector_weight,
                "keyword_weight": keyword_weight,
            },
            strategy_name=self.name,
        )

    async def rerank(
        self,
        query: str,
        documents: List[Document],
        config: RetrievalConfig,
        **kwargs: Any,
    ) -> List[Document]:
        """
        Rerank documents.

        Hybrid search results are already ranked by RRF.
        This returns them as-is.
        """
        return documents
