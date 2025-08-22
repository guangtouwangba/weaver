"""
API documentation configuration module

Configures custom styles and behaviors for Swagger UI and ReDoc.
"""

from typing import Dict, Any

# Swagger UI custom configuration
SWAGGER_UI_PARAMETERS = {
    "deepLinking": True,
    "displayOperationId": True,
    "defaultModelsExpandDepth": 2,
    "defaultModelExpandDepth": 2,
    "displayRequestDuration": True,
    "docExpansion": "list",  # Expand operation list
    "filter": True,  # Enable search filter
    "showExtensions": True,
    "showCommonExtensions": True,
    "tryItOutEnabled": True,
    "persistAuthorization": True,  # Maintain authorization state
    "layout": "BaseLayout",
    "supportedSubmitMethods": ["get", "post", "put", "delete", "patch"],
    # Custom theme colors
    "theme": {
        "primaryColor": "#1976d2",
        "backgroundColor": "#fafafa"
    }
}

# OpenAPI document tag definitions
OPENAPI_TAGS = [
    {
        "name": "System Info",
        "description": "System health checks and basic information interfaces"
    },
    {
        "name": "topics", 
        "description": "**🏷️ Topic Management**\n\nManage creation, editing, deletion, and querying of knowledge topics. Topics are containers for organizing documents and knowledge.",
        "externalDocs": {
            "description": "Topic Management Best Practices",
            "url": "https://docs.example.com/topics"
        }
    },
    {
        "name": "files",
        "description": "**📁 File Management**\n\nHandle file upload, download, storage, and metadata management. Supports multiple file formats and storage backends.",
        "externalDocs": {
            "description": "File Upload Guide",
            "url": "https://docs.example.com/files"
        }
    },
    {
        "name": "documents",
        "description": "**📄 Document Processing**\n\nDocument parsing, chunking, vectorization, and intelligent search. Core RAG functionality implementation.",
        "externalDocs": {
            "description": "RAG Search Technical Documentation", 
            "url": "https://docs.example.com/rag"
        }
    }
]

# Custom CSS styles
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

# Custom JavaScript
CUSTOM_SWAGGER_JS = """
<script>
// Custom logic after page loading
window.onload = function() {
    // Set default server URL
    if (window.ui) {
        setTimeout(function() {
            const serverSelect = document.querySelector('.scheme-container select');
            if (serverSelect) {
                serverSelect.value = window.location.origin;
            }
        }, 1000);
    }
    
    // Add keyboard shortcut support
    document.addEventListener('keydown', function(e) {
        // Ctrl+F to open search
        if (e.ctrlKey && e.key === 'f') {
            e.preventDefault();
            const filterInput = document.querySelector('.swagger-ui .filter input');
            if (filterInput) {
                filterInput.focus();
            }
        }
        // Ctrl+H to navigate to homepage
        if (e.ctrlKey && e.key === 'h') {
            e.preventDefault();
            window.location.href = '/';
        }
    });
};
</script>
"""

def get_openapi_config() -> Dict[str, Any]:
    """Get OpenAPI configuration"""
    return {
        "title": "RAG Knowledge Management API",
        "description": """
# 🔍 RAG Knowledge Management System API

Intelligent knowledge management system based on DDD architecture and Service layer orchestration, providing complete RAG functionality including document upload, processing, and vector search.

## 🚀 Core Features

- **📚 Intelligent Document Processing**: Support for PDF, Word, TXT and other formats
- **🔍 Semantic Search**: Intelligent content retrieval based on vector similarity
- **🏷️ Topic Organization**: Flexible knowledge classification and management system
- **⚡ Asynchronous Processing**: High-performance non-blocking I/O operations
- **🔒 Secure Upload**: Secure file transfer based on signed URLs
- **📊 Real-time Monitoring**: Complete processing status tracking and error handling

## 🛠️ Technical Architecture

- **Backend Framework**: FastAPI + SQLAlchemy + Pydantic
- **Database**: PostgreSQL (relational data) + Weaviate (vector data)
- **Storage**: MinIO/AWS S3/GCS (multi-backend support)
- **Cache**: Redis (session and queue management)
- **Search**: Elasticsearch + vector database hybrid search

## 📖 Usage Guide

### Basic Workflow

1. **Create Topic** → `POST /api/v1/topics`
2. **Get Upload URL** → `POST /api/v1/files/upload/signed-url`
3. **Upload File** → Use returned signed URL
4. **Confirm Upload** → `POST /api/v1/files/confirm`
5. **Search Content** → `POST /api/v1/documents/search`

### Authentication Methods

The system supports multiple authentication methods:
- **API Key**: Add `X-API-Key` in request headers
- **Bearer Token**: Standard JWT token authentication
- **OAuth2**: Support for third-party OAuth2 providers

### Error Handling

All API responses follow a unified error format:
```json
{
  "success": false,
  "message": "Error description",
  "error": {
    "code": "ERROR_CODE",
    "details": {}
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## 🔗 Related Links

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
