"""Base interface for reranker implementations."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any

from rag_core.core.models import Document


class RerankerInterface(ABC):
    """
    Abstract base class for document rerankers.
    
    Rerankers take a query and a list of retrieved documents and reorder them
    based on their relevance to the query. This is typically more accurate but
    slower than initial retrieval.
    
    Common reranking approaches:
    - Cross-Encoder models: BERT-based models that score query-document pairs
    - LLM-based reranking: Use LLM to score or compare documents
    - Learning-to-rank models: Trained ranking models
    """
    
    @abstractmethod
    async def rerank(
        self,
        query: str,
        documents: List[Document],
        top_n: int | None = None
    ) -> List[Document]:
        """
        Rerank documents based on their relevance to the query.
        
        Args:
            query: The search query
            documents: List of documents to rerank
            top_n: Number of top documents to return (None = return all)
        
        Returns:
            List of documents sorted by relevance score (highest first)
        
        Raises:
            RerankerException: If reranking fails
        """
        pass
    
    @abstractmethod
    def get_config(self) -> Dict[str, Any]:
        """
        Get reranker configuration.
        
        Returns:
            Dictionary containing reranker configuration
        """
        pass

