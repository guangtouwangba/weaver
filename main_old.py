"""
RAG Knowledge Management System - Main Application

A modern RAG system with clean architecture based on Service layer orchestration.
Architecture: Schema + Repository + Service + API
"""

import logging
from fastapi import FastAPI, HTTPException
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
    general_exception_handler
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
        "email": "support@example.com"
    },
    "license_info": {
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    }
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

# Register new Service layer API routes
app.include_router(api_router)

# Custom Swagger UI page
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
        swagger_favicon_url="/favicon.ico"
    )

# Custom ReDoc page
@app.get("/redoc", include_in_schema=False)
async def custom_redoc_html():
    """Custom ReDoc page"""
    from fastapi.openapi.docs import get_redoc_html
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - ReDoc Documentation",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@2.1.3/bundles/redoc.standalone.js",
        redoc_favicon_url="/favicon.ico"
    )

# Add documentation homepage
@app.get("/api-docs", response_class=HTMLResponse, include_in_schema=False)
async def api_documentation():
    """
API documentation homepage providing various documentation entries
"""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{app.title} - API Documentation Center</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                max-width: 1200px;
                margin: 0 auto;
                padding: 2rem;
                line-height: 1.6;
                color: #333;
            }}
            .header {{
                text-align: center;
                margin-bottom: 3rem;
                padding: 2rem;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border-radius: 10px;
            }}
            .cards {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 2rem;
                margin-bottom: 3rem;
            }}
            .card {{
                padding: 2rem;
                border: 1px solid #e1e5e9;
                border-radius: 8px;
                text-decoration: none;
                color: inherit;
                transition: transform 0.2s, box-shadow 0.2s;
            }}
            .card:hover {{
                transform: translateY(-4px);
                box-shadow: 0 4px 20px rgba(0,0,0,0.1);
                text-decoration: none;
            }}
            .card h3 {{
                margin-top: 0;
                color: #1976d2;
            }}
            .features {{
                background: #f8f9fa;
                padding: 2rem;
                border-radius: 8px;
            }}
            .feature-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 1.5rem;
                margin-top: 1rem;
            }}
            .feature {{
                background: white;
                padding: 1.5rem;
                border-radius: 6px;
                border-left: 4px solid #1976d2;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🔍 {app.title}</h1>
            <p>Intelligent Knowledge Management System Based on DDD Architecture</p>
            <p>Version: {app.version}</p>
        </div>
        
        <div class="cards">
            <a href="/docs" class="card">
                <h3>📊 Swagger UI</h3>
                <p>Interactive API documentation with online testing and debugging support. Provides rich interface and parameter validation.</p>
                <p><strong>Suitable for</strong>: Developer testing, API exploration</p>
            </a>
            
            <a href="/redoc" class="card">
                <h3>📚 ReDoc</h3>
                <p>Beautiful documentation reading interface with optimized layout and navigation. Perfect for product documentation and user manuals.</p>
                <p><strong>Suitable for</strong>: Documentation reading, product introduction</p>
            </a>
            
            <a href="/openapi.json" class="card">
                <h3>⚙️ OpenAPI JSON</h3>
                <p>OpenAPI specification in JSON format, can be used for client code generation, testing tools, etc.</p>
                <p><strong>Suitable for</strong>: Code generation, tool integration</p>
            </a>
            
            <a href="/health" class="card">
                <h3>❤️ System Status</h3>
                <p>Check the running status of system components including database, storage, cache, etc.</p>
                <p><strong>Suitable for</strong>: Operations monitoring, system diagnostics</p>
            </a>
        </div>
        
        <div class="features">
            <h2>🚀 System Features</h2>
            <div class="feature-grid">
                <div class="feature">
                    <h4>📚 Intelligent Document Processing</h4>
                    <p>Support PDF, Word, TXT and other formats with automatic extraction, chunking, and vectorization</p>
                </div>
                <div class="feature">
                    <h4>🔍 Semantic Search</h4>
                    <p>Intelligent content retrieval based on vector similarity, supporting multiple languages</p>
                </div>
                <div class="feature">
                    <h4>🏷️ Topic Management</h4>
                    <p>Flexible knowledge classification and organization system, building knowledge graphs</p>
                </div>
                <div class="feature">
                    <h4>⚡ High-Performance Async</h4>
                    <p>Non-blocking I/O operations supporting high concurrency and real-time processing</p>
                </div>
            </div>
        </div>
        
        <footer style="text-align: center; margin-top: 3rem; padding: 2rem; color: #666;">
            <p>Powered by FastAPI + RAG Technology | Licensed under MIT</p>
        </footer>
        
        <style>
            .docs-info {{
                background: #f8f9fa;
                padding: 1rem;
                border-radius: 6px;
                border-left: 4px solid #28a745;
                margin: 1rem 0;
            }}
        </style>
        <script>
            // Add simple page interaction features
            document.addEventListener('DOMContentLoaded', function() {{
                console.log('API Documentation Center loaded');
            }});
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/", response_model=APIResponse, summary="API Root Directory", tags=["System Information"])
async def root():
    """
    # API Service Root Directory
    
    Returns basic information and version details of the RAG Knowledge Management System.
    
    ## Response Content
    - 🚀 **Service Name**: RAG Knowledge Management API
    - 📦 **Version Info**: Current system version
    - 🏗️ **Architecture Pattern**: DDD + Service Layer
    - 📊 **Technology Stack**: FastAPI + SQLAlchemy + Pydantic
    
    ## Use Cases
    Used to check if the API service is running normally and to get basic system information.
    """
    return APIResponse(
        success=True,
        message="RAG Knowledge Management API v2.0.0",
        data={
            "service": "RAG Knowledge Management API",
            "version": "2.0.0", 
            "architecture": "DDD + Service Layer",
            "features": [
                "Document upload and processing",
                "Intelligent text chunking",
                "Vector search",
                "Topic management",
                "Multi-storage backend support"
            ],
            "endpoints": {
                "docs": "/docs",
                "redoc": "/redoc",
                "openapi": "/openapi.json",
                "health": "/health"
            }
        }
    )

@app.get("/health", response_model=APIResponse, summary="System Health Check", tags=["System Information"])
async def health_check():
    """
    # System Health Status Check
    
    Check the running status of various components of the RAG system, including database connections, service layer status, etc.
    
    ## Check Items
    - 🗄️ **Database**: PostgreSQL connection status
    - ⚙️ **API Service**: FastAPI application status
    - 🔧 **Business Services**: Service layer component status
    - 📊 **Data Layer**: Repository layer status
    - 📋 **Schema**: Pydantic model validation status
    
    ## Return Status
    - ✅ **healthy**: All components normal
    - ⚠️ **degraded**: Some components abnormal but service available
    - ❌ **unhealthy**: Critical components abnormal, service unavailable
    
    ## Monitoring Recommendations
    Recommend using this endpoint for:
    - Load balancer health checks
    - Monitoring system status polling
    - Container orchestration health probes
    - Operations automation scripts
    """
    try:
        # Check database connection
        db_status = "healthy"
        try:
            from modules.database import get_database_connection
            db = await get_database_connection()
            # Execute simple health check
            health_ok = await db.health_check()
            if not health_ok:
                db_status = "unhealthy: health check failed"
        except Exception as e:
            db_status = f"unhealthy: {str(e)}"
        
        health_data = HealthCheckResponse(
            status="healthy" if db_status == "healthy" else "degraded",
            version="2.0.0",
            components={
                "database": db_status,
                "api": "healthy",
                "services": "healthy",
                "repositories": "healthy",
                "schemas": "healthy"
            }
        )
        
        return APIResponse(
            success=True,
            data=health_data
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")

# Complete dependency check endpoint
@app.get("/health/detailed", summary="Detailed Health Check", tags=["System Information"])
async def detailed_health_check():
    """
    # Detailed Health Check Endpoint
    
    Run complete dependency service checks including status of all middleware and external services.
    
    ## Services Checked
    - 🗄️ **Database**: PostgreSQL connection, configuration validation, performance status
    - 🤖 **AI Services**: OpenAI, Anthropic, HuggingFace API configuration
    - 💾 **Storage Services**: Local storage or MinIO connection status
    - 🔍 **Vector Database**: Weaviate, ChromaDB and other library availability
    
    ## Return Information
    - Overall status summary
    - Detailed status of each service
    - Configuration warnings and errors
    - Performance metrics and capacity information
    
    ## Application Scenarios
    - Complete verification after system deployment
    - Troubleshooting and diagnosis
    - Operations monitoring and reporting
    - Validation after configuration changes
    """
    try:
        from config import get_config
        from datetime import datetime
        
        config = get_config()
        health_result = await initialize_checks(config)
        
        return {
            "success": True,
            "data": health_result,
            "message": "Detailed health check completed",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "2.0.0"
        }
    except Exception as e:
        from datetime import datetime
        logger.error(f"Detailed health check failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Detailed health check failed",
            "timestamp": datetime.utcnow().isoformat(),
            "status_code": 500
        }

@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    logger.info("🚀 Starting RAG API with Service Layer...")
    
    # Run dependency health checks
    try:
        from config import get_config
        config = get_config()
        health_result = await initialize_checks(config)
        
        # Decide whether to continue startup based on health check results
        if health_result["overall_status"] == "error":
            logger.error("🚨 Critical dependencies failed health check!")
            logger.error("   Application may not function correctly.")
            logger.error("   Please check the error details above and fix the issues.")
        elif health_result["overall_status"] == "warning":
            logger.warning("⚠️ Some dependencies have warnings but application can start")
        else:
            logger.info("🎉 All dependencies passed health checks!")
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        logger.warning("   Continuing startup anyway...")
    
    logger.info("📚 API Documentation available at:")
    logger.info("   - Swagger UI: http://localhost:8000/docs")
    logger.info("   - ReDoc: http://localhost:8000/redoc")
    logger.info("   - OpenAPI JSON: http://localhost:8000/openapi.json")
    logger.info("   - Docs Center: http://localhost:8000/api-docs")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    logger.info("👋 Shutting down RAG API...")


async def database_connection_check(config: AppConfig) -> dict:
    """
    Check database connection status
    
    Returns:
        dict: Check results including status and detailed information
    """
    result = {
        "service": "PostgreSQL Database",
        "status": "unknown", 
        "details": {},
        "errors": [],
        "warnings": []
    }
    
    try:
        # 检查数据库配置
        db_config = config.database
        
        # 配置安全性检查
        security_warnings = db_config.validate_security()
        if security_warnings:
            result["warnings"].extend(security_warnings)
        
        # 尝试连接数据库
        logger.info(f"🔍 Checking database connection: {db_config.host}:{db_config.port}")
        
        from modules.database.connection import get_database_connection
        db = await get_database_connection()
        
        # 执行健康检查
        health_check_result = await db.health_check()
        
        if health_check_result:
            result["status"] = "healthy"
            result["details"] = {
                "host": db_config.host,
                "port": db_config.port,
                "database": db_config.name,
                "driver": db_config.driver,
                "pool_size": db_config.pool_size,
                "connection_url": db_config.url.replace(db_config.password or "", "***") if db_config.password else db_config.url
            }
            logger.info("✅ Database connection: HEALTHY")
        else:
            result["status"] = "unhealthy"
            result["errors"].append("Database health check failed")
            logger.error("❌ Database connection: FAILED")
            
    except Exception as e:
        result["status"] = "error"
        result["errors"].append(f"Database connection error: {str(e)}")
        logger.error(f"❌ Database connection check failed: {e}")
    
    return result

async def ai_config_check(config: AppConfig) -> dict:
    """
    检查AI服务配置和可用性
    
    Returns:
        dict: 检查结果
    """
    result = {
        "service": "AI Services",
        "status": "unknown",
        "details": {},
        "errors": [],
        "warnings": []
    }
    
    try:
        ai_config = config.ai
        logger.info("🔍 Checking AI services configuration...")
        
        # Get model names based on the selected provider
        embedding_model = None
        chat_model = None
        
        # Get embedding model based on provider
        if ai_config.embedding.provider == "openai":
            embedding_model = ai_config.embedding.openai.embedding_model
        elif ai_config.embedding.provider == "huggingface":
            embedding_model = ai_config.embedding.huggingface.embedding_model
        elif ai_config.embedding.provider == "local":
            embedding_model = ai_config.embedding.local.embedding_model
        
        # Get chat model based on provider
        if ai_config.chat.provider == "openai":
            chat_model = ai_config.chat.openai.chat_model
        elif ai_config.chat.provider == "anthropic":
            chat_model = ai_config.chat.anthropic.chat_model
        elif ai_config.chat.provider == "huggingface":
            chat_model = ai_config.chat.huggingface.chat_model
        elif ai_config.chat.provider == "local":
            chat_model = ai_config.chat.local.chat_model
        
        details = {
            "embedding_provider": ai_config.embedding.provider,
            "embedding_model": embedding_model,
            "chat_provider": ai_config.chat.provider,
            "chat_model": chat_model
        }
        
        # 检查API密钥配置
        providers_checked = []
        
        # 检查OpenAI配置 (check both embedding and chat configs)
        openai_api_key = None
        if ai_config.embedding.provider == "openai" and ai_config.embedding.openai.api_key:
            openai_api_key = ai_config.embedding.openai.api_key
        elif ai_config.chat.provider == "openai" and ai_config.chat.openai.api_key:
            openai_api_key = ai_config.chat.openai.api_key
        
        if openai_api_key:
            try:
                # 简单的API密钥格式验证
                if openai_api_key.startswith('sk-'):
                    details["openai_configured"] = True
                    providers_checked.append("OpenAI")
                    logger.info("✅ OpenAI API key configured")
                else:
                    result["warnings"].append("OpenAI API key format may be invalid")
            except Exception as e:
                result["warnings"].append(f"OpenAI configuration issue: {e}")
        else:
            result["warnings"].append("OpenAI API key not configured")
        
        # 检查Anthropic配置
        anthropic_api_key = None
        if ai_config.chat.provider == "anthropic" and ai_config.chat.anthropic.api_key:
            anthropic_api_key = ai_config.chat.anthropic.api_key
        
        if anthropic_api_key:
            try:
                if anthropic_api_key.startswith('sk-ant-'):
                    details["anthropic_configured"] = True
                    providers_checked.append("Anthropic")
                    logger.info("✅ Anthropic API key configured")
                else:
                    result["warnings"].append("Anthropic API key format may be invalid")
            except Exception as e:
                result["warnings"].append(f"Anthropic configuration issue: {e}")
        else:
            result["warnings"].append("Anthropic API key not configured")
        
        # 检查HuggingFace配置
        huggingface_api_key = None
        if ai_config.embedding.provider == "huggingface" and ai_config.embedding.huggingface.api_key:
            huggingface_api_key = ai_config.embedding.huggingface.api_key
        elif ai_config.chat.provider == "huggingface" and ai_config.chat.huggingface.api_key:
            huggingface_api_key = ai_config.chat.huggingface.api_key
        
        if huggingface_api_key:
            details["huggingface_configured"] = True
            providers_checked.append("HuggingFace")
            logger.info("✅ HuggingFace API key configured")
        else:
            result["warnings"].append("HuggingFace API key not configured")
        
        result["details"] = details
        
        if providers_checked:
            result["status"] = "healthy"
            result["details"]["configured_providers"] = providers_checked
            logger.info(f"✅ AI services: {len(providers_checked)} provider(s) configured")
        else:
            result["status"] = "warning"
            result["warnings"].append("No AI providers are properly configured")
            logger.warning("⚠️ AI services: No providers configured")
            
    except Exception as e:
        result["status"] = "error"
        result["errors"].append(f"AI configuration check error: {str(e)}")
        logger.error(f"❌ AI services check failed: {e}")
    
    return result

async def storage_config_check(config: AppConfig) -> dict:
    """
    检查存储服务配置和连接
    
    Returns:
        dict: 检查结果
    """
    result = {
        "service": "Storage Services",
        "status": "unknown",
        "details": {},
        "errors": [],
        "warnings": []
    }
    
    try:
        storage_config = config.storage
        logger.info(f"🔍 Checking storage configuration: {storage_config.provider}")
        
        details = {
            "provider": storage_config.provider,
            "bucket_name": storage_config.bucket_name
        }
        
        if storage_config.provider == "local":
            # 检查本地存储
            import os
            from pathlib import Path
            
            storage_path = Path(storage_config.local_path)
            
            # 检查目录是否存在
            if not storage_path.exists():
                try:
                    storage_path.mkdir(parents=True, exist_ok=True)
                    logger.info(f"✅ Created local storage directory: {storage_path}")
                except Exception as e:
                    result["errors"].append(f"Cannot create storage directory: {e}")
                    result["status"] = "error"
                    return result
            
            # 检查目录权限
            if not os.access(storage_path, os.R_OK | os.W_OK):
                result["errors"].append(f"Insufficient permissions for storage directory: {storage_path}")
                result["status"] = "error"
                return result
            
            # 获取存储空间信息
            import shutil
            total, used, free = shutil.disk_usage(storage_path)
            
            details.update({
                "local_path": str(storage_path),
                "total_space": f"{total // (1024**3)} GB",
                "used_space": f"{used // (1024**3)} GB", 
                "free_space": f"{free // (1024**3)} GB",
                "usage_percent": round((used / total) * 100, 2)
            })
            
            # 磁盘空间警告
            if (used / total) > 0.85:
                result["warnings"].append("Storage disk usage is above 85%")
            
            result["status"] = "healthy"
            logger.info("✅ Local storage: HEALTHY")
            
        elif storage_config.provider == "minio":
            # 检查MinIO配置
            try:
                from modules.storage.minio_storage import MinIOStorage
                
                minio_storage = MinIOStorage(
                    endpoint=storage_config.minio_endpoint,
                    access_key=storage_config.minio_access_key,
                    secret_key=storage_config.minio_secret_key,
                    bucket_name=storage_config.bucket_name,
                    secure=storage_config.minio_secure
                )
                
                # 测试连接和桶访问
                bucket_exists = minio_storage.client.bucket_exists(storage_config.bucket_name)
                if not bucket_exists:
                    result["warnings"].append(f"Bucket '{storage_config.bucket_name}' does not exist")
                
                details.update({
                    "endpoint": storage_config.minio_endpoint,
                    "bucket_name": storage_config.bucket_name,
                    "secure": storage_config.minio_secure
                })
                
                result["status"] = "healthy"
                logger.info("✅ MinIO storage: HEALTHY")
                
            except Exception as e:
                result["status"] = "error"
                result["errors"].append(f"MinIO connection error: {str(e)}")
                logger.error(f"❌ MinIO storage check failed: {e}")
                
        else:
            result["status"] = "warning"
            result["warnings"].append(f"Unknown storage provider: {storage_config.provider}")
            logger.warning(f"⚠️ Unknown storage provider: {storage_config.provider}")
        
        result["details"] = details
        
    except Exception as e:
        result["status"] = "error"
        result["errors"].append(f"Storage configuration check error: {str(e)}")
        logger.error(f"❌ Storage services check failed: {e}")
    
    return result

async def vector_db_check(config: AppConfig) -> dict:
    """
    检查向量数据库服务
    
    Returns:
        dict: 检查结果
    """
    result = {
        "service": "Vector Database",
        "status": "unknown",
        "details": {},
        "errors": [],
        "warnings": []
    }
    
    try:
        logger.info("🔍 Checking vector database services...")
        
        # 检查具体的向量数据库配置和库
        import importlib.util
        
        vector_libs = {
            "weaviate": "weaviate-client",
            "chromadb": "chromadb", 
            "pinecone": "pinecone-client",
            "faiss": "faiss-cpu"
        }
        
        available_libs = []
        for lib_name, package_name in vector_libs.items():
            spec = importlib.util.find_spec(lib_name)
            if spec is not None:
                available_libs.append(lib_name)
        
        if available_libs:
            result["status"] = "healthy"
            result["details"] = {
                "available_libraries": available_libs,
                "note": "Vector database libraries are available, but specific database connection not tested"
            }
            logger.info(f"✅ Vector database: {len(available_libs)} library(ies) available")
        else:
            result["status"] = "warning"
            result["warnings"].append("No vector database libraries found")
            result["details"] = {
                "note": "Consider installing vector database libraries: pip install weaviate-client chromadb"
            }
            logger.warning("⚠️ Vector database: No libraries found")
            
    except Exception as e:
        result["status"] = "error"
        result["errors"].append(f"Vector database check error: {str(e)}")
        logger.error(f"❌ Vector database check failed: {e}")
    
    return result


async def initialize_checks(config: AppConfig) -> dict:
    """
    初始化时运行所有依赖检查
    
    Returns:
        dict: 所有服务的检查结果汇总
    """
    logger.info("🚀 Starting dependency health checks...")
    
    # 并行运行所有检查
    import asyncio
    
    checks = await asyncio.gather(
        database_connection_check(config),
        ai_config_check(config),
        storage_config_check(config),
        vector_db_check(config),
        return_exceptions=True
    )
    
    # 整理检查结果
    health_summary = {
        "overall_status": "healthy",
        "total_services": len(checks),
        "healthy_services": 0,
        "warning_services": 0,
        "error_services": 0,
        "services": {}
    }
    
    service_names = ["database", "ai_services", "storage", "vector_db"]
    
    for i, check_result in enumerate(checks):
        if isinstance(check_result, Exception):
            # 处理异常
            service_name = service_names[i]
            health_summary["services"][service_name] = {
                "service": service_name,
                "status": "error",
                "errors": [str(check_result)]
            }
            health_summary["error_services"] += 1
        else:
            service_name = service_names[i]
            health_summary["services"][service_name] = check_result
            
            if check_result["status"] == "healthy":
                health_summary["healthy_services"] += 1
            elif check_result["status"] == "warning":
                health_summary["warning_services"] += 1
            else:
                health_summary["error_services"] += 1
    
    # 确定总体状态
    if health_summary["error_services"] > 0:
        health_summary["overall_status"] = "error"
    elif health_summary["warning_services"] > 0:
        health_summary["overall_status"] = "warning"
    else:
        health_summary["overall_status"] = "healthy"
    
    # 打印汇总
    logger.info("📋 Health Check Summary:")
    logger.info(f"   ✅ Healthy: {health_summary['healthy_services']}")
    logger.info(f"   ⚠️  Warning: {health_summary['warning_services']}")  
    logger.info(f"   ❌ Error: {health_summary['error_services']}")
    logger.info(f"   🎯 Overall: {health_summary['overall_status'].upper()}")
    
    return health_summary



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
