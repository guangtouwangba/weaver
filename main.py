"""
Main FastAPI application for RAG system.

This module creates and configures the FastAPI application with all routes,
middleware, and infrastructure integration.
"""

import logging
import sys
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

# Infrastructure imports
from infrastructure import (
    get_config, validate_config,
    get_health_checker, get_metrics_collector, get_alert_manager
)

# API routes
from api.topic_routes import router as topic_router
from api.file_routes import router as file_router
from api.resource_routes import router as resource_router
from api.rag_routes import router as rag_router
from api.topic_files_routes import router as topic_files_router
from api.topic_stats_routes import router as topic_stats_router
from api.task_routes import router as task_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown operations including:
    - Configuration validation
    - Infrastructure health checks
    - Background monitoring startup
    """
    # Startup
    logger.info("Starting RAG API application...")
    
    try:
        # Validate configuration
        if not validate_config():
            logger.error("Configuration validation failed")
            raise RuntimeError("Invalid configuration")
        
        # Initialize monitoring
        health_checker = get_health_checker()
        # await health_checker.start_background_monitoring()
        
        # Initialize task processing service
        from infrastructure.tasks import get_task_service
        task_service = await get_task_service()
        logger.info("Task processing service initialized")
        
        logger.info("RAG API application started successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise
    finally:
        # Shutdown
        logger.info("Shutting down RAG API application...")
        
        try:
            # Stop background monitoring
            health_checker = get_health_checker()
            await health_checker.stop_background_monitoring()
            
            # Shutdown task processing service
            from infrastructure.tasks import shutdown_task_service
            await shutdown_task_service()
            logger.info("Task processing service shutdown")
            
            logger.info("RAG API application shutdown complete")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    
    # Get configuration
    config = get_config()
    
    # Create FastAPI app
    app = FastAPI(
        title="RAG Knowledge Management API",
        description="""
        A comprehensive API for Research-Augmented Generation (RAG) knowledge management system.
        
        ## Features
        
        * **Topic Management**: Create, update, and organize knowledge topics
        * **Resource Upload**: Upload and manage documents, images, and other resources
        * **Content Processing**: Automatic parsing and analysis of uploaded content
        * **Task Processing**: Asynchronous file embedding and processing pipeline
        * **Real-time Updates**: WebSocket and SSE support for live status tracking
        * **Search & Discovery**: Advanced search across topics and resources
        * **Event-Driven Architecture**: Real-time notifications and processing
        * **Storage Integration**: Scalable object storage with MinIO/S3
        * **Health Monitoring**: Comprehensive health checks and metrics
        
        ## Architecture
        
        This API follows Domain-Driven Design (DDD) principles with:
        - **Domain Layer**: Core business logic and entities
        - **Application Layer**: Use cases and orchestration
        - **Infrastructure Layer**: External service integrations
        - **API Layer**: REST endpoints and HTTP handling
        """,
        version="1.0.0",
        contact={
            "name": "RAG System Team",
            "email": "support@rag-system.com",
        },
        license_info={
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT",
        },
        lifespan=lifespan,
        docs_url=None,  # Disable default docs
        redoc_url=None,  # Disable default redoc
        openapi_url="/openapi.json" if config.debug else None,
        swagger_ui_parameters={
            "defaultModelsExpandDepth": -1,
            "defaultModelExpandDepth": 1,
            "displayRequestDuration": True,
            "docExpansion": "list",
            "filter": True,
            "showExtensions": True,
            "showCommonExtensions": True,
            "tryItOutEnabled": True,
            "syntaxHighlight.theme": "monokai"
        }
    )
    
    # Add middleware
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Configure CORS
    if config.security.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=config.security.cors_origins,
            allow_credentials=True,
            allow_methods=config.security.cors_methods,
            allow_headers=["*"],
        )
    else:
        # Allow all origins in development
        if config.environment == "development":
            app.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )
    
    # Include routers
    app.include_router(topic_router)
    app.include_router(file_router)
    app.include_router(resource_router)
    app.include_router(rag_router)
    app.include_router(topic_files_router)
    app.include_router(topic_stats_router)
    app.include_router(task_router)
    
    # Mount static files for Swagger UI
    try:
        app.mount("/static", StaticFiles(directory="static"), name="static")
    except Exception:
        # If static directory doesn't exist, create a fallback
        pass
    
    # Custom Swagger UI endpoint with local files
    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        """Custom Swagger UI with local files."""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>RAG Knowledge Management API - Swagger UI</title>
            <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui.css" />
            <link rel="icon" type="image/png" href="https://fastapi.tiangolo.com/img/favicon.png"/>
            <style>
                html { box-sizing: border-box; overflow: -moz-scrollbars-vertical; overflow-y: scroll; }
                *, *:before, *:after { box-sizing: inherit; }
                body { margin:0; background: #fafafa; }
                .swagger-ui .topbar { display: none; }
            </style>
        </head>
        <body>
            <div id="swagger-ui"></div>
            <script src="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui-bundle.js"></script>
            <script src="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui-standalone-preset.js"></script>
            <script>
                window.onload = function() {
                    const ui = SwaggerUIBundle({
                        url: '/openapi.json',
                        dom_id: '#swagger-ui',
                        deepLinking: true,
                        presets: [
                            SwaggerUIBundle.presets.apis,
                            SwaggerUIStandalonePreset
                        ],
                        plugins: [
                            SwaggerUIBundle.plugins.DownloadUrl
                        ],
                        layout: "BaseLayout",
                        tryItOutEnabled: true,
                        showExtensions: true,
                        showCommonExtensions: true,
                        defaultModelsExpandDepth: 1,
                        defaultModelExpandDepth: 1,
                        displayRequestDuration: true,
                        docExpansion: "list",
                        filter: true,
                        syntaxHighlight: {
                            theme: "monokai"
                        },
                        onComplete: function() {
                            console.log("Swagger UI loaded successfully");
                        },
                        onFailure: function(data) {
                            console.error("Swagger UI failed to load:", data);
                        }
                    });
                };
            </script>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content, status_code=200)
    
    # Custom ReDoc endpoint
    @app.get("/redoc", include_in_schema=False)
    async def custom_redoc_html():
        """Custom ReDoc with local files."""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>RAG Knowledge Management API - ReDoc</title>
            <meta charset="utf-8"/>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet">
            <style>
                body { margin: 0; padding: 0; }
            </style>
        </head>
        <body>
            <redoc spec-url="/openapi.json"></redoc>
            <script src="https://cdn.jsdelivr.net/npm/redoc@2.1.3/bundles/redoc.standalone.js"></script>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content, status_code=200)
    
    # Add custom OpenAPI schema
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
            openapi_version="3.0.2"  # Force OpenAPI 3.0.2 for better Swagger UI compatibility
        )
        
        # Add custom schema extensions
        openapi_schema["info"]["x-environment"] = config.environment
        openapi_schema["info"]["x-version"] = "1.0.0"
        
        # Ensure compatibility with Swagger UI
        if "servers" not in openapi_schema:
            openapi_schema["servers"] = [
                {"url": "/", "description": "Current server"}
            ]
        
        # Add security schemes if needed
        if "components" not in openapi_schema:
            openapi_schema["components"] = {}
        
        # Enhance OpenAPI schema with task processing documentation
        from api.swagger_docs import enhance_openapi_schema
        openapi_schema = enhance_openapi_schema(openapi_schema)
        
        app.openapi_schema = openapi_schema
        return app.openapi_schema
    
    app.openapi = custom_openapi
    
    return app


# Create app instance
app = create_app()


# Health and monitoring endpoints

@app.get("/health", tags=["health"], include_in_schema=False)
async def health_check():
    """
    Application health check endpoint.
    
    Returns the health status of the application and its dependencies.
    """
    try:
        health_checker = get_health_checker()
        system_health = await health_checker.check_all()
        
        return {
            "status": system_health.status.value,
            "timestamp": system_health.timestamp.isoformat(),
            "healthy_components": system_health.healthy_components,
            "total_components": system_health.total_components,
            "health_percentage": system_health.health_percentage,
            "components": [
                {
                    "component": comp.component,
                    "status": comp.status.value,
                    "message": comp.message,
                    "response_time_ms": comp.response_time_ms
                }
                for comp in system_health.components
            ]
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": logger.info.__name__
            }
        )


@app.get("/metrics", tags=["monitoring"], include_in_schema=False)
async def get_metrics():
    """
    Prometheus-compatible metrics endpoint.
    
    Returns application metrics in Prometheus format.
    """
    try:
        metrics_collector = get_metrics_collector()
        metrics = metrics_collector.export_prometheus_format()
        
        from fastapi import Response
        return Response(content=metrics, media_type="text/plain")
    except Exception as e:
        logger.error(f"Metrics collection failed: {e}")
        raise HTTPException(status_code=500, detail="Metrics unavailable")


@app.get("/info", tags=["info"])
async def get_info():
    """
    Application information endpoint.
    
    Returns general information about the application and its configuration.
    """
    config = get_config()
    
    return {
        "application": "RAG Knowledge Management API",
        "version": "1.0.0",
        "environment": config.environment,
        "debug": config.debug,
        "features": {
            "topic_management": True,
            "resource_upload": True,
            "content_processing": True,
            "task_processing": True,
            "real_time_updates": True,
            "search": True,
            "messaging": True,
            "storage": True,
            "monitoring": True
        },
        "endpoints": {
            "topics": "/api/v1/topics",
            "files": "/api/v1/files",
            "tasks": "/api/v1/tasks",
            "websocket": "/api/v1/tasks/ws/{topic_id}/{client_id}",
            "sse": "/api/v1/tasks/events/{topic_id}",
            "health": "/health",
            "metrics": "/metrics",
            "docs": "/docs" if config.debug else None,
            "redoc": "/redoc" if config.debug else None
        }
    }


# Import exception handlers
from api.exceptions import (
    RAGAPIException, rag_api_exception_handler,
    http_exception_handler, validation_exception_handler,
    general_exception_handler
)
from pydantic import ValidationError

# Register exception handlers
app.add_exception_handler(RAGAPIException, rag_api_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(ValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)


# Request/Response middleware

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests and responses."""
    import time
    
    start_time = time.time()
    
    # Log request
    logger.info(f"Request: {request.method} {request.url}")
    
    # Process request
    response = await call_next(request)
    
    # Calculate response time
    process_time = time.time() - start_time
    
    # Log response
    logger.info(
        f"Response: {response.status_code} - {process_time:.3f}s - "
        f"{request.method} {request.url}"
    )
    
    # Add response time header
    response.headers["X-Process-Time"] = str(process_time)
    
    return response


if __name__ == "__main__":
    import uvicorn
    
    config = get_config()
    
    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=config.debug,
        log_level="info" if not config.debug else "debug",
        access_log=True
    )