"""
Main application entry point for DDD + RAG architecture.

This module creates and configures the FastAPI application using 
Domain-Driven Design principles with RAG capabilities.
"""

import logging
import sys
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from config import get_config, RAGConfig
from interfaces.api.controllers.rag_controller import router as rag_router


# Configure logging
def setup_logging(config: RAGConfig):
    """Setup application logging."""
    logging.basicConfig(
        level=getattr(logging, config.log_level.upper()),
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
    - Infrastructure initialization
    - Service registration
    """
    # Startup
    logger.info("Starting DDD + RAG application...")
    
    try:
        # Get and validate configuration
        config = get_config()
        errors = config.validate()
        if errors:
            logger.error(f"Configuration validation failed: {'; '.join(errors)}")
            raise RuntimeError("Invalid configuration")
        
        logger.info("Configuration validated successfully")
        
        # Initialize infrastructure services
        # (In real implementation, these would be properly initialized)
        logger.info("Initializing infrastructure services...")
        
        # Vector store
        # vector_store = create_vector_store(config.vector_store)
        
        # Embedding service  
        # embedding_service = create_embedding_service(config.embedding)
        
        # Document processing
        # document_processor = create_document_processor(config.document_processing)
        
        # Event bus
        # event_bus = create_event_bus()
        
        # Initialize repositories
        # document_repository = create_document_repository(config.database)
        
        # Initialize domain services
        # knowledge_extractor = create_knowledge_extraction_service()
        # rag_domain_service = RAGDomainService(document_repository, knowledge_extractor)
        
        # Initialize application services
        # rag_app_service = RAGApplicationService(
        #     rag_domain_service,
        #     document_repository,
        #     vector_store,
        #     embedding_service,
        #     event_bus
        # )
        
        # Note: Routes will be registered in create_app() function
        
        logger.info("DDD + RAG application started successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise
    finally:
        # Shutdown
        logger.info("Shutting down DDD + RAG application...")
        
        try:
            # Cleanup infrastructure services
            # await vector_store.close()
            # await event_bus.close()
            
            logger.info("DDD + RAG application shutdown complete")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    
    # Get configuration
    config = get_config()
    
    # Setup logging
    setup_logging(config)
    
    # Create FastAPI app
    app = FastAPI(
        title="RAG Knowledge Management API (DDD Architecture)",
        description="""
        A Domain-Driven Design implementation of a RAG (Retrieval-Augmented Generation) 
        knowledge management system.
        
        ## Architecture
        
        This API follows Domain-Driven Design (DDD) principles:
        
        ### Domain Layer
        - **Entities**: Document, Topic, Knowledge, KnowledgeBase
        - **Value Objects**: FileMetadata, SearchCriteria
        - **Domain Services**: RAGDomainService, KnowledgeExtractionService
        - **Repositories**: Abstract interfaces for data access
        
        ### Application Layer  
        - **Application Services**: RAGApplicationService, DocumentApplicationService
        - **DTOs**: Request/Response data transfer objects
        - **Workflows**: Document ingestion, knowledge extraction workflows
        
        ### Infrastructure Layer
        - **RAG Components**: Vector stores, embeddings, retrievers
        - **Persistence**: Database repositories, ORM models
        - **External APIs**: OpenAI, Pinecone, etc.
        
        ### Interface Layer
        - **REST API**: HTTP controllers and endpoints
        - **Middleware**: Authentication, CORS, error handling
        
        ## Features
        
        * **Document Ingestion**: Upload and process documents into knowledge base
        * **Semantic Search**: Find relevant content using vector embeddings  
        * **Knowledge Extraction**: Extract structured knowledge from documents
        * **Hybrid Search**: Combine semantic and keyword search
        * **Related Content**: Find similar content based on semantic similarity
        * **Topic Management**: Organize content by topics and categories
        * **Event-Driven Architecture**: Asynchronous processing with domain events
        
        ## RAG Capabilities
        
        * **Vector Embeddings**: Support for multiple embedding providers
        * **Multiple Vector Stores**: Chroma, Pinecone, Weaviate integration
        * **Document Processing**: Intelligent chunking and metadata extraction
        * **Search Strategies**: Semantic, keyword, and hybrid search
        * **Knowledge Graphs**: Extract and link related knowledge concepts
        """,
        version="2.0.0",
        contact={
            "name": "RAG System Team",
            "email": "support@rag-system.com",
        },
        license_info={
            "name": "MIT", 
            "url": "https://opensource.org/licenses/MIT",
        },
        lifespan=lifespan,
        docs_url=None,  # We'll create custom docs endpoint
        redoc_url=None,  # We'll create custom redoc endpoint  
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
    if config.environment == "development":
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    # Include API routes
    app.include_router(rag_router)
    
    # Mount static files
    try:
        # Try to mount static files from parent directory
        import os
        static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
        if os.path.exists(static_dir):
            app.mount("/static", StaticFiles(directory=static_dir), name="static")
            logger.info(f"Mounted static files from: {static_dir}")
        else:
            logger.warning(f"Static directory not found: {static_dir}")
    except Exception as e:
        logger.warning(f"Could not mount static files: {e}")
        # Continue without static files - will fall back to CDN
    
    # Health check endpoint
    @app.get("/health", tags=["health"], include_in_schema=False)
    async def health_check():
        """Application health check endpoint."""
        config = get_config()
        
        return {
            "status": "healthy",
            "version": "2.0.0",
            "architecture": "DDD + RAG",
            "environment": config.environment,
            "features": {
                "document_ingestion": True,
                "semantic_search": True,
                "knowledge_extraction": True,
                "hybrid_search": config.search.enable_hybrid_search,
                "reranking": config.search.enable_reranking,
                "vector_store": config.vector_store.provider,
                "embedding_provider": config.embedding.provider
            },
            "configuration": {
                "chunk_size": config.document_processing.chunk_size,
                "chunk_overlap": config.document_processing.chunk_overlap,
                "similarity_threshold": config.search.similarity_threshold,
                "max_file_size_mb": config.document_processing.max_file_size_mb
            }
        }
    
    # System info endpoint
    @app.get("/info", tags=["info"])
    async def get_system_info():
        """System information endpoint."""
        config = get_config()
        
        return {
            "application": "RAG Knowledge Management API",
            "version": "2.0.0",
            "architecture": "Domain-Driven Design (DDD)",
            "environment": config.environment,
            "debug": config.debug,
            "layers": {
                "domain": {
                    "description": "Core business logic and entities",
                    "components": ["entities", "value_objects", "domain_services", "repositories"]
                },
                "application": {
                    "description": "Use cases and workflow orchestration", 
                    "components": ["application_services", "dtos", "handlers", "workflows"]
                },
                "infrastructure": {
                    "description": "Technical implementations and external integrations",
                    "components": ["rag_components", "persistence", "messaging", "storage"]
                },
                "interface": {
                    "description": "API controllers and HTTP handling",
                    "components": ["rest_api", "middleware", "serializers"]
                }
            },
            "rag_features": {
                "vector_store": config.vector_store.provider,
                "embedding_model": config.embedding.model_name,
                "document_processing": {
                    "chunk_size": config.document_processing.chunk_size,
                    "supported_types": config.document_processing.supported_file_types
                },
                "search_capabilities": {
                    "semantic_search": True,
                    "hybrid_search": config.search.enable_hybrid_search,
                    "reranking": config.search.enable_reranking
                }
            },
            "endpoints": {
                "document_ingestion": "/api/v1/rag/documents/ingest",
                "file_upload": "/api/v1/rag/documents/upload", 
                "knowledge_search": "/api/v1/rag/search",
                "knowledge_extraction": "/api/v1/rag/documents/{id}/knowledge",
                "related_content": "/api/v1/rag/content/related",
                "health": "/health",
                "docs": "/docs" if config.debug else None
            }
        }
    
    # Custom Swagger UI endpoint using CDN
    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        """Custom Swagger UI with CDN resources."""
        from fastapi.responses import HTMLResponse
        
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
    
    # Custom ReDoc endpoint using CDN
    @app.get("/redoc", include_in_schema=False)
    async def custom_redoc_html():
        """Custom ReDoc with CDN resources."""
        from fastapi.responses import HTMLResponse
        
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
    
    # Custom OpenAPI generator to ensure compatibility
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        
        from fastapi.openapi.utils import get_openapi
        
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
            openapi_version="3.0.2"  # Use 3.0.2 for better Swagger UI compatibility
        )
        
        # Add custom schema extensions
        openapi_schema["info"]["x-environment"] = config.environment
        openapi_schema["info"]["x-architecture"] = "DDD + RAG"
        
        # Ensure servers are defined
        if "servers" not in openapi_schema:
            openapi_schema["servers"] = [
                {"url": "/", "description": "Current server"}
            ]
        
        # Add security schemes if needed
        if "components" not in openapi_schema:
            openapi_schema["components"] = {}
        
        app.openapi_schema = openapi_schema
        return app.openapi_schema
    
    app.openapi = custom_openapi
    
    return app


# Exception handlers
async def handle_rag_exceptions(request: Request, call_next):
    """Handle RAG-specific exceptions."""
    try:
        response = await call_next(request)
        return response
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={
                "error": "VALIDATION_ERROR",
                "message": str(e),
                "type": "domain_validation"
            }
        )
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "error": "INTERNAL_SERVER_ERROR", 
                "message": "An unexpected error occurred",
                "type": "system_error"
            }
        )


# Create app instance
app = create_app()

# Add global exception handler  
app.middleware("http")(handle_rag_exceptions)


if __name__ == "__main__":
    import uvicorn
    
    config = get_config()
    
    # Run the application
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=config.debug,
        log_level=config.log_level.lower(),
        access_log=True
    )
