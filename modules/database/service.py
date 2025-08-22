"""
数据库服务

为RagAPI提供数据库操作的高级接口。
"""

import logging
from typing import Any, Dict, List, Optional

# Repository imports
from ..repository import DocumentRepository, FileRepository, TopicRepository
from .connection import get_session

logger = logging.getLogger(__name__)


class DatabaseService:
    """数据库服务"""

    async def health_check(self) -> Dict[str, Any]:
        """数据库健康检查"""
        try:
            async with get_session() as session:
                await session.execute("SELECT 1")
                return {"status": "healthy", "message": "Database connection successful"}
        except Exception as e:
            logger.error(f"数据库健康检查失败: {e}")
            return {"status": "unhealthy", "message": f"Database connection failed: {str(e)}"}

    # ===== 主题管理 =====

    async def create_topic(self, name: str, description: str = "", **kwargs) -> Dict[str, Any]:
        """创建主题"""
        try:
            async with get_session() as session:
                repo = TopicRepository(session)
                topic = await repo.create_topic(name, description, **kwargs)

                return {
                    "id": topic.id,
                    "name": topic.name,
                    "description": topic.description,
                    "status": topic.status,
                    "created_at": topic.created_at.isoformat(),
                    "success": True,
                }
        except Exception as e:
            logger.error(f"创建主题失败: {e}")
            return {"success": False, "error": str(e)}

    async def get_topic(self, topic_id: int) -> Optional[Dict[str, Any]]:
        """获取主题详情"""
        try:
            async with get_session() as session:
                repo = TopicRepository(session)
                topic = await repo.get_topic_by_id(topic_id)

                if not topic:
                    return None

                return {
                    "id": topic.id,
                    "name": topic.name,
                    "description": topic.description,
                    "status": topic.status,
                    "category": topic.category,
                    "total_resources": topic.total_resources,
                    "total_conversations": topic.total_conversations,
                    "created_at": topic.created_at.isoformat(),
                    "updated_at": topic.updated_at.isoformat(),
                    "file_count": len(topic.files) if topic.files else 0,
                }
        except Exception as e:
            logger.error(f"获取主题失败: {e}")
            return None

    async def list_topics(self, page: int = 1, page_size: int = 20, **filters) -> Dict[str, Any]:
        """获取主题列表"""
        try:
            async with get_session() as session:
                repo = TopicRepository(session)
                topics = await repo.get_topics(page, page_size, **filters)
                total_count = await repo.get_topics_count(**filters)

                return {
                    "topics": [
                        {
                            "id": topic.id,
                            "name": topic.name,
                            "description": topic.description,
                            "status": topic.status,
                            "category": topic.category,
                            "total_resources": topic.total_resources,
                            "file_count": (
                                len([f for f in topic.files if not f.is_deleted])
                                if topic.files
                                else 0
                            ),
                            "created_at": topic.created_at.isoformat(),
                            "updated_at": topic.updated_at.isoformat(),
                        }
                        for topic in topics
                    ],
                    "page": page,
                    "page_size": page_size,
                    "total": total_count,
                    "has_next": (page * page_size) < total_count,
                }
        except Exception as e:
            logger.error(f"获取主题列表失败: {e}")
            return {"topics": [], "error": str(e)}

    async def update_topic(self, topic_id: int, **updates) -> Optional[Dict[str, Any]]:
        """更新主题"""
        try:
            async with get_session() as session:
                repo = TopicRepository(session)
                topic = await repo.update_topic(topic_id, **updates)

                if not topic:
                    return None

                return {
                    "id": topic.id,
                    "name": topic.name,
                    "description": topic.description,
                    "status": topic.status,
                    "category": topic.category,
                    "updated_at": topic.updated_at.isoformat(),
                    "success": True,
                }
        except Exception as e:
            logger.error(f"更新主题失败: {e}")
            return {"success": False, "error": str(e)}

    async def delete_topic(self, topic_id: int) -> bool:
        """删除主题"""
        try:
            async with get_session() as session:
                repo = TopicRepository(session)
                return await repo.delete_topic(topic_id)
        except Exception as e:
            logger.error(f"删除主题失败: {e}")
            return False

    # ===== 文件管理 =====

    async def create_file(
        self, file_id: str, original_name: str, content_type: str, **kwargs
    ) -> Dict[str, Any]:
        """创建文件记录"""
        try:
            async with get_session() as session:
                repo = FileRepository(session)
                file_record = await repo.create_file(file_id, original_name, content_type, **kwargs)

                return {
                    "id": file_record.id,
                    "original_name": file_record.original_name,
                    "content_type": file_record.content_type,
                    "status": file_record.status,
                    "created_at": file_record.created_at.isoformat(),
                    "success": True,
                }
        except Exception as e:
            logger.error(f"创建文件记录失败: {e}")
            return {"success": False, "error": str(e)}

    async def get_file(self, file_id: str) -> Optional[Dict[str, Any]]:
        """获取文件详情"""
        try:
            async with get_session() as session:
                repo = FileRepository(session)
                file_record = await repo.get_file_by_id(file_id)

                if not file_record:
                    return None

                return {
                    "id": file_record.id,
                    "original_name": file_record.original_name,
                    "content_type": file_record.content_type,
                    "file_size": file_record.file_size,
                    "file_hash": file_record.file_hash,
                    "storage_bucket": file_record.storage_bucket,
                    "storage_key": file_record.storage_key,
                    "storage_url": file_record.storage_url,
                    "status": file_record.status,
                    "processing_status": file_record.processing_status,
                    "topic_id": file_record.topic_id,
                    "topic_name": file_record.topic.name if file_record.topic else None,
                    "created_at": file_record.created_at.isoformat(),
                    "updated_at": file_record.updated_at.isoformat(),
                }
        except Exception as e:
            logger.error(f"获取文件失败: {e}")
            return None

    async def list_topic_files(
        self, topic_id: int, page: int = 1, page_size: int = 20, **filters
    ) -> Dict[str, Any]:
        """获取主题文件列表"""
        try:
            async with get_session() as session:
                repo = FileRepository(session)
                files = await repo.get_files_by_topic(topic_id, page, page_size, **filters)

                return {
                    "files": [
                        {
                            "id": file.id,
                            "original_name": file.original_name,
                            "content_type": file.content_type,
                            "file_size": file.file_size,
                            "status": file.status,
                            "processing_status": file.processing_status,
                            "created_at": file.created_at.isoformat(),
                        }
                        for file in files
                    ],
                    "topic_id": topic_id,
                    "page": page,
                    "page_size": page_size,
                    "total": len(files),
                    "has_next": len(files) == page_size,
                }
        except Exception as e:
            logger.error(f"获取主题文件列表失败: {e}")
            return {"files": [], "error": str(e)}

    async def update_file_status(self, file_id: str, status: str, **kwargs) -> bool:
        """更新文件状态"""
        try:
            async with get_session() as session:
                repo = FileRepository(session)
                result = await repo.update_file_status(file_id, status, **kwargs)
                return result is not None
        except Exception as e:
            logger.error(f"更新文件状态失败: {e}")
            return False

    async def delete_file(self, file_id: str) -> bool:
        """删除文件"""
        try:
            async with get_session() as session:
                repo = FileRepository(session)
                return await repo.soft_delete_file(file_id)
        except Exception as e:
            logger.error(f"删除文件失败: {e}")
            return False

    # ===== 文档管理 =====

    async def create_document(
        self, document_id: str, title: str, content_type: str, **kwargs
    ) -> Dict[str, Any]:
        """创建文档"""
        try:
            async with get_session() as session:
                repo = DocumentRepository(session)
                document = await repo.create_document(document_id, title, content_type, **kwargs)

                return {
                    "id": document.id,
                    "title": document.title,
                    "content_type": document.content_type,
                    "status": document.status,
                    "created_at": document.created_at.isoformat(),
                    "success": True,
                }
        except Exception as e:
            logger.error(f"创建文档失败: {e}")
            return {"success": False, "error": str(e)}

    async def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """获取文档详情"""
        try:
            async with get_session() as session:
                repo = DocumentRepository(session)
                document = await repo.get_document_by_id(document_id)

                if not document:
                    return None

                return {
                    "id": document.id,
                    "title": document.title,
                    "content": document.content,
                    "content_type": document.content_type,
                    "file_id": document.file_id,
                    "file_path": document.file_path,
                    "file_size": document.file_size,
                    "status": document.status,
                    "chunks_count": len(document.chunks) if document.chunks else 0,
                    "created_at": document.created_at.isoformat(),
                    "updated_at": document.updated_at.isoformat(),
                }
        except Exception as e:
            logger.error(f"获取文档失败: {e}")
            return None

    async def search_documents(
        self, query: str, limit: int = 10, **filters
    ) -> List[Dict[str, Any]]:
        """搜索文档"""
        try:
            async with get_session() as session:
                repo = DocumentRepository(session)
                documents = await repo.search_documents(query, limit, **filters)

                return [
                    {
                        "id": doc.id,
                        "title": doc.title,
                        "content": (
                            doc.content[:200] + "..."
                            if doc.content and len(doc.content) > 200
                            else doc.content
                        ),
                        "content_type": doc.content_type,
                        "file_id": doc.file_id,
                        "relevance_score": 0.8,  # 简单的固定相关性分数
                        "created_at": doc.created_at.isoformat(),
                    }
                    for doc in documents
                ]
        except Exception as e:
            logger.error(f"搜索文档失败: {e}")
            return []

    async def delete_document(self, document_id: str) -> bool:
        """删除文档"""
        try:
            async with get_session() as session:
                repo = DocumentRepository(session)
                return await repo.delete_document(document_id)
        except Exception as e:
            logger.error(f"删除文档失败: {e}")
            return False
