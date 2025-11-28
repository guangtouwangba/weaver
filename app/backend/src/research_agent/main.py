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
    yield
    # Shutdown
    logger.info("Shutting down Research Agent RAG API...")


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

    # Error handlers (must be set up before middleware)
    setup_error_handlers(app)

    # Custom middleware (added first, runs last)
    setup_middleware(app)

    # CORS middleware (added last, runs first - wraps everything)
    # This ensures CORS headers are added even on error responses
    cors_origins = settings.cors_origins_list
    logger.info(f"CORS origins configured: {cors_origins}")
    logger.info(f"Raw CORS_ORIGINS env: {settings.cors_origins}")
    
    # If no specific origins configured or in production, allow the known domains
    if not cors_origins or cors_origins == ["http://localhost:3000"]:
        cors_origins = [
            "http://localhost:3000",
            "https://research-agent-rag-web-dev.zeabur.app",
            "https://research-agent-rag-frontend-dev.zeabur.app",
        ]
        logger.info(f"Using default CORS origins: {cors_origins}")
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
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

