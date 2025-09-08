"""
FastAPI application factory.

Creates and configures the FastAPI application.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from ...shared.di.container import Container, create_container
from ...infrastructure.config.config_manager import get_config
from ...shared.exceptions.base_exceptions import ApplicationError
from .document_controller import DocumentController
from .chat_controller import ChatController
from .topic_controller import TopicController


def create_app(container: Container = None) -> FastAPI:
    """Create and configure FastAPI application."""
    
    # Load configuration
    config = get_config()
    
    # Create container if not provided
    if container is None:
        container = create_container(config.environment)
    
    # Create FastAPI app
    app = FastAPI(
        title="RAG Knowledge Management API",
        description="A Clean Architecture implementation of a RAG-based knowledge management system",
        version="1.0.0",
        debug=config.debug
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Store container in app state
    app.state.container = container
    
    # Configure logging
    logging.basicConfig(level=getattr(logging, config.log_level))
    
    # Add exception handlers
    @app.exception_handler(ApplicationError)
    async def application_error_handler(request: Request, exc: ApplicationError):
        return JSONResponse(
            status_code=400 if exc.code != "NOT_FOUND" else 404,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details
                }
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logging.error(f"Unhandled exception: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An internal server error occurred"
                }
            }
        )
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "environment": config.environment}
    
    # Include routers
    document_controller = DocumentController(container)
    chat_controller = ChatController(container)
    topic_controller = TopicController(container)
    
    app.include_router(document_controller.router, prefix="/api/v1/documents", tags=["documents"])
    app.include_router(chat_controller.router, prefix="/api/v1/chat", tags=["chat"])
    app.include_router(topic_controller.router, prefix="/api/v1/topics", tags=["topics"])
    
    return app