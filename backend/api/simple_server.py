#!/usr/bin/env python3
"""
Simplified FastAPI server for Research Agent RAG System - Without database dependencies
"""

import asyncio
import logging
import os
import sys
import time
from contextlib import asynccontextmanager
from typing import Dict, List, Optional, Any

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Add backend directory to Python path
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
    query: str = Field(..., description="Research query")
    max_papers: int = Field(default=20, ge=1, le=100, description="Maximum papers to retrieve")
    include_recent: bool = Field(default=True, description="Include recent papers")
    session_id: Optional[str] = Field(default=None, description="Session ID for conversation continuity")

class ChatResponse(BaseModel):
    success: bool
    response: str
    relevant_papers: List[Dict[str, Any]]
    agent_discussions: Dict[str, Any]
    session_id: Optional[str]
    search_strategy: str
    expanded_queries: List[str]
    vector_results_count: int
    arxiv_results_count: int
    processing_time_ms: int

class ErrorResponse(BaseModel):
    error: str
    error_type: str
    details: Optional[Dict[str, Any]] = None

class HealthResponse(BaseModel):
    status: str
    message: str
    uptime_seconds: float
    agents_available: List[str]

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Service unavailable - orchestrator not initialized")
    
    uptime = time.time() - getattr(app.state, 'start_time', time.time())
    
    return HealthResponse(
        status="healthy",
        message="Research Agent RAG System is running",
        uptime_seconds=uptime,
        agents_available=list(orchestrator.agents.keys())
    )

# Chat endpoint
@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Main chat endpoint for research queries"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Service unavailable - orchestrator not initialized")
    
    start_time = time.time()
    
    try:
        logger.info(f"Processing chat request: {request.query[:100]}...")
        
        # Call orchestrator
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            orchestrator.research_and_discuss,
            request.query,
            request.max_papers,
            request.include_recent,
            request.session_id
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

# Set start time
@app.on_event("startup")
async def startup_event():
    app.state.start_time = time.time()

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
        "api.simple_server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers,
        log_level="info"
    )

if __name__ == "__main__":
    main()

# Dashboard API endpoints
@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    """Get dashboard statistics"""
    return {
        "total_jobs": 0,
        "active_jobs": 0,
        "completed_runs": 0,
        "failed_runs": 0,
        "papers_processed": 0,
        "success_rate": 0.0
    }

@app.get("/api/health")
async def api_health_check():
    """Health check endpoint with /api prefix"""
    return await health_check()

@app.get("/api/cronjobs")
async def get_cronjobs():
    """Get cronjobs (mock data for now)"""
    return []
