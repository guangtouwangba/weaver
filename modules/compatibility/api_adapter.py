"""
API适配器

将新的模块化API适配为原有的DDD架构接口，保持向后兼容性。
"""

import logging
from typing import List, Dict, Any, Optional, AsyncIterator
from datetime import datetime

# 注意：RagAPI已被新的api_router替代
# from ..api import api_router
from ..models import Document, ContentType, ChunkingStrategy

logger = logging.getLogger(__name__)


class APIAdapter:
    """
    API适配器，将模块化API包装为原有接口格式
    
    此适配器确保原有的API调用方式仍然可以工作，
    同时内部使用新的模块化架构。
    """
    
    def __init__(self):
        """
        初始化API适配器
        
        Args:
            rag_api: RAG API实例（可选，会自动创建）
        """
        # 新架构不再需要RagAPI实例
        # 改为使用Service层进行操作
        self._initialized = True
        self._initialized = False
        
        logger.info("API适配器初始化完成")
    
    async def initialize(self) -> None:
        """初始化适配器"""
        if not self._initialized:
            await self.rag_api.initialize()
            self._initialized = True
            logger.info("API适配器已初始化")
    
    # 兼容原有的文件上传和确认接口
    async def confirm_upload_completion(self, file_id: str, file_path: str, 
                                      metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        确认文件上传完成（兼容接口）
        
        此方法模拟原有的文件上传确认流程，
        实际上会触发新的文档处理流程。
        
        Args:
            file_id: 文件ID
            file_path: 文件路径
            metadata: 文件元数据
            
        Returns:
            Dict[str, Any]: 上传确认结果
        """
        try:
            await self.initialize()
            
            # 使用新的API处理文件
            result = await self.rag_api.process_file(
                file_path=file_path,
                metadata=metadata or {}
            )
            
            # 转换为原有接口格式
            return {
                "file_id": file_id,
                "status": "confirmed" if result["success"] else "failed",
                "document_id": result.get("document_id"),
                "processing_time": result.get("processing_time_ms", 0),
                "chunks_created": result.get("chunks_created", 0),
                "message": "File upload confirmed and processed successfully" if result["success"] else result.get("error", "Processing failed")
            }
            
        except Exception as e:
            logger.error(f"确认上传完成失败 {file_id}: {e}")
            return {
                "file_id": file_id,
                "status": "failed",
                "error": str(e),
                "message": "File upload confirmation failed"
            }
    
    # 兼容原有的知识库查询接口
    async def search_knowledge(self, query: str, limit: int = 10, 
                             filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        搜索知识库（兼容接口）
        
        Args:
            query: 搜索查询
            limit: 结果数量限制
            filters: 搜索过滤器
            
        Returns:
            Dict[str, Any]: 搜索结果
        """
        try:
            await self.initialize()
            
            # 使用新的API进行搜索
            result = await self.rag_api.search(
                query=query,
                limit=limit,
                **(filters or {})
            )
            
            # 转换为原有接口格式
            return {
                "query": result["query"],
                "results": [
                    {
                        "id": item["chunk_id"],
                        "content": item["content"],
                        "score": item["score"],
                        "document_id": item["document_id"],
                        "metadata": item["metadata"]
                    }
                    for item in result["results"]
                ],
                "total": result["total_results"],
                "search_time": result["search_time_ms"],
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"知识库搜索失败: {e}")
            return {
                "query": query,
                "results": [],
                "total": 0,
                "status": "failed",
                "error": str(e)
            }
    
    # 兼容原有的文档管理接口
    async def get_document_info(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        获取文档信息（兼容接口）
        
        Args:
            document_id: 文档ID
            
        Returns:
            Optional[Dict[str, Any]]: 文档信息
        """
        try:
            await self.initialize()
            
            document = await self.rag_api.get_document(document_id)
            
            if not document:
                return None
            
            # 转换为原有接口格式
            return {
                "id": document["id"],
                "title": document["title"],
                "content_type": document["content_type"],
                "file_size": document["file_size"],
                "source_path": document["source_path"],
                "created_at": document["created_at"],
                "updated_at": document["updated_at"],
                "metadata": document["metadata"],
                "tags": document["tags"],
                "status": "active"
            }
            
        except Exception as e:
            logger.error(f"获取文档信息失败 {document_id}: {e}")
            return None
    
    async def delete_document_by_id(self, document_id: str) -> Dict[str, Any]:
        """
        删除文档（兼容接口）
        
        Args:
            document_id: 文档ID
            
        Returns:
            Dict[str, Any]: 删除结果
        """
        try:
            await self.initialize()
            
            success = await self.rag_api.delete_document(document_id)
            
            return {
                "document_id": document_id,
                "status": "deleted" if success else "failed",
                "success": success,
                "message": "Document deleted successfully" if success else "Failed to delete document"
            }
            
        except Exception as e:
            logger.error(f"删除文档失败 {document_id}: {e}")
            return {
                "document_id": document_id,
                "status": "failed",
                "success": False,
                "error": str(e),
                "message": "Document deletion failed"
            }
    
    # 兼容原有的主题和会话接口
    async def create_topic(self, title: str, description: str = "", 
                          metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        创建主题（兼容接口）
        
        Args:
            title: 主题标题
            description: 主题描述
            metadata: 主题元数据
            
        Returns:
            Dict[str, Any]: 创建结果
        """
        # 在新架构中，主题概念被文档和标签替代
        # 这里创建一个虚拟主题ID
        topic_id = f"topic_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        return {
            "id": topic_id,
            "title": title,
            "description": description,
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat(),
            "status": "created",
            "message": "Topic created (mapped to document tags in new architecture)"
        }
    
    async def get_topic_documents(self, topic_id: str) -> List[Dict[str, Any]]:
        """
        获取主题下的文档（兼容接口）
        
        Args:
            topic_id: 主题ID
            
        Returns:
            List[Dict[str, Any]]: 文档列表
        """
        # 在新架构中，通过标签搜索相关文档
        try:
            await self.initialize()
            
            # 使用标签搜索相关文档
            # 这里简化处理，实际可以根据topic_id的映射关系查找
            result = await self.rag_api.search(
                query=f"topic:{topic_id}",
                limit=100
            )
            
            # 提取唯一的文档ID
            unique_doc_ids = list(set(item["document_id"] for item in result["results"]))
            
            # 获取完整文档信息
            documents = []
            for doc_id in unique_doc_ids:
                doc_info = await self.get_document_info(doc_id)
                if doc_info:
                    documents.append(doc_info)
            
            return documents
            
        except Exception as e:
            logger.error(f"获取主题文档失败 {topic_id}: {e}")
            return []
    
    # 兼容原有的系统状态接口
    async def get_system_health(self) -> Dict[str, Any]:
        """
        获取系统健康状态（兼容接口）
        
        Returns:
            Dict[str, Any]: 系统健康状态
        """
        try:
            await self.initialize()
            
            status = await self.rag_api.get_status()
            
            # 转换为原有接口格式
            overall_healthy = status["components"].get("overall_status") == "healthy"
            
            return {
                "status": "healthy" if overall_healthy else "degraded",
                "timestamp": status["timestamp"],
                "components": {
                    "database": {"status": "healthy"},  # 模拟数据库状态
                    "storage": status["components"].get("storage_backend", {"status": "not_configured"}),
                    "search": status["components"].get("search_backend", {"status": "not_configured"}),
                    "file_processing": status["components"].get("document_processor", {"status": "healthy"}),
                    "api": status["api"]
                },
                "metrics": {
                    "documents_processed": status["components"].get("orchestrator", {}).get("cached_documents", 0),
                    "uptime_seconds": 0,  # 可以添加实际的运行时间计算
                    "memory_usage": "unknown"  # 可以添加实际的内存使用统计
                }
            }
            
        except Exception as e:
            logger.error(f"获取系统健康状态失败: {e}")
            return {
                "status": "error",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "components": {},
                "metrics": {}
            }
    
    # 兼容原有的配置接口
    async def get_supported_file_types(self) -> List[str]:
        """
        获取支持的文件类型（兼容接口）
        
        Returns:
            List[str]: 支持的文件类型列表
        """
        try:
            await self.initialize()
            
            formats = await self.rag_api.get_supported_formats()
            
            # 转换为MIME类型格式（如果需要）
            mime_types = []
            for fmt in formats:
                if fmt == '.txt':
                    mime_types.append('text/plain')
                elif fmt == '.pdf':
                    mime_types.append('application/pdf')
                elif fmt == '.doc':
                    mime_types.append('application/msword')
                elif fmt == '.docx':
                    mime_types.append('application/vnd.openxmlformats-officedocument.wordprocessingml.document')
                elif fmt == '.html':
                    mime_types.append('text/html')
                elif fmt == '.md':
                    mime_types.append('text/markdown')
                elif fmt == '.json':
                    mime_types.append('application/json')
                elif fmt == '.csv':
                    mime_types.append('text/csv')
                else:
                    mime_types.append(f'application/{fmt[1:]}')
            
            return mime_types
            
        except Exception as e:
            logger.error(f"获取支持文件类型失败: {e}")
            return ['text/plain', 'application/pdf', 'text/html']  # 默认支持的类型
