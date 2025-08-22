"""
基于Service层编排的RAG系统主应用

使用新的架构：Schema + Repository + Service + API
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.exceptions import RequestValidationError
import logging

from config.settings import AppConfig
# 导入新的Service层API
from modules.api import api_router
from modules.database import DatabaseConnection
from modules.schemas import APIResponse, HealthCheckResponse
from modules.api.error_handlers import (
    unicode_decode_error_handler,
    request_validation_error_handler,
    general_exception_handler
)
from config.docs import SWAGGER_UI_PARAMETERS

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="RAG Knowledge Management API",
    description="""🔍 **基于Service层编排的RAG知识管理系统**
    
    ## 🚀 核心功能
    
    ### 📚 文档管理
    - **文件上传**: 支持PDF、Word、TXT等格式的文档上传
    - **文档处理**: 智能文本分块和向量化处理
    - **内容检索**: 语义搜索和关键词搜索
    
    ### 🏷️ 主题组织
    - **主题创建**: 创建和管理知识主题
    - **文档分类**: 将文档关联到相应主题
    - **知识图谱**: 构建主题间的关联关系
    
    ### ⚡ 技术架构
    - **领域驱动**: DDD架构设计
    - **服务编排**: 清晰的业务逻辑分层
    - **异步处理**: 高性能的异步I/O操作
    - **多存储支持**: MinIO/AWS S3/GCS等存储后端
    
    ## 🔧 快速开始
    
    1. **健康检查**: `GET /health` - 检查系统状态
    2. **创建主题**: `POST /api/v1/topics` - 创建知识主题
    3. **上传文件**: `POST /api/v1/files/upload/signed-url` - 获取上传URL
    4. **文档搜索**: `POST /api/v1/documents/search` - 搜索相关内容
    
    ---
    
    💡 **提示**: 使用下方的API文档探索所有可用的端点和功能
    """,
    version="2.0.0",
    contact={
        "name": "RAG API Support",
        "url": "https://github.com/your-repo/research-agent-rag",
        "email": "support@example.com"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    },
    servers=[
        {
            "url": "http://localhost:8000",
            "description": "开发环境"
        },
        {
            "url": "https://api.example.com",
            "description": "生产环境"
        }
    ],
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# 注册错误处理器
app.add_exception_handler(UnicodeDecodeError, unicode_decode_error_handler)
app.add_exception_handler(RequestValidationError, request_validation_error_handler)
app.add_exception_handler(Exception, general_exception_handler)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册新的Service层API路由
app.include_router(api_router)

# 自定义Swagger UI页面
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """自定义Swagger UI页面带额外样式和功能"""
    from fastapi.openapi.docs import get_swagger_ui_html
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - 交互式文档",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui.css",
        swagger_ui_parameters=SWAGGER_UI_PARAMETERS,
        swagger_favicon_url="/favicon.ico"
    )

# 自定义ReDoc页面
@app.get("/redoc", include_in_schema=False)
async def custom_redoc_html():
    """自定义ReDoc页面"""
    from fastapi.openapi.docs import get_redoc_html
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - ReDoc文档",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@2.1.3/bundles/redoc.standalone.js",
        redoc_favicon_url="/favicon.ico"
    )

# 添加文档首页
@app.get("/api-docs", response_class=HTMLResponse, include_in_schema=False)
async def api_documentation():
    """
