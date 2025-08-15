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


class InMemoryKnowledgeStore(BaseKnowledgeStore):
    """内存知识存储实现（用于测试和小规模应用）"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.documents: Dict[str, Document] = {}
        self.processing_metadata: Dict[str, Dict[str, Any]] = {}
    
    async def store_document(self, document: Document) -> str:
        """存储文档到内存"""
        self.documents[document.id] = document
        return document.id
    
    async def get_document(self, document_id: str) -> Optional[Document]:
        """从内存获取文档"""
        return self.documents.get(document_id)
    
    async def update_document(self, document_id: str, document: Document) -> bool:
        """更新内存中的文档"""
        if document_id in self.documents:
            self.documents[document_id] = document
            return True
        return False
    
    async def delete_document(self, document_id: str) -> bool:
        """从内存删除文档"""
        if document_id in self.documents:
            del self.documents[document_id]
            self.processing_metadata.pop(document_id, None)
            return True
        return False
    
    async def search_documents(self, query: str, 
                              filters: Optional[SearchFilter] = None,
                              limit: int = 10,
                              offset: int = 0) -> List[Document]:
        """在内存中搜索文档"""
        results = list(self.documents.values())
        
        # 应用查询过滤
        if query:
            query_lower = query.lower()
            filtered_results = []
            for doc in results:
                if (query_lower in doc.title.lower() or 
                    query_lower in doc.content.lower()):
                    filtered_results.append(doc)
            results = filtered_results
        
        # 应用其他过滤器
        if filters:
            if filters.document_ids:
                results = [doc for doc in results if doc.id in filters.document_ids]
            
            if filters.file_types:
                results = [doc for doc in results if doc.file_type in filters.file_types]
            
            if filters.created_after:
                results = [doc for doc in results if doc.created_at >= filters.created_after]
            
            if filters.created_before:
                results = [doc for doc in results if doc.created_at <= filters.created_before]
        
        # 分页
        return results[offset:offset + limit]
    
    async def get_documents_by_status(self, status: DocumentStatus) -> List[Document]:
        """根据状态获取文档"""
        return [doc for doc in self.documents.values() if doc.status == status]
    
    async def update_document_status(self, document_id: str, status: DocumentStatus) -> bool:
        """更新文档状态"""
        if document_id in self.documents:
            self.documents[document_id].update_status(status)
            return True
        return False
    
    async def get_document_statistics(self) -> Dict[str, Any]:
        """获取文档统计信息"""
        total_docs = len(self.documents)
        status_counts = {}
        file_type_counts = {}
        total_size = 0
        
        for doc in self.documents.values():
            # 状态统计
            status_counts[doc.status.value] = status_counts.get(doc.status.value, 0) + 1
            
            # 文件类型统计
            file_type_counts[doc.file_type] = file_type_counts.get(doc.file_type, 0) + 1
            
            # 文件大小统计
            total_size += doc.file_size
        
        return {
            'total_documents': total_docs,
            'status_distribution': status_counts,
            'file_type_distribution': file_type_counts,
            'total_size_bytes': total_size,
            'average_size_bytes': total_size / total_docs if total_docs > 0 else 0
        }
    
    async def store_processing_metadata(self, document_id: str, metadata: Dict[str, Any]) -> bool:
        """存储处理元数据"""
        if document_id in self.documents:
            self.processing_metadata[document_id] = metadata
            return True
        return False
    
    async def get_processing_metadata(self, document_id: str) -> Optional[Dict[str, Any]]:
        """获取处理元数据"""
        return self.processing_metadata.get(document_id)


# 异常类定义
class KnowledgeStoreError(Exception):
    """知识存储错误"""
    pass


class DocumentNotFoundError(KnowledgeStoreError):
    """文档未找到错误"""
    pass