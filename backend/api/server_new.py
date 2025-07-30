"""
FastAPI server for Research Agent RAG System - Refactored with Clean Architecture
"""

import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

# Add backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

from core.config import get_settings
from core.exceptions import ApplicationError
from models.schemas.common import ErrorResponse
from database.database import init_database
from routes.cronjob_routes import router as cronjob_router
from routes.research_routes import router as research_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - initialize and cleanup resources"""
    
    try:
        settings = get_settings()
        
        # Initialize database first
        logger.info("🗄️ Initializing database...")
        settings.validate()
        db_manager = init_database()
        db_manager.create_tables()
        
        # Seed database with initial configurations
        logger.info("🌱 Seeding database configurations...")
        from database.seed_data import seed_database
        seed_database()
        logger.info("✅ Database initialized successfully")
        
        # Initialize the global orchestrator (will be created by dependency injection)
        logger.info("🚀 Research Agent RAG System ready")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize system: {e}")
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

# Include routers
app.include_router(research_router)
app.include_router(cronjob_router)

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

@app.exception_handler(ApplicationError)
async def application_exception_handler(request: Request, exc: ApplicationError):
    """Handle application-specific exceptions"""
    logger.error(f"Application error: {exc.message}")
    status_code = 400 if isinstance(exc, ValueError) else 500
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(
            error=exc.message,
            error_type=type(exc).__name__,
            details={"error_code": exc.error_code} if exc.error_code else None
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
        "api.server_new:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers,
        log_level="info"
    )

if __name__ == "__main__":
    main()