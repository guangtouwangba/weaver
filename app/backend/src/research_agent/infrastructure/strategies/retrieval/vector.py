"""
Vector Retrieval Strategy.

Standard vector similarity search using PGVector.
"""

from typing import Any, List
from uuid import UUID

from langchain_core.documents import Document

from research_agent.domain.entities.config import RetrievalConfig
from research_agent.domain.strategies.base import IRetrievalStrategy, RetrievalResult
from research_agent.infrastructure.embedding.base import EmbeddingService
from research_agent.infrastructure.vector_store.base import VectorStore
from research_agent.shared.utils.logger import logger


class VectorRetrievalStrategy(IRetrievalStrategy):
    """
    Standard vector similarity search strategy.

    Uses embedding service to convert query to vector,
    then searches PGVector for similar documents.
    """

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store: VectorStore,
    ):
        """
        Initialize vector retrieval strategy.

        Args:
            embedding_service: Service for generating embeddings
            vector_store: Vector store (PGVector or Weaviate)
        """
        self._embedding_service = embedding_service
        self._vector_store = vector_store

    @property
    def name(self) -> str:
        return "vector"

    async def retrieve(
        self,
        query: str,
        project_id: UUID,
        config: RetrievalConfig,
        **kwargs: Any,
    ) -> RetrievalResult:
        """
        Retrieve documents using vector similarity search.

        Args:
            query: Search query
            project_id: Project scope
            config: Retrieval configuration
            **kwargs: Additional parameters (ignored)

        Returns:
            RetrievalResult with matching documents
        """
        logger.info(
            f"[VectorRetrieval] Searching with top_k={config.top_k}, "
            f"min_similarity={config.min_similarity}"
        )

        # Get query embedding
        query_embedding = await self._embedding_service.embed(query)

        # Search vector store
        results = await self._vector_store.search(
            query_embedding=query_embedding,
            project_id=project_id,
            limit=config.top_k,
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
                },
            )
            for result in results
        ]

        logger.info(f"[VectorRetrieval] Retrieved {len(documents)} documents")

        return RetrievalResult(
            documents=documents,
            metadata={
                "query": query,
                "top_k": config.top_k,
                "min_similarity": config.min_similarity,
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
        Rerank documents by similarity score.

        For vector retrieval, documents are already sorted by similarity.
        This implementation just returns them as-is.
        """
        # Documents from vector search are already sorted by similarity
        return documents
