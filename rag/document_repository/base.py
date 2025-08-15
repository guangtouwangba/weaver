"""
文档仓储基础接口
专注于文档级别的元数据管理、状态跟踪和查询
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..models import Document, DocumentStatus, SearchFilter
from .exceptions import DocumentRepositoryError


class BaseDocumentRepository(ABC):
    """文档仓储基类 - 专注文档级别管理"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化文档仓储
        
        Args:
            config: 配置参数
        """
        self.config = config or {}
    
    @abstractmethod
    async def save(self, document: Document) -> str:
        """
        保存文档（新增或更新）
        
        Args:
            document: 文档对象
            
        Returns:
            str: 文档ID
            
        Raises:
            DocumentRepositoryError: 保存失败
        """
        pass
    
    @abstractmethod
    async def find_by_id(self, document_id: str) -> Optional[Document]:
        """
        根据ID查找文档
        
        Args:
            document_id: 文档ID
            
        Returns:
            Optional[Document]: 文档对象，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    async def find_by_status(self, status: DocumentStatus) -> List[Document]:
        """
        根据状态查找文档
        
        Args:
            status: 文档状态
            
        Returns:
            List[Document]: 文档列表
        """
        pass
    
    @abstractmethod
    async def search(self, 
                    query: str = "",
                    filters: Optional[SearchFilter] = None,
                    limit: int = 10,
                    offset: int = 0) -> List[Document]:
        """
        搜索文档（基于元数据、标题等）
        
        Args:
            query: 搜索查询
            filters: 搜索过滤器
            limit: 返回结果数量限制
            offset: 结果偏移量
            
        Returns:
            List[Document]: 匹配的文档列表
        """
        pass
    
    @abstractmethod
    async def update_status(self, document_id: str, status: DocumentStatus) -> bool:
        """
        更新文档状态
        
        Args:
            document_id: 文档ID
            status: 新状态
            
        Returns:
            bool: 更新是否成功
        """
        pass
    
    @abstractmethod
    async def delete(self, document_id: str) -> bool:
        """
        删除文档
        
        Args:
            document_id: 文档ID
            
        Returns:
            bool: 删除是否成功
        """
        pass
    
    @abstractmethod
    async def exists(self, document_id: str) -> bool:
        """
        检查文档是否存在
        
        Args:
            document_id: 文档ID
            
        Returns:
            bool: 是否存在
        """
        pass
    
    @abstractmethod
    async def count(self, filters: Optional[SearchFilter] = None) -> int:
        """
        统计文档数量
        
        Args:
            filters: 过滤条件
            
        Returns:
            int: 文档数量
        """
        pass
    
    @abstractmethod
    async def get_statistics(self) -> Dict[str, Any]:
        """
        获取文档统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        pass
    
    # 批量操作
    async def save_batch(self, documents: List[Document]) -> List[str]:
        """
        批量保存文档
        
        Args:
            documents: 文档列表
            
        Returns:
            List[str]: 保存的文档ID列表
        """
        saved_ids = []
        for document in documents:
            doc_id = await self.save(document)
            saved_ids.append(doc_id)
        return saved_ids
    
    async def find_by_ids(self, document_ids: List[str]) -> List[Document]:
        """
        根据ID列表查找文档
        
        Args:
            document_ids: 文档ID列表
            
        Returns:
            List[Document]: 文档列表
        """
        documents = []
        for doc_id in document_ids:
            document = await self.find_by_id(doc_id)
            if document:
                documents.append(document)
        return documents
    
    # 便捷方法
    async def find_by_file_type(self, file_type: str) -> List[Document]:
        """
        根据文件类型查找文档
        
        Args:
            file_type: 文件类型
            
        Returns:
            List[Document]: 文档列表
        """
        filter_criteria = SearchFilter(file_types=[file_type])
        return await self.search("", filter_criteria)
    
    async def find_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Document]:
        """
        根据日期范围查找文档
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            List[Document]: 文档列表
        """
        filter_criteria = SearchFilter(created_after=start_date, created_before=end_date)
        return await self.search("", filter_criteria)
    
    async def find_pending_documents(self) -> List[Document]:
        """查找待处理文档"""
        return await self.find_by_status(DocumentStatus.PENDING)
    
    async def find_completed_documents(self) -> List[Document]:
        """查找已完成文档"""
        return await self.find_by_status(DocumentStatus.COMPLETED)
    
    async def find_failed_documents(self) -> List[Document]:
        """查找处理失败文档"""
        return await self.find_by_status(DocumentStatus.ERROR)


