"""FastAPI application entry point."""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from research_agent.api.errors import setup_error_handlers
from research_agent.api.middleware import setup_middleware
from research_agent.api.v1.router import api_router
from research_agent.config import get_settings
from research_agent.domain.entities.task import TaskType
from research_agent.infrastructure.database.session import init_db, get_async_session_factory
from research_agent.shared.utils.logger import logger
from research_agent.worker.dispatcher import TaskDispatcher
from research_agent.worker.tasks import DocumentProcessorTask, GraphExtractorTask, CanvasSyncerTask
from research_agent.worker.worker import BackgroundWorker

settings = get_settings()

# Global worker instance
_background_worker: Optional[BackgroundWorker] = None


def create_task_dispatcher() -> TaskDispatcher:
    """Create and configure the task dispatcher."""
    dispatcher = TaskDispatcher()
    
    # Register task handlers
    dispatcher.register(TaskType.PROCESS_DOCUMENT, DocumentProcessorTask)
    dispatcher.register(TaskType.EXTRACT_GRAPH, GraphExtractorTask)
    dispatcher.register(TaskType.SYNC_CANVAS, CanvasSyncerTask)
    
    return dispatcher


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    global _background_worker
    
    # Startup
    logger.info("Starting Research Agent RAG API...")
    
    # Debug: Check API key configuration
    openrouter_key = settings.openrouter_api_key
    
    if openrouter_key:
        masked = openrouter_key[:10] + "..." + openrouter_key[-4:] if len(openrouter_key) > 14 else "***"
        logger.info(f"OpenRouter API Key: {masked}")
        logger.info(f"LLM Model: {settings.llm_model}")
        logger.info(f"Embedding Model: {settings.embedding_model}")
    else:
        logger.warning("⚠️  OPENROUTER_API_KEY not set!")
        logger.warning("   Get one at: https://openrouter.ai/keys")
    
    await init_db()
    logger.info("Database connection established")
    
    # Start background worker
    try:
        session_factory = get_async_session_factory()
        dispatcher = create_task_dispatcher()
        
        _background_worker = BackgroundWorker(
            dispatcher=dispatcher,
            session_factory=session_factory,
            poll_interval=2.0,
            max_concurrent_tasks=3,
        )
        
        # Start worker in background
        asyncio.create_task(_background_worker.start())
        logger.info("Background worker started")
    except Exception as e:
        logger.error(f"Failed to start background worker: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Research Agent RAG API...")
    
    # Stop background worker
    if _background_worker:
        await _background_worker.stop()
        logger.info("Background worker stopped")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="Weaver API",
        description="Weave knowledge into insights. AI-powered research workspace with infinite canvas.",
        version="0.1.0",
        lifespan=lifespan,
        docs_url=None,  # Disable default docs, we'll add custom ones
        redoc_url=None,  # Disable default redoc
    )
    
    # Custom Swagger UI with reliable CDN
    from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
    
    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        return get_swagger_ui_html(
            openapi_url="/openapi.json",
            title=app.title + " - Swagger UI",
            swagger_js_url="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js",
            swagger_css_url="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css",
        )
    
    @app.get("/redoc", include_in_schema=False)
    async def custom_redoc_html():
        return get_redoc_html(
            openapi_url="/openapi.json",
            title=app.title + " - ReDoc",
            redoc_js_url="https://unpkg.com/redoc@next/bundles/redoc.standalone.js",
    )

    # CORS middleware - MUST be added FIRST so it wraps everything
    # and can handle preflight requests before other middleware runs
    cors_origins = settings.cors_origins_list
    logger.info(f"CORS origins from settings: {cors_origins}")
    logger.info(f"Raw CORS_ORIGINS env: {settings.cors_origins}")
    
    # Build comprehensive list of allowed origins
    allowed_origins = set(cors_origins) if cors_origins else set()
    
    # Always add known Zeabur domains for this project
    zeabur_origins = [
        "https://research-agent-rag-web-dev.zeabur.app",
        "https://research-agent-rag-frontend-dev.zeabur.app",
        "http://localhost:3000",
        "http://localhost:3001",
    ]
    allowed_origins.update(zeabur_origins)
    
    # Convert to list and log
    cors_origins_final = list(allowed_origins)
    logger.info(f"Final CORS allowed origins: {cors_origins_final}")
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins_final,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"],
        allow_headers=["*"],
        expose_headers=["*"],
        max_age=86400,  # Cache preflight for 24 hours
    )

    # Error handlers (must be set up before other middleware)
    setup_error_handlers(app)

    # Custom middleware (logging, etc.)
    setup_middleware(app)

    # Include API router
    app.include_router(api_router, prefix="/api/v1")

    # Health check endpoint
    @app.get("/health", tags=["health"])
    async def health_check() -> dict:
        """Health check endpoint."""
        return {
            "status": "healthy",
            "environment": settings.environment,
            "version": "0.1.0",
        }

    # Root endpoint
    @app.get("/", tags=["root"])
    async def root() -> dict:
        """Root endpoint with API info."""
        return {
            "name": "Weaver API",
            "version": "0.1.0",
            "docs": "/docs",
            "health": "/health",
        }

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "research_agent.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_development,
    )

