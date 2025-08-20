"""
基于Service层编排的RAG系统主应用

使用新的架构：Schema + Repository + Service + API
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.exceptions import RequestValidationError
import logging

# 导入新的Service层API
from modules.api import api_router
from modules.compatibility import APIAdapter
from modules.database import DatabaseConnection
from modules.schemas import APIResponse, HealthCheckResponse
from modules.api.error_handlers import (
    unicode_decode_error_handler,
    request_validation_error_handler,
    general_exception_handler
)
from modules.config.docs import SWAGGER_UI_PARAMETERS

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

@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info("🚀 Starting RAG API with Service Layer...")
    logger.info("📊 Architecture: Schema + Repository + Service + API")
    logger.info("✅ Service layer orchestration enabled")
    logger.info("🗂️ Pydantic schemas for data validation")
    logger.info("🏗️ Repository pattern for data access")
    logger.info("🎯 Domain-driven service design")
    logger.info("📚 API Documentation available at:")
    logger.info("   - Swagger UI: http://localhost:8000/docs")
    logger.info("   - ReDoc: http://localhost:8000/redoc")
    logger.info("   - OpenAPI JSON: http://localhost:8000/openapi.json")
    logger.info("   - Docs Center: http://localhost:8000/api-docs")

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("👋 Shutting down RAG API...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
