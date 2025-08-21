"""
API文档配置模块

配置Swagger UI和ReDoc的自定义样式和行为。
"""

from typing import Dict, Any

# Swagger UI自定义配置
SWAGGER_UI_PARAMETERS = {
    "deepLinking": True,
    "displayOperationId": True,
    "defaultModelsExpandDepth": 2,
    "defaultModelExpandDepth": 2,
    "displayRequestDuration": True,
    "docExpansion": "list",  # 展开操作列表
    "filter": True,  # 启用搜索过滤
    "showExtensions": True,
    "showCommonExtensions": True,
    "tryItOutEnabled": True,
    "persistAuthorization": True,  # 保持授权状态
    "layout": "BaseLayout",
    "supportedSubmitMethods": ["get", "post", "put", "delete", "patch"],
    # 自定义主题配色
    "theme": {
        "primaryColor": "#1976d2",
        "backgroundColor": "#fafafa"
    }
}

# OpenAPI文档的标签定义
OPENAPI_TAGS = [
    {
        "name": "系统信息",
        "description": "系统健康检查和基本信息接口"
    },
    {
        "name": "topics", 
        "description": "**🏷️ 主题管理**\n\n管理知识主题的创建、编辑、删除和查询。主题是组织文档和知识的容器。",
        "externalDocs": {
            "description": "主题管理最佳实践",
            "url": "https://docs.example.com/topics"
        }
    },
    {
        "name": "files",
        "description": "**📁 文件管理**\n\n处理文件上传、下载、存储和元数据管理。支持多种文件格式和存储后端。",
        "externalDocs": {
            "description": "文件上传指南",
            "url": "https://docs.example.com/files"
        }
    },
    {
        "name": "documents",
        "description": "**📄 文档处理**\n\n文档的解析、分块、向量化和智能搜索。核心的RAG功能实现。",
        "externalDocs": {
            "description": "RAG搜索技术文档", 
            "url": "https://docs.example.com/rag"
        }
    }
]

# 自定义CSS样式
CUSTOM_SWAGGER_CSS = """
<style>
.swagger-ui .topbar {
    background-color: #1976d2;
}
.swagger-ui .topbar .download-url-wrapper .select-label select {
    color: white;
}
.swagger-ui .info .title {
    color: #1976d2;
}
.swagger-ui .scheme-container {
    background: #f8f9fa;
    border: 1px solid #e9ecef;
    border-radius: 4px;
    padding: 10px;
}
.swagger-ui .opblock.opblock-post {
    border-color: #49cc90;
    background: rgba(73, 204, 144, 0.1);
}
.swagger-ui .opblock.opblock-get {
    border-color: #61affe;
    background: rgba(97, 175, 254, 0.1);
}
.swagger-ui .opblock.opblock-put {
    border-color: #fca130;
    background: rgba(252, 161, 48, 0.1);
}
.swagger-ui .opblock.opblock-delete {
    border-color: #f93e3e;
    background: rgba(249, 62, 62, 0.1);
}
.swagger-ui .opblock-summary {
    font-weight: 600;
}
.swagger-ui .opblock-description-wrapper p {
    margin: 0 0 10px 0;
}
</style>
"""

# 自定义JavaScript
CUSTOM_SWAGGER_JS = """
<script>
// 页面加载完成后的自定义逻辑
window.onload = function() {
    // 设置默认的服务器URL
    if (window.ui) {
        setTimeout(function() {
            const serverSelect = document.querySelector('.scheme-container select');
            if (serverSelect) {
                serverSelect.value = window.location.origin;
            }
        }, 1000);
    }
    
    // 添加快捷键支持
    document.addEventListener('keydown', function(e) {
        // Ctrl+F 打开搜索
        if (e.ctrlKey && e.key === 'f') {
            e.preventDefault();
            const filterInput = document.querySelector('.swagger-ui .filter input');
            if (filterInput) {
                filterInput.focus();
            }
        }
        // Ctrl+H 切换到主页
        if (e.ctrlKey && e.key === 'h') {
            e.preventDefault();
            window.location.href = '/';
        }
    });
};
</script>
"""

def get_openapi_config() -> Dict[str, Any]:
    """获取OpenAPI配置"""
    return {
        "title": "RAG Knowledge Management API",
        "description": """
# 🔍 RAG知识管理系统API

基于DDD架构和Service层编排的智能知识管理系统，提供文档上传、处理、向量化搜索等完整的RAG功能。

## 🚀 核心特性

- **📚 智能文档处理**: 支持PDF、Word、TXT等多种格式
- **🔍 语义搜索**: 基于向量相似度的智能内容检索
- **🏷️ 主题组织**: 灵活的知识分类和管理体系
- **⚡ 异步处理**: 高性能的非阻塞I/O操作
- **🔒 安全上传**: 基于签名URL的安全文件传输
- **📊 实时监控**: 完整的处理状态跟踪和错误处理

## 🛠️ 技术架构

- **后端框架**: FastAPI + SQLAlchemy + Pydantic
- **数据库**: PostgreSQL (关系数据) + Weaviate (向量数据)
- **存储**: MinIO/AWS S3/GCS (多后端支持)
- **缓存**: Redis (会话和队列管理)
- **搜索**: Elasticsearch + 向量数据库混合搜索

## 📖 使用指南

### 基本工作流程

1. **创建主题** → `POST /api/v1/topics`
2. **获取上传URL** → `POST /api/v1/files/upload/signed-url`
3. **上传文件** → 使用返回的签名URL
4. **确认上传** → `POST /api/v1/files/confirm`
5. **搜索内容** → `POST /api/v1/documents/search`

### 认证方式

系统支持多种认证方式：
- **API Key**: 在请求头中添加 `X-API-Key`
- **Bearer Token**: 标准的JWT令牌认证
- **OAuth2**: 支持第三方OAuth2提供商

### 错误处理

所有API响应都遵循统一的错误格式：
```json
{
  "success": false,
  "message": "错误描述",
  "error": {
    "code": "ERROR_CODE",
    "details": {}
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## 🔗 相关链接

- [API文档 (Swagger UI)](/docs)
- [API文档 (ReDoc)](/redoc)
- [OpenAPI规范](/openapi.json)
- [开发者文档](https://docs.example.com)
- [GitHub仓库](https://github.com/your-repo/research-agent-rag)

---

**💡 提示**: 使用右上角的搜索框可以快速找到所需的API端点。
        """,
        "version": "2.0.0",
        "contact": {
            "name": "RAG API技术支持",
            "url": "https://github.com/your-repo/research-agent-rag",
            "email": "support@example.com"
        },
        "license": {
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT"
        },
        "servers": [
            {
                "url": "http://localhost:8000",
                "description": "开发环境"
            },
            {
                "url": "https://api-staging.example.com", 
                "description": "测试环境"
            },
            {
                "url": "https://api.example.com",
                "description": "生产环境"
            }
        ],
        "tags": OPENAPI_TAGS
    }
