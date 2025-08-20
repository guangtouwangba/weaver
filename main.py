"""
简化的RAG系统主应用

只使用模块化架构，不依赖复杂的DDD结构。
"""

import logging
import sys
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional

from fastapi import FastAPI, Request, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

# 模块化API导入
from modules import RagAPI, APIAdapter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("启动RAG API应用...")
    
    # 初始化模块化API
    app.state.rag_api = RagAPI()
    app.state.api_adapter = APIAdapter(app.state.rag_api)
    
    await app.state.rag_api.initialize()
    await app.state.api_adapter.initialize()
    
    logger.info("RAG API应用启动成功")
    
    yield
    
    logger.info("关闭RAG API应用...")
    logger.info("RAG API应用关闭完成")


# 创建FastAPI应用
app = FastAPI(
    title="RAG API - 模块化版本",
    description="基于模块化架构的简化RAG系统API",
    version="2.0.0",
    lifespan=lifespan
)

# 添加中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    logger.error(f"全局异常: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": str(exc),
            "path": str(request.url.path),
            "method": request.method
        }
    )


# ===== 统一V1 API端点 =====

@app.post("/api/v1/documents/process")
async def process_document(
    file_path: str,
    chunking_strategy: str = "fixed_size",
    chunk_size: int = 1000,
    chunk_overlap: int = 200
):
    """处理文档"""
    try:
        result = await app.state.rag_api.process_file(
            file_path=file_path,
            chunking_strategy=chunking_strategy,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        return result
    except Exception as e:
        logger.error(f"处理文档失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/documents/search")
async def search_documents(query: str, limit: int = 10):
    """搜索文档"""
    try:
        result = await app.state.rag_api.search(query=query, limit=limit)
        return result
    except Exception as e:
        logger.error(f"搜索失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/documents/{document_id}")
async def get_document(document_id: str):
    """获取文档详情"""
    try:
        result = await app.state.rag_api.get_document(document_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Document not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文档失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v1/documents/{document_id}")
async def delete_document(document_id: str):
    """删除文档"""
    try:
        success = await app.state.rag_api.delete_document(document_id)
        return {"success": success, "message": "Document deleted" if success else "Failed to delete"}
    except Exception as e:
        logger.error(f"删除文档失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/status")
async def get_status():
    """获取系统状态"""
    try:
        status = await app.state.rag_api.get_status()
        return status
    except Exception as e:
        logger.error(f"获取状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/formats")
async def get_supported_formats():
    """获取支持的文件格式"""
    try:
        formats = await app.state.rag_api.get_supported_formats()
        return {"supported_formats": formats}
    except Exception as e:
        logger.error(f"获取支持格式失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== 主题和资源管理API =====

@app.get("/api/v1/topics")
async def list_topics(page: int = 1, page_size: int = 20):
    """获取主题列表"""
    try:
        # 模拟主题列表
        topics = [
            {
                "id": i,
                "name": f"主题 {i}",
                "description": f"这是第 {i} 个测试主题",
                "created_at": "2025-08-20T02:00:00Z",
                "updated_at": "2025-08-20T02:00:00Z",
                "file_count": i * 2,
                "status": "active"
            }
            for i in range(1, 11)
        ]
        return {
            "topics": topics,
            "total": len(topics),
            "page": page,
            "page_size": page_size,
            "has_next": False
        }
    except Exception as e:
        logger.error(f"获取主题列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/topics/{topic_id}")
async def get_topic(topic_id: int):
    """获取主题详情"""
    try:
        # 模拟主题详情
        topic = {
            "id": topic_id,
            "name": f"主题 {topic_id}",
            "description": f"这是第 {topic_id} 个测试主题的详细描述",
            "created_at": "2025-08-20T02:00:00Z",
            "updated_at": "2025-08-20T02:00:00Z",
            "file_count": topic_id * 2,
            "status": "active",
            "tags": ["测试", "演示"],
            "metadata": {
                "total_size": f"{topic_id * 1024}KB",
                "last_processed": "2025-08-20T02:00:00Z"
            }
        }
        return topic
    except Exception as e:
        logger.error(f"获取主题详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/topics/{topic_id}/files")
async def get_topic_files(
    topic_id: int,
    page: int = 1,
    page_size: int = 20,
    sort_by: str = "created_at",
    sort_order: str = "desc"
):
    """获取主题文件列表"""
    try:
        # 模拟文件列表
        files = [
            {
                "id": f"{topic_id}-{i}",
                "original_name": f"文档{i}.pdf",
                "content_type": "application/pdf",
                "file_size": 1024 * i,
                "created_at": "2025-08-20T02:00:00Z",
                "updated_at": "2025-08-20T02:00:00Z",
                "status": "processed",
                "processing_status": "completed",
                "metadata": {
                    "pages": i * 2,
                    "language": "zh-CN"
                }
            }
            for i in range(1, 6)
        ]
        
        return {
            "files": files,
            "total": len(files),
            "page": page,
            "page_size": page_size,
            "has_next": False,
            "sort_by": sort_by,
            "sort_order": sort_order
        }
    except Exception as e:
        logger.error(f"获取主题文件列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/files/upload/signed-url")
async def generate_upload_url(request: Dict[str, Any] = Body(...)):
    """生成文件上传的签名URL"""
    try:
        from modules.file_upload import FileUploadService
        
        # 提取参数
        filename = request.get('filename')
        content_type = request.get('content_type')
        topic_id = request.get('topic_id')
        expires_in = request.get('expires_in', 3600)
        
        # 验证必需参数
        if not filename:
            raise HTTPException(status_code=400, detail="filename is required")
        if not content_type:
            raise HTTPException(status_code=400, detail="content_type is required")
        
        upload_service = FileUploadService()
        result = await upload_service.generate_upload_url(
            filename=filename,
            content_type=content_type,
            topic_id=topic_id,
            expires_in=expires_in
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成上传URL失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/files/confirm")
async def confirm_upload_completion(request: Dict[str, Any] = Body(...)):
    """确认文件上传完成"""
    try:
        from modules.file_upload import FileUploadService
        
        # 提取参数
        file_id = request.get('file_id')
        actual_size = request.get('actual_size')
        file_hash = request.get('file_hash')
        
        # 验证必需参数
        if not file_id:
            raise HTTPException(status_code=400, detail="file_id is required")
        
        upload_service = FileUploadService()
        result = await upload_service.confirm_upload(
            file_id=file_id,
            actual_size=actual_size,
            file_hash=file_hash
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"确认上传失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/knowledge/search")
async def search_knowledge(query: str, limit: int = 10):
    """搜索知识库"""
    try:
        result = await app.state.api_adapter.search_knowledge(query=query, limit=limit)
        return result
    except Exception as e:
        logger.error(f"知识库搜索失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/document_info/{document_id}")
async def get_document_info(document_id: str):
    """获取文档信息（旧格式兼容）"""
    try:
        result = await app.state.api_adapter.get_document_info(document_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Document not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文档信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v1/document_legacy/{document_id}")
async def delete_document_by_id(document_id: str):
    """删除文档（旧格式兼容）"""
    try:
        result = await app.state.api_adapter.delete_document_by_id(document_id)
        return result
    except Exception as e:
        logger.error(f"删除文档失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/topics")
async def create_topic(title: str, description: str = ""):
    """创建主题"""
    try:
        result = await app.state.api_adapter.create_topic(title=title, description=description)
        return result
    except Exception as e:
        logger.error(f"创建主题失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/resources/{resource_id}")
async def get_resource(resource_id: str):
    """获取资源详情"""
    try:
        # 模拟资源详情
        resource = {
            "id": resource_id,
            "name": f"资源-{resource_id[:8]}",
            "type": "document",
            "size": 2048,
            "created_at": "2025-08-20T02:00:00Z",
            "status": "active",
            "metadata": {
                "content_type": "application/pdf",
                "pages": 10
            }
        }
        return resource
    except Exception as e:
        logger.error(f"获取资源失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v1/resources/{resource_id}")
async def delete_resource(resource_id: str):
    """删除资源"""
    try:
        # 模拟删除操作
        return {
            "success": True,
            "message": "Resource soft deleted",
            "resource_id": resource_id,
            "deleted_at": "2025-08-20T02:00:00Z"
        }
    except Exception as e:
        logger.error(f"删除资源失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/health")
async def get_system_health():
    """系统健康检查"""
    try:
        result = await app.state.api_adapter.get_system_health()
        return result
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": "2025-08-20T02:00:00Z"
        }


# 基础端点
@app.get("/")
async def root():
    """根端点"""
    return {
        "message": "RAG API - 模块化版本",
        "version": "1.0.0",
        "architecture": "modular",
        "api_docs": "/docs",
        "api_base": "/api/v1/",
        "endpoints": {
            "documents": "/api/v1/documents/",
            "topics": "/api/v1/topics/",
            "resources": "/api/v1/resources/",
            "status": "/api/v1/status",
            "health": "/api/v1/health"
        }
    }


@app.get("/health")
async def basic_health():
    """基础健康检查"""
    return {
        "status": "healthy",
        "architecture": "modular",
        "version": "1.0.0",
        "api_base": "/api/v1/",
        "timestamp": "2025-08-20T02:00:00Z"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
