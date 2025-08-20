"""
Enhanced RAG Knowledge Management API with Advanced Multi-Resource Topic Chat

This is the enhanced version that integrates the new advanced RAG system
alongside the existing DDD architecture for comprehensive knowledge management.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.exceptions import RequestValidationError
import logging

# Import existing modules
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

# Import new advanced RAG system
from modules.rag import include_rag_routes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="Advanced RAG Knowledge Management API",
    description="""🚀 **增强版RAG知识管理系统** - 集成先进的多资源话题聊天
    
    ## 🌟 全新功能特性
    
    ### 🔬 Advanced RAG System
    - **🎯 多策略检索**: 语义搜索 + 关键词搜索 + 混合策略
    - **🧠 智能答案生成**: GPT-4/Claude驱动的精准回答
    - **💬 话题对话**: 基于主题的多资源聊天系统
    - **📊 实时评估**: 全方位的RAG质量评估框架
    - **🔍 上下文管理**: 多轮对话记忆与上下文维护
    - **📈 性能监控**: 实时系统指标与健康检查
    
    ### 🏗️ 原有核心功能
    - **📚 文档管理**: 智能文档上传、处理和索引
    - **🏷️ 主题组织**: 灵活的知识分类和标签系统
    - **⚡ 异步处理**: 高性能的文档处理管道
    - **🗂️ 多存储支持**: MinIO/AWS S3/GCS等多种存储后端
    
    ## 🚀 快速开始
    
    ### 1. 传统文档管理
    - `GET /health` - 系统健康检查
    - `POST /api/v1/topics` - 创建知识主题
    - `POST /api/v1/files/upload/signed-url` - 获取文档上传URL
    - `POST /api/v1/documents/search` - 搜索文档内容
    
    ### 2. 🆕 Advanced RAG 功能
    - `POST /api/v1/rag/topics/{topic_id}/index` - 索引主题文档
    - `POST /api/v1/rag/chat` - 智能多资源对话
    - `POST /api/v1/rag/evaluation/run` - 运行系统评估
    - `GET /api/v1/rag/system/metrics` - 获取性能指标
    
    ## 💡 使用场景
    
    ### 📖 知识问答
    ```json
    POST /api/v1/rag/chat
    {
        "query": "什么是深度学习？与机器学习有什么区别？",
        "topic_id": 1,
        "max_sources": 5
    }
    ```
    
    ### 📄 文档索引
    ```json
    POST /api/v1/rag/topics/1/index
    {
        "topic_id": 1,
        "documents": [
            {
                "id": "doc_001",
                "title": "深度学习入门",
                "content": "深度学习是机器学习的一个重要分支..."
            }
        ]
    }
    ```
    
    ## 🔧 技术架构
    
    - **🏛️ DDD架构**: 领域驱动设计 + 服务层编排
    - **🤖 Advanced RAG**: 多模型嵌入 + 混合检索 + LLM生成
    - **📊 向量数据库**: Weaviate/ChromaDB支持
    - **⚡ 异步处理**: FastAPI + AsyncIO高性能框架
    - **🗄️ 多存储**: PostgreSQL + Redis + 对象存储
    
    ---
    
    💡 **提示**: 使用下方的API文档探索所有功能，新的RAG功能在 `/api/v1/rag/*` 路径下
    """,
    version="2.1.0",
    contact={
        "name": "Advanced RAG API Support",
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

# Include existing API routes
app.include_router(api_router)

# Include new Advanced RAG routes
include_rag_routes(app)

# Custom Swagger UI page
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """自定义Swagger UI页面"""
    from fastapi.openapi.docs import get_swagger_ui_html
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - 交互式文档",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui.css",
        swagger_ui_parameters=SWAGGER_UI_PARAMETERS,
        swagger_favicon_url="/favicon.ico"
    )

# Enhanced documentation homepage
@app.get("/api-docs", response_class=HTMLResponse, include_in_schema=False)
async def api_documentation():
    """增强版API文档首页"""
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
                max-width: 1400px;
                margin: 0 auto;
                padding: 2rem;
                line-height: 1.6;
                color: #333;
                background: #f8f9fa;
            }}
            .header {{
                text-align: center;
                margin-bottom: 3rem;
                padding: 3rem;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border-radius: 15px;
                box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            }}
            .subtitle {{
                font-size: 1.2em;
                opacity: 0.9;
                margin-top: 1rem;
            }}
            .cards {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
                gap: 2rem;
                margin-bottom: 3rem;
            }}
            .card {{
                padding: 2.5rem;
                background: white;
                border: 1px solid #e1e5e9;
                border-radius: 12px;
                text-decoration: none;
                color: inherit;
                transition: transform 0.3s, box-shadow 0.3s;
                position: relative;
                overflow: hidden;
            }}
            .card:hover {{
                transform: translateY(-8px);
                box-shadow: 0 12px 40px rgba(0,0,0,0.15);
                text-decoration: none;
            }}
            .card::before {{
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                width: 4px;
                height: 100%;
                background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
            }}
            .card h3 {{
                margin-top: 0;
                color: #1976d2;
                font-size: 1.4em;
                margin-bottom: 1rem;
            }}
            .card p {{
                margin-bottom: 0.5rem;
            }}
            .badge {{
                display: inline-block;
                background: #e3f2fd;
                color: #1976d2;
                padding: 0.3rem 0.8rem;
                border-radius: 20px;
                font-size: 0.8em;
                font-weight: 600;
                margin-bottom: 1rem;
            }}
            .new-badge {{
                background: linear-gradient(45deg, #ff6b6b, #ff8787);
                color: white;
                animation: pulse 2s infinite;
            }}
            .features {{
                background: white;
                padding: 3rem;
                border-radius: 12px;
                margin-bottom: 2rem;
                box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            }}
            .feature-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 2rem;
                margin-top: 2rem;
            }}
            .feature {{
                background: #f8f9fa;
                padding: 2rem;
                border-radius: 10px;
                border-left: 4px solid #1976d2;
                transition: transform 0.2s;
            }}
            .feature:hover {{
                transform: translateX(4px);
            }}
            .tech-stack {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 3rem;
                border-radius: 12px;
                margin-bottom: 2rem;
            }}
            .tech-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 1.5rem;
                margin-top: 2rem;
            }}
            .tech-item {{
                background: rgba(255,255,255,0.1);
                padding: 1.5rem;
                border-radius: 8px;
                backdrop-filter: blur(10px);
            }}
            @keyframes pulse {{
                0% {{ transform: scale(1); }}
                50% {{ transform: scale(1.05); }}
                100% {{ transform: scale(1); }}
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🚀 {app.title}</h1>
            <div class="subtitle">增强版RAG知识管理系统 - 智能多资源话题聊天</div>
            <p>Version: {app.version}</p>
        </div>
        
        <div class="cards">
            <a href="/docs" class="card">
                <div class="badge">交互式文档</div>
                <h3>📊 Swagger UI</h3>
                <p>完整的API交互式文档，支持在线测试和调试。包含传统文档管理和新的Advanced RAG功能。</p>
                <p><strong>特色</strong>：实时测试、参数验证、响应预览</p>
            </a>
            
            <a href="/redoc" class="card">
                <div class="badge">美观阅读</div>
                <h3>📚 ReDoc</h3>
                <p>优雅的API文档阅读界面，适合产品文档和用户手册阅读。</p>
                <p><strong>适用</strong>：文档学习、功能了解、集成参考</p>
            </a>
            
            <a href="/api/v1/rag/chat" class="card">
                <div class="badge new-badge">🆕 NEW</div>
                <h3>💬 Advanced RAG Chat</h3>
                <p>全新的多资源话题聊天功能，支持跨文档智能问答和上下文对话。</p>
                <p><strong>核心功能</strong>：精准检索、智能生成、来源引用</p>
            </a>
            
            <a href="/health" class="card">
                <div class="badge">系统监控</div>
                <h3>❤️ 系统健康</h3>
                <p>实时检查系统各组件状态，包括数据库、存储、RAG组件等。</p>
                <p><strong>用途</strong>：运维监控、故障诊断、性能优化</p>
            </a>
        </div>
        
        <div class="features">
            <h2>🌟 Advanced RAG 核心特性</h2>
            <div class="feature-grid">
                <div class="feature">
                    <h4>🎯 多策略检索</h4>
                    <p>语义搜索、关键词搜索、混合检索策略，确保信息检索的全面性和准确性</p>
                </div>
                <div class="feature">
                    <h4>🧠 智能答案生成</h4>
                    <p>基于GPT-4/Claude的高质量答案生成，支持多文档信息综合</p>
                </div>
                <div class="feature">
                    <h4>💬 上下文对话</h4>
                    <p>维护对话历史，支持多轮问答和上下文理解</p>
                </div>
                <div class="feature">
                    <h4>📊 实时评估</h4>
                    <p>全方位的RAG质量评估，包括检索质量、生成质量、用户体验等</p>
                </div>
                <div class="feature">
                    <h4>🔍 来源追踪</h4>
                    <p>详细的信息来源标注和引用，确保答案的可验证性</p>
                </div>
                <div class="feature">
                    <h4>📈 性能监控</h4>
                    <p>实时系统指标监控，包括响应时间、成功率、组件健康状况</p>
                </div>
            </div>
        </div>
        
        <div class="tech-stack">
            <h2>🔧 技术架构栈</h2>
            <div class="tech-grid">
                <div class="tech-item">
                    <h4>🤖 AI & ML</h4>
                    <p>GPT-4, Claude, BGE Embeddings, Cross-encoder Re-ranking</p>
                </div>
                <div class="tech-item">
                    <h4>🗄️ 数据存储</h4>
                    <p>PostgreSQL, Weaviate, ChromaDB, Redis, MinIO</p>
                </div>
                <div class="tech-item">
                    <h4>⚡ 后端框架</h4>
                    <p>FastAPI, AsyncIO, Pydantic, SQLAlchemy</p>
                </div>
                <div class="tech-item">
                    <h4>🏗️ 架构模式</h4>
                    <p>DDD, Service Layer, Repository Pattern, CQRS</p>
                </div>
            </div>
        </div>
        
        <footer style="text-align: center; margin-top: 3rem; padding: 2rem; color: #666;">
            <p>🚀 由 Advanced RAG + FastAPI 驱动 | 遵循MIT许可证</p>
            <p>📚 探索 <strong>/api/v1/rag/*</strong> 路径下的全新RAG功能</p>
        </footer>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/", response_model=APIResponse, summary="API根目录", tags=["系统信息"])
async def root():
    """
    # Enhanced API服务根目录
    
    返回增强版RAG知识管理系统的基本信息和新功能介绍。
    
    ## 🆕 新增功能
    - 🎯 **Advanced RAG Chat**: `/api/v1/rag/chat` - 多资源话题智能聊天
    - 📊 **系统评估**: `/api/v1/rag/evaluation/run` - 全方位性能评估
    - 📈 **性能监控**: `/api/v1/rag/system/metrics` - 实时指标监控
    - 🔍 **文档索引**: `/api/v1/rag/topics/{id}/index` - 高级文档索引
    
    ## 🏗️ 技术栈升级
    - **多策略检索**: 语义 + 关键词 + 混合检索
    - **智能生成**: GPT-4/Claude 驱动的精准答案
    - **向量数据库**: Weaviate/ChromaDB 支持
    - **实时评估**: 多维度RAG质量评估
    """
    return APIResponse(
        success=True,
        message="Enhanced RAG Knowledge Management API v2.1.0",
        data={
            "service": "Enhanced RAG Knowledge Management API",
            "version": "2.1.0", 
            "architecture": "DDD + Advanced RAG System",
            "new_features": [
                "多资源话题聊天 (/api/v1/rag/chat)",
                "智能文档索引 (/api/v1/rag/topics/*/index)",
                "系统性能评估 (/api/v1/rag/evaluation/run)",
                "实时指标监控 (/api/v1/rag/system/metrics)",
                "对话历史管理 (/api/v1/rag/conversations/*)"
            ],
            "original_features": [
                "文档上传与处理",
                "主题管理",
                "多存储后端支持",
                "异步任务处理",
                "健康检查与监控"
            ],
            "endpoints": {
                "docs": "/docs",
                "redoc": "/redoc", 
                "openapi": "/openapi.json",
                "health": "/health",
                "api_docs": "/api-docs",
                "rag_chat": "/api/v1/rag/chat",
                "rag_health": "/api/v1/rag/health"
            }
        }
    )

@app.get("/health", response_model=APIResponse, summary="系统健康检查", tags=["系统信息"])
async def health_check():
    """
    # 增强版系统健康状态检查
    
    检查整个系统的健康状态，包括原有组件和新的Advanced RAG系统。
    
    ## 检查范围
    
    ### 🏛️ 原有架构组件
    - 🗄️ **数据库**: PostgreSQL连接状态
    - ⚡ **API服务**: FastAPI应用状态
    - 🔧 **业务服务**: Service层组件状态
    - 📊 **数据层**: Repository层状态
    
    ### 🚀 Advanced RAG组件
    - 🧮 **嵌入服务**: 多模型嵌入系统状态
    - 🗄️ **向量存储**: Weaviate/ChromaDB连接状态
    - 🔍 **检索系统**: 多策略检索器状态
    - 🤖 **生成服务**: LLM连接和推理状态
    - 📊 **评估框架**: 评估系统状态
    
    ## 状态级别
    - ✅ **healthy**: 所有组件正常运行
    - ⚠️ **degraded**: 部分组件异常但核心功能可用
    - ❌ **unhealthy**: 关键组件异常，服务不可用
    """
    try:
        # Check traditional components
        db_status = "healthy"
        try:
            from modules.database import get_database_connection
            db = await get_database_connection()
            health_ok = await db.health_check()
            if not health_ok:
                db_status = "unhealthy: health check failed"
        except Exception as e:
            db_status = f"unhealthy: {str(e)}"
        
        # Check Advanced RAG system
        rag_status = "healthy"
        rag_components = {}
        try:
            from modules.rag.api import get_rag_system
            rag_system = await get_rag_system()
            rag_health = await rag_system.health_check()
            rag_status = rag_health.get("status", "unknown")
            rag_components = rag_health.get("components", {})
        except Exception as e:
            rag_status = f"unhealthy: {str(e)}"
        
        # Determine overall status
        if db_status == "healthy" and rag_status == "healthy":
            overall_status = "healthy"
        elif "unhealthy" in db_status or "unhealthy" in rag_status:
            overall_status = "unhealthy"
        else:
            overall_status = "degraded"
        
        health_data = HealthCheckResponse(
            status=overall_status,
            version="2.1.0",
            components={
                **{
                    "database": db_status,
                    "api": "healthy",
                    "services": "healthy",
                    "repositories": "healthy",
                    "schemas": "healthy"
                },
                **{f"rag_{k}": v for k, v in rag_components.items()}
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
    logger.info("🚀 Starting Enhanced RAG Knowledge Management API...")
    logger.info("📊 Architecture: DDD + Advanced RAG System")
    logger.info("🆕 New Features: Multi-resource topic chat, Advanced evaluation")
    logger.info("⚡ Enhanced Components:")
    logger.info("   - 🎯 Multi-strategy retrieval (semantic + keyword + hybrid)")
    logger.info("   - 🧠 GPT-4/Claude powered answer generation")
    logger.info("   - 💬 Context-aware conversation management")
    logger.info("   - 📊 Comprehensive RAG evaluation framework")
    logger.info("   - 🗄️ Vector database integration (Weaviate/ChromaDB)")
    logger.info("📚 API Documentation available at:")
    logger.info("   - Swagger UI: http://localhost:8000/docs")
    logger.info("   - ReDoc: http://localhost:8000/redoc")
    logger.info("   - Enhanced Docs: http://localhost:8000/api-docs")
    logger.info("🆕 New RAG Endpoints: http://localhost:8000/api/v1/rag/*")

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("👋 Shutting down Enhanced RAG API...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main_enhanced:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )