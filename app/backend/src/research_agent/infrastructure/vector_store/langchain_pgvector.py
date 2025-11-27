"""LangChain retriever wrapper for PGVector."""

from typing import List
from uuid import UUID

from langchain_core.documents import Document as LangChainDocument
from langchain_core.retrievers import BaseRetriever
from langchain_core.callbacks import CallbackManagerForRetrieverRun

from research_agent.infrastructure.embedding.base import EmbeddingService
from research_agent.infrastructure.vector_store.pgvector import PgVectorStore


class PGVectorRetriever(BaseRetriever):
    """LangChain retriever that wraps our PGVector implementation."""
    
    vector_store: PgVectorStore
    embedding_service: EmbeddingService
    project_id: UUID
    k: int = 5
    
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
        """Retrieve relevant documents for a query."""
        # Get query embedding
        query_embedding = await self.embedding_service.embed(query)
        
        # Search vector store
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
) -> PGVectorRetriever:
    """Factory function to create a PGVector retriever."""
    return PGVectorRetriever(
        vector_store=vector_store,
        embedding_service=embedding_service,
        project_id=project_id,
        k=k,
    )

