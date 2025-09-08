"""
Vector search domain service.

Handles vector-based search operations.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

from ..value_objects.document_chunk import DocumentChunk


class SearchResult:
    """Search result with score and metadata."""
    
    def __init__(self, chunk: DocumentChunk, score: float, metadata: Optional[Dict[str, Any]] = None):
        self.chunk = chunk
        self.score = score
        self.metadata = metadata or {}


class VectorSearchService(ABC):
    """Abstract domain service for vector search operations."""
    
    @abstractmethod
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for text."""
        pass
    
    @abstractmethod
    async def search_similar_chunks(
        self, 
        query: str, 
        limit: int = 10,
        threshold: float = 0.7,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Search for similar document chunks."""
        pass
    
    @abstractmethod
    async def search_by_embedding(
        self, 
        embedding: List[float], 
        limit: int = 10,
        threshold: float = 0.7,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Search using embedding vector."""
        pass
    
    @abstractmethod
    async def index_chunks(self, chunks: List[DocumentChunk]) -> bool:
        """Index document chunks for search."""
        pass
    
    @abstractmethod
    async def remove_chunks_from_index(self, chunk_ids: List[str]) -> bool:
        """Remove chunks from search index."""
        pass
    
    @abstractmethod
    async def update_chunk_in_index(self, chunk: DocumentChunk) -> bool:
        """Update a chunk in the search index."""
        pass
    
    @abstractmethod
    async def get_index_stats(self) -> Dict[str, Any]:
        """Get search index statistics."""
        pass
    
    @abstractmethod
    async def hybrid_search(
        self, 
        query: str, 
        limit: int = 10,
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.3,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Perform hybrid semantic + keyword search."""
        pass