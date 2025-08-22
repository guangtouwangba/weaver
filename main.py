"""
RAG Knowledge Management System - Main Application

A modern RAG system with clean architecture based on Service layer orchestration.
Architecture: Schema + Repository + Service + API
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.exceptions import RequestValidationError

from config.settings import AppConfig
from config.docs import SWAGGER_UI_PARAMETERS
from modules.api import api_router
from modules.database import DatabaseConnection
from modules.schemas import APIResponse, HealthCheckResponse
from modules.api.error_handlers import (
    unicode_decode_error_handler,
    request_validation_error_handler,
    general_exception_handler,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Application metadata
APP_METADATA = {
    "title": "RAG Knowledge Management API",
    "description": """
🔍 **RAG Knowledge Management System**

## Features
- 📚 Document processing (PDF, Word, TXT)
- 🏷️ Topic organization and classification  
- ⚡ Semantic search and retrieval
- 🔧 Clean service-oriented architecture

## Quick Start
1. Health check: `GET /health`
2. Create topic: `POST /api/v1/topics`
3. Upload file: `POST /api/v1/files/upload/signed-url`
4. Search content: `POST /api/v1/documents/search`
    """,
    "version": "2.0.0",
    "contact": {
        "name": "RAG API Support",
        "url": "https://github.com/your-repo/research-agent-rag",
        "email": "support@example.com",
    },
    "license_info": {"name": "MIT", "url": "https://opensource.org/licenses/MIT"},
}

# Create FastAPI application
app = FastAPI(**APP_METADATA)

# Register error handlers
app.add_exception_handler(UnicodeDecodeError, unicode_decode_error_handler)
app.add_exception_handler(RequestValidationError, request_validation_error_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routes
app.include_router(api_router, prefix="/api/v1")


# Documentation routes
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """Custom Swagger UI page with additional styles and features"""
    from fastapi.openapi.docs import get_swagger_ui_html

    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - Interactive Documentation",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui.css",
        swagger_ui_parameters=SWAGGER_UI_PARAMETERS,
        swagger_favicon_url="/favicon.ico",
    )


@app.get("/redoc", include_in_schema=False)
async def custom_redoc_html():
    """Custom ReDoc page"""
    from fastapi.openapi.docs import get_redoc_html

    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - ReDoc Documentation",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@2.1.3/bundles/redoc.standalone.js",
        redoc_favicon_url="/favicon.ico",
    )


@app.get("/api-docs", response_class=HTMLResponse, include_in_schema=False)
async def api_documentation():
    """API documentation homepage with links to all documentation types."""
    from modules.api.templates import get_documentation_homepage_html

    html_content = get_documentation_homepage_html(app.title, app.version)
    return HTMLResponse(content=html_content)


# System routes
@app.get("/", response_model=APIResponse, summary="API Root", tags=["System"])
async def root():
    """API service root directory with basic system information."""
    return APIResponse(
        success=True,
        message="RAG Knowledge Management API is running",
        data={
            "version": app.version,
            "title": app.title,
            "docs": "/docs",
            "redoc": "/redoc",
            "health": "/health",
        },
    )


@app.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="Health Check",
    tags=["System"],
)
async def health_check():
    """
    System health check endpoint for monitoring and load balancers.

    Returns system status including:
    - Application status
    - Database connectivity
    - Version information
    """
    try:
        # Check database connection
        db = DatabaseConnection()
        db_status = await db.check_connection()

        return HealthCheckResponse(
            success=True,
            message="System is healthy",
            data={
                "status": "healthy",
                "version": app.version,
                "database": "connected" if db_status else "disconnected",
                "components": {
                    "api": "operational",
                    "database": "operational" if db_status else "degraded",
                },
            },
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthCheckResponse(
            success=False,
            message=f"Health check failed: {str(e)}",
            data={"status": "unhealthy", "version": app.version, "error": str(e)},
        )


# Application startup
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    logger.info(f"Starting {app.title} v{app.version}")
    logger.info("RAG Knowledge Management System initialized successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    logger.info("RAG Knowledge Management System shutting down")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
