"""
Repository接口定义

定义数据访问层的抽象接口，遵循依赖倒置原则。
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar

# 泛型类型
EntityType = TypeVar("EntityType")
IdType = TypeVar("IdType")


class IBaseRepository(ABC, Generic[EntityType, IdType]):
    """Base repository接口"""

    @abstractmethod
    async def create(self, entity_data: Dict[str, Any]) -> EntityType:
        """创建实体"""
        pass

    @abstractmethod
    async def get_by_id(self, entity_id: IdType) -> Optional[EntityType]:
        """根据ID获取实体"""
        pass

    @abstractmethod
    async def update(
        self, entity_id: IdType, updates: Dict[str, Any]
    ) -> Optional[EntityType]:
        """更新实体"""
        pass

    @abstractmethod
    async def delete(self, entity_id: IdType) -> bool:
        """删除实体"""
        pass

    @abstractmethod
    async def list(
        self,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
    ) -> List[EntityType]:
        """列出实体"""
        pass


class ITopicRepository(IBaseRepository):
    """主题Repository接口"""

    @abstractmethod
    async def create_topic(self, name: str, description: str = "", **kwargs) -> Any:
        """创建主题"""
        pass

    @abstractmethod
    async def get_topic_by_id(self, topic_id: int) -> Optional[Any]:
        """根据ID获取主题"""
        pass

    @abstractmethod
    async def get_topics(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        user_id: Optional[int] = None,
    ) -> List[Any]:
        """获取主题列表"""
        pass

    @abstractmethod
    async def update_topic(self, topic_id: int, **updates) -> Optional[Any]:
        """更新主题"""
        pass

    @abstractmethod
    async def delete_topic(self, topic_id: int) -> bool:
        """删除主题"""
        pass

    @abstractmethod
    async def get_topics_by_user(self, user_id: int) -> List[Any]:
        """获取用户的主题列表"""
        pass

    @abstractmethod
    async def search_topics(self, query: str, limit: int = 10) -> List[Any]:
        """搜索主题"""
        pass


class IFileRepository(IBaseRepository):
    """文件Repository接口"""

    @abstractmethod
    async def create_file(
        self,
        file_id: str,
        original_name: str,
        content_type: str,
        file_size: int = 0,
        **kwargs,
    ) -> Any:
        """创建文件记录"""
        pass

    @abstractmethod
    async def get_file_by_id(self, file_id: str) -> Optional[Any]:
        """根据ID获取文件"""
        pass

    @abstractmethod
    async def get_files_by_topic(
        self,
        topic_id: int,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
    ) -> List[Any]:
        """获取主题下的文件列表"""
        pass

    @abstractmethod
    async def update_file_status(
        self,
        file_id: str,
        status: str,
        processing_status: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> Optional[Any]:
        """更新文件状态"""
        pass

    @abstractmethod
    async def soft_delete_file(self, file_id: str) -> bool:
        """软删除文件"""
        pass

    @abstractmethod
    async def get_files_by_status(self, status: str) -> List[Any]:
        """根据状态获取文件"""
        pass

    @abstractmethod
    async def get_files_by_user(self, user_id: int) -> List[Any]:
        """获取用户的文件列表"""
        pass

    @abstractmethod
    async def search_files(self, query: str, limit: int = 10) -> List[Any]:
        """搜索文件"""
        pass


class IDocumentRepository(IBaseRepository):
    """Document repository interface"""

    @abstractmethod
    async def create_document(
        self, document_id: str, title: str, content_type: str, **kwargs
    ) -> Any:
        """Create document"""
        pass

    @abstractmethod
    async def get_document_by_id(self, document_id: str) -> Optional[Any]:
        """根据IDGet document"""
        pass

    @abstractmethod
    async def create_document_chunk(
        self, document_id: str, content: str, chunk_index: int, **kwargs
    ) -> Any:
        """Create document块"""
        pass

    @abstractmethod
    async def search_documents(
        self, query: str, limit: int = 10, content_type: Optional[str] = None
    ) -> List[Any]:
        """搜索文档"""
        pass

    @abstractmethod
    async def delete_document(self, document_id: str) -> bool:
        """Delete document"""
        pass

    @abstractmethod
    async def get_documents_by_file(self, file_id: str) -> List[Any]:
        """根据文件IDGet document列表"""
        pass

    @abstractmethod
    async def get_document_chunks(self, document_id: str) -> List[Any]:
        """Get document的所有块"""
        pass

    @abstractmethod
    async def update_document_status(self, document_id: str, status: str) -> bool:
        """Update document状态"""
        pass
