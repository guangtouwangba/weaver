#!/usr/bin/env python3
"""
FastAPI server for Research Agent RAG System - Optimized for serverless deployment
"""

import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager
from typing import Dict, List, Optional, Any

import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field, validator
from dotenv import load_dotenv

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

from config import Config
from agents.orchestrator import ResearchOrchestrator

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global orchestrator instance (initialized on startup)
orchestrator: Optional[ResearchOrchestrator] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - initialize and cleanup resources"""
    global orchestrator
    
    try:
        # Startup: Initialize orchestrator
        logger.info("🚀 Initializing Research Orchestrator...")
        Config.validate()
        
        orchestrator = ResearchOrchestrator(
            openai_api_key=Config.OPENAI_API_KEY,
            deepseek_api_key=Config.DEEPSEEK_API_KEY,
            anthropic_api_key=Config.ANTHROPIC_API_KEY,
            default_provider=Config.DEFAULT_PROVIDER,
            agent_configs=Config.get_all_agent_configs(),
            db_path=Config.VECTOR_DB_PATH
        )
        
        logger.info("✅ Research Orchestrator initialized successfully")
        logger.info(f"Available agents: {list(orchestrator.agents.keys())}")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize orchestrator: {e}")
        raise
    finally:
        # Cleanup (if needed)
        logger.info("🔄 Cleaning up resources...")

# Create FastAPI app with lifespan management
app = FastAPI(
    title="Research Agent RAG API",
    description="Multi-agent research paper analysis system with iterative discussions",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Request/Response Models
class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    query: str = Field(..., min_length=1, max_length=1000, description="Research question")
    max_papers: Optional[int] = Field(20, ge=1, le=100, description="Maximum papers to analyze")
    similarity_threshold: Optional[float] = Field(0.5, ge=0.0, le=1.0, description="Minimum similarity threshold")
    enable_arxiv_fallback: Optional[bool] = Field(True, description="Enable ArXiv fallback search")
    session_id: Optional[str] = Field(None, description="Optional session ID")

    @validator('query')
    def validate_query(cls, v):
        if not v.strip():
            raise ValueError('Query cannot be empty')
        return v.strip()

class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    success: bool
    response: str
    relevant_papers: List[Dict[str, Any]]
    agent_discussions: Dict[str, Any]
    session_id: Optional[str] = None
    search_strategy: str
    expanded_queries: List[str]
    vector_results_count: int
    arxiv_results_count: int
    processing_time_ms: int

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    uptime_seconds: float
    agents_available: List[str]
    database_status: str

class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = False
    error: str
    error_type: str
    details: Optional[Dict[str, Any]] = None

# Store startup time for uptime calculation
import time
startup_time = time.time()

# API Endpoints
@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint"""
    return {
        "message": "Research Agent RAG API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for load balancers and monitoring"""
    global orchestrator
    
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    try:
        # Check database connectivity
        stats = orchestrator.vector_store.get_collection_stats()
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = f"unhealthy: {str(e)}"
    
    return HealthResponse(
        status="healthy" if db_status == "healthy" else "degraded",
        version="1.0.0",
        uptime_seconds=time.time() - startup_time,
        agents_available=list(orchestrator.agents.keys()) if orchestrator else [],
        database_status=db_status
    )

@app.get("/config", response_model=Dict[str, Any])
async def get_config():
    """Get current system configuration (non-sensitive data)"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    return {
        "default_provider": Config.DEFAULT_PROVIDER,
        "available_agents": list(orchestrator.agents.keys()),
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

@app.post("/chat", response_model=ChatResponse)
async def chat_with_papers(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    req: Request
):
    """
    Main chat endpoint for research paper analysis
    
    This endpoint processes research queries through multi-agent iterative discussion
    and returns comprehensive analysis with Chinese final conclusions.
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    start_time = time.time()
    
    try:
        logger.info(f"Processing chat request: {request.query[:100]}...")
        
        # Process the query using the orchestrator
        result = orchestrator.chat_with_papers(
            query=request.query,
            session_id=request.session_id,
            n_papers=request.max_papers,
            min_similarity_threshold=request.similarity_threshold,
            enable_arxiv_fallback=request.enable_arxiv_fallback
        )
        
        processing_time = int((time.time() - start_time) * 1000)
        
        logger.info(f"Chat request completed in {processing_time}ms")
        
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
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        logger.error(f"Chat request failed after {processing_time}ms: {e}")
        
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error=str(e),
                error_type=type(e).__name__,
                details={"processing_time_ms": processing_time}
            ).dict()
        )

@app.get("/stats", response_model=Dict[str, Any])
async def get_database_stats():
    """Get database statistics"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    try:
        stats = orchestrator.vector_store.get_collection_stats()
        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Failed to get database stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    logger.error(f"HTTP {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            error_type="HTTPException"
        ).dict()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            error_type=type(exc).__name__,
            details={"message": str(exc)}
        ).dict()
    )

# Development server
def main():
    """Run the development server"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Research Agent RAG API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--workers", type=int, default=1, help="Number of workers")
    
    args = parser.parse_args()
    
    logger.info(f"Starting Research Agent RAG API server on {args.host}:{args.port}")
    
    uvicorn.run(
        "api.server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers,
        log_level="info"
    )

if __name__ == "__main__":
    main()