"""Application entrypoint for the minimal LangChain/LangGraph RAG service."""

import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Configure logging at module level
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("="  * 80)
logger.info("📦 Loading apps.api.app module...")
logger.info("="  * 80)

from apps.api.app.lifecycle import lifespan

logger.info("✅ Lifespan imported successfully")
from apps.api.app.routers import (
    ingest,
    qa,
    qa_stream,
    search,
    topics,
    topic_contents,
    conversations,
    messages,
    health,
    evaluation,
)
from apps.api.app.errors import (
    AppException,
    app_exception_handler,
    http_exception_handler,
    general_exception_handler,
)


def create_app() -> FastAPI:
    """
    Configure FastAPI with core routers and shared metadata.
    
    Includes:
    - Lifespan management for component initialization/cleanup
    - Health check endpoints
    - Business logic routers
    - Error handlers
    - CORS middleware
    """
    logger.info("🏗️  Creating FastAPI app with lifespan management...")
    logger.info(f"   Lifespan function: {lifespan}")
    
    app = FastAPI(
        title="Knowledge Platform RAG Service",
        version="0.3.0",
        description=(
            "API surface for topic management, content management, document ingest, semantic search, and QA "
            "built on LangChain + LangGraph with PostgreSQL for knowledge management. "
            "Includes comprehensive health checks and lifecycle management."
        ),
        lifespan=lifespan,  # 🔥 Add lifecycle management
    )
    
    logger.info(f"✅ FastAPI app created with lifespan: {app.router.lifespan_context if hasattr(app.router, 'lifespan_context') else 'NO LIFESPAN CONTEXT'}")
    
    # Register exception handlers
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)

    # Configure CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",  # Vite dev server default port
            "http://localhost:5174",  # Vite alternate port
            "http://localhost:3000",  # Alternative React port
            "http://127.0.0.1:5173",
            "http://127.0.0.1:5174",
            "http://127.0.0.1:3000",
        ],
        allow_credentials=True,
        allow_methods=["*"],  # Allow all HTTP methods
        allow_headers=["*"],  # Allow all headers
    )

    # Health check endpoints (no prefix for Kubernetes probes)
    app.include_router(health.router)

    # Topic management
    app.include_router(topics.router, prefix="/api/v1")
    
    # Topic content management
    app.include_router(topic_contents.router, prefix="/api/v1")
    
    # Conversation and message management
    app.include_router(conversations.router, prefix="/api/v1")
    app.include_router(messages.router, prefix="/api/v1")

    # Document and RAG operations
    app.include_router(ingest.router, prefix="/api/v1")
    app.include_router(search.router, prefix="/api/v1")
    app.include_router(qa.router, prefix="/api/v1")
    app.include_router(qa_stream.router, prefix="/api/v1")  # Streaming QA endpoint
    
    # Runtime evaluation endpoints
    app.include_router(evaluation.router, prefix="/api/v1")

    return app


logger.info("🚀 Calling create_app() to initialize application...")
app = create_app()
logger.info(f"✅ Application instance created: {app.title}")
logger.info("="  * 80)
