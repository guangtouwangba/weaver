"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from research_agent.api.errors import setup_error_handlers
from research_agent.api.middleware import setup_middleware
from research_agent.api.v1.router import api_router
from research_agent.config import get_settings
from research_agent.infrastructure.database.session import init_db
from research_agent.shared.utils.logger import logger

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    # Startup
    logger.info("Starting Research Agent RAG API...")
    await init_db()
    logger.info("Database connection established")
    yield
    # Shutdown
    logger.info("Shutting down Research Agent RAG API...")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="Research Agent RAG API",
        description="AI-powered research assistant with knowledge cards",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Error handlers (must be set up before middleware)
    setup_error_handlers(app)

    # Custom middleware (added first, runs last)
    setup_middleware(app)

    # CORS middleware (added last, runs first - wraps everything)
    # This ensures CORS headers are added even on error responses
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

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
            "name": "Research Agent RAG API",
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

