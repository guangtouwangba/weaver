"""
Research controller for handling HTTP request/response logic.
"""
import logging
import time
from typing import Dict, Any, List
from fastapi import HTTPException

from models.schemas.research import ChatRequest, ChatResponse
from models.schemas.common import HealthResponse
from services.research_service import ResearchService
from core.exceptions import ServiceError
from agents.orchestrator import ResearchOrchestrator

logger = logging.getLogger(__name__)

class ResearchController:
    """Controller for research operations"""
    
    def __init__(self, research_service: ResearchService, orchestrator: ResearchOrchestrator = None):
        self.research_service = research_service
        self.orchestrator = orchestrator
        if orchestrator:
            self.research_service.set_orchestrator(orchestrator)
    
    async def chat_with_papers(self, request: ChatRequest) -> ChatResponse:
        """
        Main chat endpoint for research paper analysis
        
        This endpoint processes research queries through multi-agent iterative discussion
        and returns comprehensive analysis.
        """
        try:
            logger.info(f"Processing chat request: {request.query[:100]}...")
            
            result = self.research_service.chat_with_papers(
                query=request.query,
                session_id=request.session_id,
                max_papers=request.max_papers,
                similarity_threshold=request.similarity_threshold,
                enable_arxiv_fallback=request.enable_arxiv_fallback
            )
            
            logger.info(f"Chat request completed in {result.get('processing_time_ms', 0)}ms")
            
            return ChatResponse(
                success=True,
                response=result.get("response", ""),
                relevant_papers=result.get("relevant_papers", []),
                agent_discussions=result.get("agent_discussions", {}),
                session_id=result.get("session_id"),
                search_strategy=result.get("search_strategy", "unknown"),
                expanded_queries=result.get("expanded_queries", []),
                vector_results_count=result.get("vector_results_count", 0),
                arxiv_results_count=result.get("arxiv_results_count", 0),
                processing_time_ms=result.get("processing_time_ms", 0)
            )
            
        except ServiceError as e:
            logger.error(f"Service error in chat request: {e}")
            raise HTTPException(status_code=500, detail=str(e))
        except Exception as e:
            logger.error(f"Unexpected error in chat request: {e}")
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    
    async def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            return self.research_service.get_database_stats()
        except ServiceError as e:
            logger.error(f"Service error getting database stats: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def health_check(self) -> HealthResponse:
        """Health check endpoint for load balancers and monitoring"""
        try:
            if not self.orchestrator:
                raise HTTPException(status_code=503, detail="Orchestrator not initialized")
            
            # Check database connectivity
            try:
                stats = self.orchestrator.vector_store.get_collection_stats()
                db_status = "healthy"
            except Exception as e:
                logger.error(f"Database health check failed: {e}")
                db_status = f"unhealthy: {str(e)}"
            
            # Store startup time for uptime calculation
            startup_time = getattr(self, '_startup_time', time.time())
            if not hasattr(self, '_startup_time'):
                self._startup_time = startup_time
            
            return HealthResponse(
                status="healthy" if db_status == "healthy" else "degraded",
                version="1.0.0",
                uptime_seconds=time.time() - startup_time,
                agents_available=list(self.orchestrator.agents.keys()) if self.orchestrator else [],
                database_status=db_status
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            raise HTTPException(status_code=503, detail=str(e))
    
    async def get_config(self) -> Dict[str, Any]:
        """Get current system configuration (non-sensitive data)"""
        try:
            if not self.orchestrator:
                raise HTTPException(status_code=503, detail="Orchestrator not initialized")
            
            from config import Config
            
            return {
                "default_provider": Config.DEFAULT_PROVIDER,
                "available_agents": list(self.orchestrator.agents.keys()),
                "agent_configs": {
                    name: {
                        "provider": config["provider"],
                        "model": config["model"]
                    }
                    for name, config in Config.get_all_agent_configs().items()
                },
                "vector_db_path": Config.VECTOR_DB_PATH,
                "max_papers_per_query": Config.MAX_PAPERS_PER_QUERY,
                "enable_arxiv_fallback": Config.ENABLE_ARXIV_FALLBACK,
                "enable_query_expansion": Config.ENABLE_QUERY_EXPANSION,
                "enable_agent_discussions": Config.ENABLE_AGENT_DISCUSSIONS
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting config: {e}")
            raise HTTPException(status_code=500, detail=str(e))