"""
编排器接口定义

定义业务流程编排的标准接口。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

from modules.models import (
    DocumentChunk,
    OrchestrationRequest,
    OrchestrationResult,
    ProcessingRequest,
    ProcessingResult,
    SearchRequest,
    SearchResult,
)
from modules.schemas import Document


class OrchestrationError(Exception):
    """编排错误"""

    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        error_code: Optional[str] = None,
        original_error: Optional[Exception] = None,
    ):
        self.operation = operation
        self.error_code = error_code
        self.original_error = original_error
        super().__init__(message)


class IOrchestrator(ABC):
    """编排器接口"""

    @abstractmethod
    async def process_document_end_to_end(
        self, request: OrchestrationRequest
    ) -> OrchestrationResult:
        """
        端到端处理文档

        包括：文件加载 -> 文档处理 -> 存储 -> 索引构建

        Args:
            request: 编排请求

        Returns:
            OrchestrationResult: 编排结果

        Raises:
            OrchestrationError: 编排失败时抛出
        """
        pass

    @abstractmethod
    async def search_documents(self, request: SearchRequest) -> SearchResult:
        """
        搜索文档

        Args:
            request: 搜索请求

        Returns:
            SearchResult: 搜索结果

        Raises:
            OrchestrationError: 搜索失败时抛出
        """
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        健康检查

        Returns:
            Dict[str, Any]: 各模块健康状态
        """
        pass

    @abstractmethod
    async def get_document_by_id(self, document_id: str) -> Optional[Document]:
        """
        根据ID获取文档

        Args:
            document_id: 文档ID

        Returns:
            Optional[Document]: 文档对象，如果不存在返回None
        """
        pass

    @abstractmethod
    async def get_chunks_by_document_id(self, document_id: str) -> List[DocumentChunk]:
        """
        根据文档ID获取所有块

        Args:
            document_id: 文档ID

        Returns:
            List[DocumentChunk]: 文档块列表
        """
        pass

    @abstractmethod
    async def delete_document(self, document_id: str) -> bool:
        """
        删除文档及其相关数据

        Args:
            document_id: 文档ID

        Returns:
            bool: 删除是否成功
        """
        pass

    @abstractmethod
    async def update_document_metadata(
        self, document_id: str, metadata: Dict[str, Any]
    ) -> bool:
        """
        更新文档元数据

        Args:
            document_id: 文档ID
            metadata: 新的元数据

        Returns:
            bool: 更新是否成功
        """
        pass

    @property
    @abstractmethod
    def orchestrator_name(self) -> str:
        """
        获取编排器名称

        Returns:
            str: 编排器名称
        """
        pass

    @property
    @abstractmethod
    def supported_operations(self) -> List[str]:
        """
        获取支持的操作列表

        Returns:
            List[str]: 支持的操作列表
        """
        pass
