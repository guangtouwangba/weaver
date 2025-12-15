"""FastAPI application entry point."""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from research_agent.api.errors import setup_error_handlers
from research_agent.api.middleware import setup_middleware
from research_agent.api.v1.router import api_router
from research_agent.api.v1.websocket import router as websocket_router
from research_agent.config import get_settings
from research_agent.domain.entities.task import TaskType
from research_agent.infrastructure.database.session import (
    close_db,
    get_async_session_factory,
    get_pool_status,
    init_db,
)
from research_agent.shared.utils.logger import logger
from research_agent.worker.dispatcher import TaskDispatcher
from research_agent.worker.tasks import (
    CanvasCleanupTask,
    CanvasSyncerTask,
    DocumentProcessorTask,
    GraphExtractorTask,
)
from research_agent.worker.tasks.file_cleanup import FileCleanupTask
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
    dispatcher.register(TaskType.CLEANUP_CANVAS, CanvasCleanupTask)
    dispatcher.register(TaskType.FILE_CLEANUP, FileCleanupTask)

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
        masked = (
            openrouter_key[:10] + "..." + openrouter_key[-4:] if len(openrouter_key) > 14 else "***"
        )
        logger.info(f"OpenRouter API Key: {masked}")
        logger.info(f"LLM Model: {settings.llm_model}")
        logger.info(f"Embedding Model: {settings.embedding_model}")
    else:
        logger.warning("⚠️  OPENROUTER_API_KEY not set!")
        logger.warning("   Get one at: https://openrouter.ai/keys")

    # Log RAG mode configuration
    logger.info("=" * 60)
    logger.info("RAG Mode Configuration:")
    logger.info(f"  Mode: {settings.rag_mode}")
    if settings.rag_mode in ("long_context", "auto"):
        from research_agent.infrastructure.llm.model_config import (
            calculate_available_tokens,
            get_model_context_window,
        )

        context_window = get_model_context_window(settings.llm_model)
        available_tokens = calculate_available_tokens(
            settings.llm_model, settings.long_context_safety_ratio
        )
        logger.info(f"  Long Context Settings:")
        logger.info(
            f"    - Safety Ratio: {settings.long_context_safety_ratio} ({settings.long_context_safety_ratio * 100}% of context window)"
        )
        logger.info(f"    - Min Tokens: {settings.long_context_min_tokens:,}")
        logger.info(f"    - Model Context Window: {context_window:,} tokens")
        logger.info(f"    - Available Tokens: {available_tokens:,} tokens")
        logger.info(
            f"    - Citation Grounding: {'✅ Enabled' if settings.enable_citation_grounding else '❌ Disabled'}"
        )
        logger.info(f"    - Citation Format: {settings.citation_format}")
    logger.info("=" * 60)

    # Initialize database - will not raise on failure, app will start anyway
    try:
        await init_db()
        logger.info("Database initialization completed")
    except Exception as e:
        logger.warning(f"⚠️  Database initialization warning: {e}")
        logger.warning("   Application will continue - database connections will be retried on demand")

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
        worker_task = asyncio.create_task(_background_worker.start())
        # Add error callback to catch any unhandled exceptions
        def worker_error_handler(task):
            try:
                task.result()
            except Exception as e:
                logger.error(f"❌ Background worker crashed: {e}", exc_info=True)
        
        worker_task.add_done_callback(worker_error_handler)
        logger.info("✅ Background worker task created and started")
    except Exception as e:
        logger.error(f"❌ Failed to start background worker: {e}", exc_info=True)

    yield

    # Shutdown
    logger.info("Shutting down Research Agent RAG API...")

    # Stop background worker
    if _background_worker:
        try:
            await asyncio.wait_for(_background_worker.stop(), timeout=30.0)
            logger.info("Background worker stopped")
        except asyncio.TimeoutError:
            logger.warning("Background worker stop timed out")
        except Exception as e:
            logger.warning(f"Error stopping background worker: {e}")

    # Close database connections gracefully
    try:
        await asyncio.wait_for(close_db(), timeout=10.0)
    except asyncio.TimeoutError:
        logger.warning("Database close timed out during shutdown")
    except Exception as e:
        logger.warning(f"Error during database close: {e}")


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
    from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html

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

    # Include WebSocket router at root level (no /api/v1 prefix)
    # This allows WebSocket connections at /ws/projects/{project_id}/...
    app.include_router(websocket_router, tags=["websocket"])

    # Health check endpoint
    @app.get("/health", tags=["health"])
    async def health_check() -> dict:
        """Health check endpoint."""
        return {
            "status": "healthy",
            "environment": settings.environment,
            "version": "0.1.0",
        }

    # Database connection pool health endpoint
    @app.get("/health/pool", tags=["health"])
    async def pool_health() -> dict:
        """
        Database connection pool status endpoint.

        Returns pool statistics for monitoring:
        - checkedout: Connections currently in use
        - checkedin: Available connections in pool
        - overflow: Current overflow connections
        - total_max: Maximum total connections
        - usage_ratio: Current usage (0.0 - 1.0)
        - status: "healthy" | "warning" | "critical"
        """
        try:
            status = get_pool_status()
            usage_ratio = status["usage_ratio"]

            # Determine health status based on usage
            if usage_ratio >= 0.9:
                health_status = "critical"
            elif usage_ratio >= 0.8:
                health_status = "warning"
            else:
                health_status = "healthy"

            return {
                "status": health_status,
                "pool": {
                    "checkedout": status["checkedout"],
                    "checkedin": status["checkedin"],
                    "overflow": status["overflow"],
                    "max_overflow": status["max_overflow"],
                    "total_max": status["total_max"],
                    "usage_ratio": round(usage_ratio, 3),
                    "usage_percent": f"{usage_ratio * 100:.1f}%",
                },
            }
        except Exception as e:
            logger.error(f"Failed to get pool status: {e}")
            return {
                "status": "error",
                "error": str(e),
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
