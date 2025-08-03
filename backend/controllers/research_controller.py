"""
Research controller for handling HTTP request/response logic.
"""
import logging
import time
import uuid
from typing import Dict, Any, List
from fastapi import HTTPException

from models.schemas.research import (
    ChatRequest, ChatResponse, AnalysisRequest, AnalysisResponse,
    QuickAnalysisRequest, QuickAnalysisResponse, AnalysisProgress
)
from models.schemas.common import HealthResponse
from services.research_service import ResearchService
from core.exceptions import ServiceError
from agents.orchestrator import ResearchOrchestrator
from utils.analysis_websocket_manager import analysis_connection_manager
from retrieval.arxiv_client import ArxivClient

logger = logging.getLogger(__name__)

class ResearchController:
    """Controller for research operations"""
    
    def __init__(self, research_service: ResearchService, orchestrator: ResearchOrchestrator = None):
        self.research_service = research_service
        self.orchestrator = orchestrator
        self.active_analyses = {}  # Store active analysis sessions
        self.arxiv_client = ArxivClient(max_results=20, delay=0.5)  # Initialize ArXiv client
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
    
    async def start_analysis(self, request: AnalysisRequest) -> AnalysisResponse:
        """Start a new research analysis with real-time progress tracking"""
        try:
            analysis_id = str(uuid.uuid4())
            logger.info(f"Starting analysis {analysis_id} for query: {request.query[:100]}...")
            
            # Initialize analysis session
            analysis_session = {
                "id": analysis_id,
                "query": request.query,
                "status": "started",
                "progress": 0,
                "current_step": "初始化分析",
                "papers_found": [],
                "agent_insights": {},
                "start_time": time.time(),
                "selected_agents": request.selected_agents or ["paper_analyst", "mit_researcher"],
                "request_params": {
                    "max_papers": request.max_papers,
                    "similarity_threshold": request.similarity_threshold,
                    "enable_arxiv_fallback": request.enable_arxiv_fallback
                }
            }
            
            self.active_analyses[analysis_id] = analysis_session
            
            # Start async analysis task (this would normally be a Celery task)
            # For now, we'll simulate the process
            import asyncio
            asyncio.create_task(self._process_analysis(analysis_id))
            
            return AnalysisResponse(
                analysis_id=analysis_id,
                query=request.query,
                status="started",
                progress=0,
                current_step="分析已启动",
                papers_found=[],
                agent_insights={},
                estimated_completion_time=60  # Estimated 60 seconds
            )
            
        except Exception as e:
            logger.error(f"Error starting analysis: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_analysis_status(self, analysis_id: str) -> AnalysisResponse:
        """Get the current status and progress of an analysis"""
        try:
            if analysis_id not in self.active_analyses:
                raise HTTPException(status_code=404, detail="Analysis not found")
            
            session = self.active_analyses[analysis_id]
            
            return AnalysisResponse(
                analysis_id=analysis_id,
                query=session["query"],
                status=session["status"],
                progress=session["progress"],
                current_step=session["current_step"],
                papers_found=session["papers_found"],
                agent_insights=session["agent_insights"],
                estimated_completion_time=max(0, 60 - int(time.time() - session["start_time"]))
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting analysis status: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def quick_analysis(self, request: QuickAnalysisRequest) -> QuickAnalysisResponse:
        """Perform a quick paper search and relevance analysis"""
        try:
            start_time = time.time()
            logger.info(f"Starting quick analysis for query: {request.query[:100]}...")
            
            papers = []
            relevance_scores = []
            
            # Try vector database first
            try:
                result = self.research_service.search_papers(
                    query=request.query,
                    max_papers=request.max_papers,
                    similarity_threshold=0.3  # Lower threshold for quick results
                )
                
                papers = result.get("papers", [])
                
                # Calculate relevance scores for papers
                for paper in papers:
                    score = paper.get("similarity_score", 0.5)
                    relevance_scores.append(float(score))
                
                logger.info(f"Found {len(papers)} papers from vector database")
                
            except Exception as vector_error:
                logger.warning(f"Vector database search failed: {vector_error}")
                papers = []
            
            # If vector database didn't return enough results, use ArXiv as fallback
            if len(papers) < 3:
                try:
                    logger.info("Using ArXiv fallback for quick analysis")
                    arxiv_papers = await asyncio.to_thread(
                        self.arxiv_client.search_papers, 
                        request.query, 
                        request.max_papers
                    )
                    
                    # Convert ArXiv papers to our format
                    for arxiv_paper in arxiv_papers:
                        paper = {
                            "id": arxiv_paper.id,
                            "title": arxiv_paper.title,
                            "authors": arxiv_paper.authors,
                            "abstract": arxiv_paper.abstract[:500] + "..." if len(arxiv_paper.abstract) > 500 else arxiv_paper.abstract,
                            "published_date": arxiv_paper.published.isoformat() if arxiv_paper.published else None,
                            "arxiv_id": arxiv_paper.arxiv_id,
                            "similarity_score": 0.8,  # Default score for ArXiv results
                            "source": "arxiv",
                            "pdf_url": arxiv_paper.pdf_url,
                            "categories": arxiv_paper.categories
                        }
                        papers.append(paper)
                        relevance_scores.append(0.8)
                    
                    logger.info(f"Added {len(arxiv_papers)} papers from ArXiv fallback")
                    
                except Exception as arxiv_error:
                    logger.error(f"ArXiv fallback also failed: {arxiv_error}")
            
            processing_time = int((time.time() - start_time) * 1000)
            
            logger.info(f"Quick analysis completed in {processing_time}ms, found {len(papers)} papers total")
            
            return QuickAnalysisResponse(
                success=True,
                query=request.query,
                papers=papers,
                relevance_scores=relevance_scores,
                total_found=len(papers),
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            logger.error(f"Unexpected error in quick analysis: {e}")
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    
    async def _process_analysis(self, analysis_id: str):
        """Background task to process the full analysis"""
        try:
            session = self.active_analyses[analysis_id]
            
            # Simulate analysis steps matching the frontend
            steps = [
                {"name": "论文检索", "duration": 3},
                {"name": "AI分析启动", "duration": 2},
                {"name": "内容分析", "duration": 5},
                {"name": "协作讨论", "duration": 4},
                {"name": "生成洞察", "duration": 3}
            ]
            
            import asyncio
            
            for i, step in enumerate(steps):
                session["current_step"] = step["name"]
                session["status"] = "in_progress"
                
                # Send step start update via WebSocket
                await analysis_connection_manager.send_progress_update(
                    analysis_id, step["name"], i * 20, None, session.get("agent_insights", {})
                )
                
                # Simulate step execution with progress updates
                for progress in range(i * 20, (i + 1) * 20, 5):
                    session["progress"] = progress
                    
                    # Send real-time progress updates
                    await analysis_connection_manager.send_progress_update(
                        analysis_id, step["name"], progress, 
                        session.get("papers_found", []), session.get("agent_insights", {})
                    )
                    
                    await asyncio.sleep(step["duration"] / 4)
                
                # Add papers during "论文检索" step - use real ArXiv API
                if step["name"] == "论文检索":
                    try:
                        # Use real ArXiv API to search for papers
                        query = session["query"]
                        max_papers = session["request_params"].get("max_papers", 10)
                        
                        # Search ArXiv for papers
                        logger.info(f"Searching ArXiv for query: {query}")
                        arxiv_papers = await asyncio.to_thread(
                            self.arxiv_client.search_papers, 
                            query, 
                            max_papers
                        )
                        
                        # Convert ArXiv papers to our format
                        papers = []
                        for arxiv_paper in arxiv_papers:
                            paper = {
                                "id": arxiv_paper.id,
                                "title": arxiv_paper.title,
                                "authors": arxiv_paper.authors,
                                "relevance_score": 0.8,  # Default relevance score
                                "summary": arxiv_paper.abstract[:300] + "..." if len(arxiv_paper.abstract) > 300 else arxiv_paper.abstract,
                                "arxiv_id": arxiv_paper.arxiv_id,
                                "pdf_url": arxiv_paper.pdf_url,
                                "published_date": arxiv_paper.published.isoformat() if arxiv_paper.published else None,
                                "categories": arxiv_paper.categories
                            }
                            papers.append(paper)
                        
                        session["papers_found"] = papers
                        logger.info(f"Found {len(papers)} papers from ArXiv")
                        
                        # Send papers found update via WebSocket
                        await analysis_connection_manager.send_papers_found(analysis_id, papers)
                        
                    except Exception as e:
                        logger.error(f"Error retrieving papers from ArXiv: {e}")
                        # Fallback to example papers if ArXiv fails
                        papers = [
                            {
                                "id": "example_1",
                                "title": "示例论文 - ArXiv API暂时不可用",
                                "authors": ["示例作者"],
                                "relevance_score": 0.5,
                                "summary": "ArXiv API暂时不可用，这是一个示例结果。请稍后重试。",
                                "error": "ArXiv API unavailable"
                            }
                        ]
                        session["papers_found"] = papers
                        await analysis_connection_manager.send_papers_found(analysis_id, papers)
                
                # Add agent insights during later steps
                if step["name"] == "协作讨论":
                    session["agent_insights"] = {
                        "mit_researcher": "从学术角度分析，这些论文展示了深度学习的重要进展",
                        "paper_analyst": "论文质量高，方法创新性强，实验验证充分"
                    }
                    
                    # Send agent insights via WebSocket
                    for agent_name, insight in session["agent_insights"].items():
                        await analysis_connection_manager.send_agent_insight(analysis_id, agent_name, insight)
            
            # Complete analysis
            session["status"] = "completed"
            session["progress"] = 100
            session["current_step"] = "分析完成"
            
            # Send completion update via WebSocket
            await analysis_connection_manager.send_analysis_completed(analysis_id, {
                "status": "completed",
                "papers_found": session.get("papers_found", []),
                "agent_insights": session.get("agent_insights", {}),
                "completion_time": time.time()
            })
            
            logger.info(f"Analysis {analysis_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Error processing analysis {analysis_id}: {e}")
            if analysis_id in self.active_analyses:
                self.active_analyses[analysis_id]["status"] = "failed"
                self.active_analyses[analysis_id]["current_step"] = f"分析失败: {str(e)}"
                
                # Send error update via WebSocket
                await analysis_connection_manager.send_error(analysis_id, str(e))