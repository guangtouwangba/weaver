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
    
    def search_papers(self, 
                     query: str,
                     max_papers: int = 10,
                     similarity_threshold: float = 0.3) -> Dict[str, Any]:
        """
        Search for papers without full analysis - used for quick results
        
        Args:
            query: Search query
            max_papers: Maximum papers to return
            similarity_threshold: Minimum similarity threshold
            
        Returns:
            Dict containing papers and metadata
        """
        if not self.orchestrator:
            raise ServiceError("Research orchestrator not initialized")
        
        try:
            start_time = time.time()
            
            # Use the vector store directly for quick search
            results = self.orchestrator.vector_store.search(
                query=query,
                n_results=max_papers,
                min_similarity_threshold=similarity_threshold
            )
            
            # Format papers for response
            papers = []
            for i, (doc, metadata, score) in enumerate(zip(
                results.get('documents', []),
                results.get('metadatas', []),
                results.get('distances', [])
            )):
                # Convert distance to similarity (assuming cosine distance)
                similarity_score = 1.0 - score if score is not None else 0.5
                
                paper = {
                    "id": metadata.get('paper_id', f'paper_{i}'),
                    "title": metadata.get('title', 'Unknown Title'),
                    "authors": metadata.get('authors', []),
                    "abstract": doc[:500] + "..." if len(doc) > 500 else doc,
                    "published_date": metadata.get('published_date', ''),
                    "arxiv_id": metadata.get('arxiv_id', ''),
                    "similarity_score": similarity_score,
                    "source": metadata.get('source', 'vector_db')
                }
                papers.append(paper)
            
            processing_time = int((time.time() - start_time) * 1000)
            
            return {
                "papers": papers,
                "total_found": len(papers),
                "processing_time_ms": processing_time,
                "search_strategy": "vector_search"
            }
            
        except Exception as e:
            logger.error(f"Error searching papers: {e}")
            raise ServiceError(f"Failed to search papers: {str(e)}")