"""
Research service for handling research-related operations.
"""
import logging
import time
from typing import Dict, Any, Optional
from agents.orchestrator import ResearchOrchestrator
from core.exceptions import ServiceError

logger = logging.getLogger(__name__)

class ResearchService:
    """Service for research operations"""
    
    def __init__(self, orchestrator: Optional[ResearchOrchestrator] = None):
        self.orchestrator = orchestrator
    
    def chat_with_papers(self, 
                        query: str,
                        session_id: Optional[str] = None,
                        max_papers: int = 20,
                        similarity_threshold: float = 0.5,
                        enable_arxiv_fallback: bool = True) -> Dict[str, Any]:
        """
        Process a research query through the orchestrator
        
        Args:
            query: Research question
            session_id: Optional session ID
            max_papers: Maximum papers to analyze
            similarity_threshold: Minimum similarity threshold
            enable_arxiv_fallback: Enable ArXiv fallback search
            
        Returns:
            Dict containing response and metadata
        """
        if not self.orchestrator:
            raise ServiceError("Research orchestrator not initialized")
        
        try:
            start_time = time.time()
            
            # Process the query using the orchestrator
            result = self.orchestrator.chat_with_papers(
                query=query,
                session_id=session_id,
                n_papers=max_papers,
                min_similarity_threshold=similarity_threshold,
                enable_arxiv_fallback=enable_arxiv_fallback
            )
            
            processing_time = int((time.time() - start_time) * 1000)
            
            # Add processing time to result
            result['processing_time_ms'] = processing_time
            
            logger.info(f"Research query processed in {processing_time}ms")
            return result
            
        except Exception as e:
            logger.error(f"Error processing research query: {e}")
            raise ServiceError(f"Failed to process research query: {str(e)}")
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        if not self.orchestrator:
            raise ServiceError("Research orchestrator not initialized")
        
        try:
            stats = self.orchestrator.vector_store.get_collection_stats()
            return {
                "success": True,
                "stats": stats
            }
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            raise ServiceError(f"Failed to get database stats: {str(e)}")
    
    def set_orchestrator(self, orchestrator: ResearchOrchestrator):
        """Set the research orchestrator"""
        self.orchestrator = orchestrator