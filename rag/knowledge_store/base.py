"""
知识存储基础接口
管理文档元数据和知识信息
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..models import Document, DocumentStatus, SearchFilter, IndexInfo


class BaseKnowledgeStore(ABC):
    """知识存储基类"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化知识存储
        
        Args:
            config: 配置参数
        """
        self.config = config or {}
    
    @abstractmethod
    async def store_document(self, document: Document) -> str:
        """
        存储文档元数据和知识信息
        
        Args:
            document: 文档对象
            
        Returns:
            str: 存储的记录ID
            
        Raises:
            KnowledgeStoreError: 存储错误
        """
        pass
    
    @abstractmethod
    async def get_document(self, document_id: str) -> Optional[Document]:
        """
        根据ID获取文档
        
        Args:
            document_id: 文档ID
            
        Returns:
            Optional[Document]: 文档对象，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    async def update_document(self, document_id: str, document: Document) -> bool:
        """
        更新文档
        
        Args:
            document_id: 文档ID
            document: 新的文档数据
            
        Returns:
            bool: 更新是否成功
        """
        pass
    
    @abstractmethod
    async def delete_document(self, document_id: str) -> bool:
        """
        删除文档
        
        Args:
            document_id: 文档ID
            
        Returns:
            bool: 删除是否成功
        """
        pass
    
    @abstractmethod
    async def search_documents(self, query: str, 
                              filters: Optional[SearchFilter] = None,
                              limit: int = 10,
                              offset: int = 0) -> List[Document]:
        """
        搜索文档
        
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
    async def get_documents_by_status(self, status: DocumentStatus) -> List[Document]:
        """
        根据状态获取文档列表
        
        Args:
            status: 文档状态
            
        Returns:
            List[Document]: 指定状态的文档列表
        """
        pass
    
    @abstractmethod
    async def update_document_status(self, document_id: str, status: DocumentStatus) -> bool:
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
    async def get_document_statistics(self) -> Dict[str, Any]:
        """
        获取文档统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        pass
    
    @abstractmethod
    async def store_processing_metadata(self, document_id: str, metadata: Dict[str, Any]) -> bool:
        """
        存储处理元数据
        
        Args:
            document_id: 文档ID
            metadata: 处理元数据
            
        Returns:
            bool: 存储是否成功
        """
        pass
    
    @abstractmethod
    async def get_processing_metadata(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        获取处理元数据
        
        Args:
            document_id: 文档ID
            
        Returns:
            Optional[Dict[str, Any]]: 处理元数据
        """
        pass
    
    # 通用工具方法
    async def batch_store_documents(self, documents: List[Document]) -> List[str]:
        """
        批量存储文档
        
        Args:
            documents: 文档列表
            
        Returns:
            List[str]: 存储的文档ID列表
        """
        stored_ids = []
        for document in documents:
            document_id = await self.store_document(document)
            stored_ids.append(document_id)
        return stored_ids
    
    async def get_documents_by_file_type(self, file_type: str) -> List[Document]:
        """
        根据文件类型获取文档
        
        Args:
            file_type: 文件类型
            
        Returns:
            List[Document]: 指定类型的文档列表
        """
        filter_criteria = SearchFilter(file_types=[file_type])
        return await self.search_documents("", filter_criteria)
    
    async def get_documents_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Document]:
        """
        根据日期范围获取文档
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            List[Document]: 指定日期范围内的文档列表
        """
        filter_criteria = SearchFilter(created_after=start_date, created_before=end_date)
        return await self.search_documents("", filter_criteria)