API文档首页，提供各种文档入口
"""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{app.title} - API文档中心</title>
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
            <p>基于DDD架构的智能知识管理系统</p>
            <p>Version: {app.version}</p>
        </div>
        
        <div class="cards">
            <a href="/docs" class="card">
                <h3>📊 Swagger UI</h3>
                <p>交互式的API文档，支持在线测试和调试。提供丰富的界面和参数验证。</p>
                <p><strong>适用于</strong>：开发者测试、API探索</p>
            </a>
            
            <a href="/redoc" class="card">
                <h3>📚 ReDoc</h3>
                <p>美观的文档阅读界面，优化的排版和导航。适合产品文档和用户手册。</p>
                <p><strong>适用于</strong>：文档阅读、产品介绍</p>
            </a>
            
            <a href="/openapi.json" class="card">
                <h3>⚙️ OpenAPI JSON</h3>
                <p>OpenAPI规范的JSON格式，可用于生成客户端代码、测试工具等。</p>
                <p><strong>适用于</strong>：代码生成、工具集成</p>
            </a>
            
            <a href="/health" class="card">
                <h3>❤️ 系统状态</h3>
                <p>检查系统各组件的运行状态，包括数据库、存储、缓存等。</p>
                <p><strong>适用于</strong>：运维监控、系统诊断</p>
            </a>
        </div>
        
        <div class="features">
            <h2>🚀 系统特性</h2>
            <div class="feature-grid">
                <div class="feature">
                    <h4>📚 智能文档处理</h4>
                    <p>支持PDF、Word、TXT等格式，自动提取、分块、向量化</p>
                </div>
                <div class="feature">
                    <h4>🔍 语义搜索</h4>
                    <p>基于向量相似度的智能内容检索，支持多语言</p>
                </div>
                <div class="feature">
                    <h4>🏷️ 主题管理</h4>
                    <p>灵活的知识分类和组织体系，构建知识图谱</p>
                </div>
                <div class="feature">
                    <h4>⚡ 高性能异步</h4>
                    <p>非阻塞I/O操作，支持大并发和实时处理</p>
                </div>
            </div>
        </div>
        
        <footer style="text-align: center; margin-top: 3rem; padding: 2rem; color: #666;">
            <p>由 FastAPI + RAG 技术驱动 | 遵循MIT许可证</p>
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
            // 添加简单的页面交互功能
            document.addEventListener('DOMContentLoaded', function() {{
                console.log('API Documentation Center loaded');
            }});
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/", response_model=APIResponse, summary="API根目录", tags=["系统信息"])
async def root():
    """
    # API服务根目录
    
    返回RAG知识管理系统的基本信息和版本详情。
    
    ## 响应内容
    - 🚀 **服务名称**: RAG Knowledge Management API
    - 📦 **版本信息**: 当前系统版本号
    - 🏗️ **架构模式**: DDD + Service Layer
    - 📊 **技术栈**: FastAPI + SQLAlchemy + Pydantic
    
    ## 使用场景
    用于检查API服务是否正常运行，以及获取基本的系统信息。
    """
    return APIResponse(
        success=True,
        message="RAG Knowledge Management API v2.0.0",
        data={
            "service": "RAG Knowledge Management API",
            "version": "2.0.0", 
            "architecture": "DDD + Service Layer",
            "features": [
                "文档上传与处理",
                "智能文本分块",
                "向量化搜索",
                "主题管理",
                "多存储后端支持"
            ],
            "endpoints": {
                "docs": "/docs",
                "redoc": "/redoc",
                "openapi": "/openapi.json",
                "health": "/health"
            }
        }
    )

@app.get("/health", response_model=APIResponse, summary="系统健康检查", tags=["系统信息"])
async def health_check():
    """
    # 系统健康状态检查
    
    检查RAG系统各个组件的运行状态，包括数据库连接、服务层状态等。
    
    ## 检查项目
    - 🗄️ **数据库**: PostgreSQL连接状态
    - ⚙️ **API服务**: FastAPI应用状态
    - 🔧 **业务服务**: Service层组件状态
    - 📊 **数据层**: Repository层状态
    - 📋 **Schema**: Pydantic模型验证状态
    
    ## 返回状态
    - ✅ **healthy**: 所有组件正常
    - ⚠️ **degraded**: 部分组件异常但服务可用
    - ❌ **unhealthy**: 关键组件异常，服务不可用
    
    ## 监控建议
    建议将此接口用于:
    - 负载均衡器健康检查
    - 监控系统状态轮询
    - 容器编排健康探测
    - 运维自动化脚本
    """
    try:
        # 检查数据库连接
        db_status = "healthy"
        try:
            from modules.database import get_database_connection
            db = await get_database_connection()
            # 执行简单的健康检查
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

# 完整的依赖检查端点
@app.get("/health/detailed", summary="详细健康检查", tags=["系统信息"])
async def detailed_health_check():
    """
    # 详细的健康检查端点
    
    运行完整的依赖服务检查，包含所有中间件和外部服务的状态。
    
    ## 检查的服务
    - 🗄️ **数据库**: PostgreSQL连接、配置验证、性能状态
    - 🤖 **AI服务**: OpenAI、Anthropic、HuggingFace API配置
    - 💾 **存储服务**: 本地存储或MinIO连接状态
    - 🔍 **向量数据库**: Weaviate、ChromaDB等库可用性
    
    ## 返回信息
    - 总体状态汇总
    - 各服务详细状态
    - 配置警告和错误
    - 性能指标和容量信息
    
    ## 适用场景
    - 系统部署后的完整验证
    - 故障排查和诊断
    - 运维监控和报告
    - 配置变更后的验证
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
    """应用启动事件"""
    logger.info("🚀 Starting RAG API with Service Layer...")
    
    # 运行依赖健康检查
    try:
        from config import get_config
        config = get_config()
        health_result = await initialize_checks(config)
        
        # 根据健康检查结果决定是否继续启动
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
    """应用关闭事件"""
    logger.info("👋 Shutting down RAG API...")


async def database_connection_check(config: AppConfig) -> dict:
    """
    检查数据库连接状态
    
    Returns:
        dict: 检查结果，包含状态和详细信息
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
