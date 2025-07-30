"""
Vector service for vector database operations.
"""
import logging
from typing import Dict, Any, List, Optional
from core.exceptions import ServiceError

logger = logging.getLogger(__name__)

class VectorService:
    """Service for vector database operations"""
    
    def __init__(self, vector_store=None):
        self.vector_store = vector_store
    
    def search_similar_papers(self, query: str, limit: int = 10, 
                             similarity_threshold: float = 0.5) -> List[Dict[str, Any]]:
        """Search for similar papers in the vector database"""
        if not self.vector_store:
            raise ServiceError("Vector store not initialized")
        
        try:
            results = self.vector_store.search(
                query=query,
                n_results=limit,
                threshold=similarity_threshold
            )
            return results
        except Exception as e:
            logger.error(f"Error searching similar papers: {e}")
            raise ServiceError(f"Failed to search similar papers: {str(e)}")
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get vector database statistics"""
        if not self.vector_store:
            raise ServiceError("Vector store not initialized")
        
        try:
            return self.vector_store.get_collection_stats()
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            raise ServiceError(f"Failed to get collection stats: {str(e)}")
    
    def add_papers(self, papers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Add papers to the vector database"""
        if not self.vector_store:
            raise ServiceError("Vector store not initialized")
        
        try:
            return self.vector_store.add_papers(papers)
        except Exception as e:
            logger.error(f"Error adding papers to vector store: {e}")
            raise ServiceError(f"Failed to add papers: {str(e)}")
    
    def set_vector_store(self, vector_store):
        """Set the vector store"""
        self.vector_store = vector_store