"""
RAG Knowledge Management System - Main Application

A modern RAG system with clean architecture based on Service layer orchestration.
Architecture: Schema + Repository + Service + API
"""

import logging

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response

from config.docs import SWAGGER_UI_PARAMETERS
from config.settings import AppConfig
from modules.api import api_router
from modules.api.error_handlers import (
    general_exception_handler,
    request_validation_error_handler,
    unicode_decode_error_handler,
)
from modules.database import DatabaseConnection
from modules.schemas import APIResponse, HealthCheckResponse

# Prometheus metrics support
try:
    from prometheus_client import generate_latest, Counter, Histogram, Gauge
    from prometheus_client.multiprocess import MultiProcessCollector
    from prometheus_client.registry import CollectorRegistry
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False


async def initialize_vector_collections():
    """初始化向量存储集合，在服务启动时创建"""
    try:
        from modules.vector_store.weaviate_service import WeaviateVectorStore
        from modules.vector_store.base import VectorStoreConfig, VectorStoreProvider, SimilarityMetric
        from config import get_config
        
        config = get_config()
        
        # 创建WeaviateVectorStore实例，启用集合创建
        weaviate_store = WeaviateVectorStore(
            url=getattr(config, 'weaviate_url', None) or 
                config.vector_db.weaviate_url or 
                "http://localhost:8080",
            api_key=getattr(config, 'weaviate_api_key', None),
            create_collections_on_init=True  # 启动时创建集合
        )
        
        # 初始化连接并创建集合
        await weaviate_store.initialize()
        
        logger.info("🎉 向量存储服务已启动，集合已准备就绪")
        
        # 清理连接
        await weaviate_store.cleanup()
        
    except ImportError as e:
        logger.warning(f"向量存储模块不可用: {e}")
        raise
    except Exception as e:
        logger.error(f"向量存储初始化失败: {e}")
        raise


async def initialize_elasticsearch():
    """初始化Elasticsearch聊天服务"""
    try:
        from modules.services.elasticsearch_service import elasticsearch_chat_service
        
        # 初始化Elasticsearch连接
        success = await elasticsearch_chat_service.initialize()
        
        if success:
            logger.info("🎉 Elasticsearch聊天服务已启动，索引已准备就绪")
        else:
            logger.warning("⚠️ Elasticsearch聊天服务初始化失败，将使用空实现")
        
        return success
        
    except ImportError as e:
        logger.warning(f"Elasticsearch模块不可用: {e}")
        return False
    except Exception as e:
        logger.error(f"Elasticsearch初始化失败: {e}")
        return False

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
app.include_router(api_router)


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
        await db.initialize()  # 需要先初始化数据库连接
        db_status = await db.health_check()

        return HealthCheckResponse(
            status="healthy",
            version=app.version,
            components={
                "api": "operational",
                "database": "operational" if db_status else "degraded",
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthCheckResponse(
            status="unhealthy",
            version=app.version,
            components={
                "api": "operational",
                "database": "error",
            }
        )


@app.get("/metrics", include_in_schema=False, summary="Prometheus Metrics")
async def metrics():
    """
    Prometheus metrics endpoint for monitoring and alerting.
    
    Returns application metrics in Prometheus format including:
    - Request counts and durations
    - System resource usage  
    - Application-specific metrics
    """
    if not PROMETHEUS_AVAILABLE:
        return Response(
            content="# Prometheus client not available\n", 
            media_type="text/plain"
        )
    
    try:
        # Create a new registry for this request
        registry = CollectorRegistry()
        
        # Add multiprocess collector if available
        try:
            MultiProcessCollector(registry)
        except (OSError, ValueError):
            # Fallback to default registry if multiprocess not available
            from prometheus_client import REGISTRY
            registry = REGISTRY
        
        # Generate metrics
        metrics_output = generate_latest(registry)
        return Response(content=metrics_output, media_type="text/plain")
        
    except Exception as e:
        logger.error(f"Failed to generate metrics: {e}")
        return Response(
            content=f"# Error generating metrics: {e}\n", 
            media_type="text/plain"
        )


# Application startup
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    logger.info(f"Starting {app.title} v{app.version}")
    
    # 初始化向量存储集合 (fail fast)
    try:
        await initialize_vector_collections()
        logger.info("✅ Weaviate集合初始化成功")
    except Exception as e:
        logger.error(f"❌ Weaviate集合初始化失败: {e}")
        # 这里可以选择是否要fail fast（抛出异常使应用启动失败）
        # 对于生产环境，可以考虑graceful degradation
        logger.warning("⚠️  应用将在没有向量存储的情况下启动")
    
    # 初始化Elasticsearch聊天服务
    try:
        await initialize_elasticsearch()
        logger.info("✅ Elasticsearch聊天服务初始化成功")
    except Exception as e:
        logger.error(f"❌ Elasticsearch聊天服务初始化失败: {e}")
        logger.warning("⚠️  应用将在没有Elasticsearch聊天历史的情况下启动")
    
    logger.info("RAG Knowledge Management System initialized successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    logger.info("RAG Knowledge Management System shutting down")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
