"""LangChain retriever wrapper for PGVector with hybrid search support."""

from typing import List
from uuid import UUID

from langchain_core.documents import Document as LangChainDocument
from langchain_core.retrievers import BaseRetriever
from langchain_core.callbacks import CallbackManagerForRetrieverRun

from research_agent.infrastructure.embedding.base import EmbeddingService
from research_agent.infrastructure.vector_store.pgvector import PgVectorStore
from research_agent.shared.utils.logger import logger


class PGVectorRetriever(BaseRetriever):
    """LangChain retriever that wraps our PGVector implementation."""
    
    vector_store: PgVectorStore
    embedding_service: EmbeddingService
    project_id: UUID
    k: int = 5
    use_hybrid_search: bool = False  # Enable hybrid search
    vector_weight: float = 0.7
    keyword_weight: float = 0.3
    
    class Config:
        """Pydantic config."""
        arbitrary_types_allowed = True
    
    def _get_relevant_documents(
        self, 
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun | None = None,
    ) -> List[LangChainDocument]:
        """Sync method - not implemented for async-only retriever."""
        raise NotImplementedError("Use async method _aget_relevant_documents")
    
    async def _aget_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun | None = None,
    ) -> List[LangChainDocument]:
        """Retrieve relevant documents for a query using vector or hybrid search."""
        # Get query embedding
        query_embedding = await self.embedding_service.embed(query)
        
        # Choose search method
        if self.use_hybrid_search:
            logger.info("Using hybrid search (vector + keyword)")
            results = await self.vector_store.hybrid_search(
                query_embedding=query_embedding,
                query_text=query,
                project_id=self.project_id,
                limit=self.k,
                vector_weight=self.vector_weight,
                keyword_weight=self.keyword_weight,
                k=self.k * 4,  # Retrieve 4x more results for fusion
            )
        else:
            logger.info("Using vector-only search")
            results = await self.vector_store.search(
                query_embedding=query_embedding,
                project_id=self.project_id,
                limit=self.k,
            )
        
        # Convert to LangChain documents
        return [
            LangChainDocument(
                page_content=result.content,
                metadata={
                    "chunk_id": str(result.chunk_id),
                    "document_id": str(result.document_id),
                    "page_number": result.page_number,
                    "similarity": result.similarity,
                }
            )
            for result in results
        ]


def create_pgvector_retriever(
    vector_store: PgVectorStore,
    embedding_service: EmbeddingService,
    project_id: UUID,
    k: int = 5,
    use_hybrid_search: bool = False,
    vector_weight: float = 0.7,
    keyword_weight: float = 0.3,
) -> PGVectorRetriever:
    """
    Factory function to create a PGVector retriever.
    
    Args:
        vector_store: PGVector store instance
        embedding_service: Embedding service
        project_id: Project UUID
        k: Number of results to return
        use_hybrid_search: Whether to use hybrid search (vector + keyword)
        vector_weight: Weight for vector search in hybrid mode
        keyword_weight: Weight for keyword search in hybrid mode
    """
    return PGVectorRetriever(
        vector_store=vector_store,
        embedding_service=embedding_service,
        project_id=project_id,
        k=k,
        use_hybrid_search=use_hybrid_search,
        vector_weight=vector_weight,
        keyword_weight=keyword_weight,
    )

