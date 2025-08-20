"""
模块化API接口定义

定义统一的、简化的API接口。
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union
from ..models import Document, DocumentChunk, SearchResult


class APIError(Exception):
    """API错误"""
    
    def __init__(self, message: str, error_code: Optional[str] = None, 
                 status_code: int = 500, details: Optional[Dict[str, Any]] = None):
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class IModularAPI(ABC):
    """模块化API接口"""
    
    @abstractmethod
    async def process_file(self, file_path: str, **options) -> Dict[str, Any]:
        """
        处理单个文件
        
        Args:
            file_path: 文件路径
            **options: 处理选项
            
        Returns:
            Dict[str, Any]: 处理结果
            
        Raises:
            APIError: 处理失败时抛出
        """
        pass
    
    @abstractmethod
    async def process_files(self, file_paths: List[str], **options) -> List[Dict[str, Any]]:
        """
        批量处理文件
        
        Args:
            file_paths: 文件路径列表
            **options: 处理选项
            
        Returns:
            List[Dict[str, Any]]: 处理结果列表
        """
        pass
    
    @abstractmethod
    async def search(self, query: str, limit: int = 10, **filters) -> Dict[str, Any]:
        """
        搜索文档
        
        Args:
            query: 搜索查询
            limit: 结果数量限制
            **filters: 搜索过滤器
            
        Returns:
            Dict[str, Any]: 搜索结果
        """
        pass
    
    @abstractmethod
    async def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        获取文档
        
        Args:
            document_id: 文档ID
            
        Returns:
            Optional[Dict[str, Any]]: 文档信息，如果不存在返回None
        """
        pass
    
    @abstractmethod
    async def get_document_chunks(self, document_id: str) -> List[Dict[str, Any]]:
        """
        获取文档块
        
        Args:
            document_id: 文档ID
            
        Returns:
            List[Dict[str, Any]]: 文档块列表
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
    async def update_document_metadata(self, document_id: str, metadata: Dict[str, Any]) -> bool:
        """
        更新文档元数据
        
        Args:
            document_id: 文档ID
            metadata: 新的元数据
            
        Returns:
            bool: 更新是否成功
        """
        pass
    
    @abstractmethod
    async def get_status(self) -> Dict[str, Any]:
        """
        获取系统状态
        
        Returns:
            Dict[str, Any]: 系统状态信息
        """
        pass
    
    @abstractmethod
    async def get_supported_formats(self) -> List[str]:
        """
        获取支持的文件格式
        
        Returns:
            List[str]: 支持的格式列表
        """
        pass
