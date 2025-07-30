"""
Base vector database interface and factory
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from retrieval.arxiv_client import Paper

@dataclass
class VectorSearchResult:
    """Standardized vector search result"""
    id: str
    document: str
    metadata: Dict[str, Any]
    similarity_score: float

@dataclass 
class VectorDBStats:
    """Vector database statistics"""
    total_documents: int
    unique_papers: int
    provider: str
    collection_name: str
    last_updated: Optional[str] = None

class BaseVectorDB(ABC):
    """Abstract base class for vector database implementations"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.provider = config.get('provider', 'unknown')
        self.collection_name = config.get('collection_name', 'research-papers')
        
    @abstractmethod
    def add_papers(self, papers: List[Paper], embeddings: List[List[float]]) -> List[str]:
        """
        Add papers with their embeddings to the vector database
        
        Args:
            papers: List of Paper objects to add
            embeddings: List of embedding vectors corresponding to papers
            
        Returns:
            List of document IDs that were added
        """
        pass
    
    @abstractmethod
    def add_paper_chunks(self, paper: Paper, chunks: List[str], embeddings: List[List[float]]) -> List[str]:
        """
        Add paper chunks with their embeddings to the vector database
        
        Args:
            paper: Paper object
            chunks: List of text chunks from the paper
            embeddings: List of embedding vectors for each chunk
            
        Returns:
            List of document IDs that were added
        """
        pass
    
    @abstractmethod
    def search_papers(self, query_embedding: List[float], limit: int = 10, 
                     filters: Optional[Dict[str, Any]] = None) -> List[VectorSearchResult]:
        """
        Search for similar papers using vector similarity
        
        Args:
            query_embedding: Query vector
            limit: Maximum number of results to return
            filters: Optional metadata filters
            
        Returns:
            List of VectorSearchResult objects
        """
        pass
    
    @abstractmethod
    def get_paper_by_id(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a paper and all its chunks by paper ID
        
        Args:
            paper_id: Paper ID to retrieve
            
        Returns:
            Paper data with all chunks or None if not found
        """
        pass
    
    @abstractmethod
    def delete_papers(self, paper_ids: List[str]) -> bool:
        """
        Delete papers from the vector database
        
        Args:
            paper_ids: List of paper IDs to delete
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_stats(self) -> VectorDBStats:
        """
        Get database statistics
        
        Returns:
            VectorDBStats object with collection information
        """
        pass
    
    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """
        Check database health and connectivity
        
        Returns:
            Dictionary with health status information
        """
        pass
    
    def paper_exists(self, paper_id: str) -> bool:
        """
        Check if a paper exists in the database
        
        Args:
            paper_id: Paper ID to check
            
        Returns:
            True if paper exists, False otherwise
        """
        return self.get_paper_by_id(paper_id) is not None

class VectorDBFactory:
    """Factory for creating vector database instances"""
    
    _providers = {}
    
    @classmethod
    def register_provider(cls, provider_name: str, provider_class):
        """Register a vector database provider"""
        cls._providers[provider_name] = provider_class
    
    @classmethod
    def create(cls, provider: str, config: Dict[str, Any]) -> BaseVectorDB:
        """
        Create a vector database instance
        
        Args:
            provider: Provider name ('chroma', 'pinecone', 'weaviate', 'qdrant')
            config: Provider-specific configuration
            
        Returns:
            BaseVectorDB instance
            
        Raises:
            ValueError: If provider is not supported
        """
        if provider not in cls._providers:
            raise ValueError(f"Unsupported vector database provider: {provider}. "
                           f"Available providers: {list(cls._providers.keys())}")
        
        provider_class = cls._providers[provider]
        return provider_class(config)
    
    @classmethod
    def get_available_providers(cls) -> List[str]:
        """Get list of available providers"""
        return list(cls._providers.keys())