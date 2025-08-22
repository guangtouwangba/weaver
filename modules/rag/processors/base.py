"""
文档处理器接口定义

定义文档处理的标准接口和异常处理。
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from ...models import Document, DocumentChunk, ProcessingRequest, ProcessingResult
from ...schemas.enums import ChunkingStrategy


class DocumentProcessorError(Exception):
    """文档处理错误"""

    def __init__(
        self, message: str, document_id: Optional[str] = None, error_code: Optional[str] = None
    ):
        self.document_id = document_id
        self.error_code = error_code
        super().__init__(message)


class IDocumentProcessor(ABC):
    """文档处理器接口"""

    @abstractmethod
    async def process_document(self, request: ProcessingRequest) -> ProcessingResult:
        """
        处理文档

        Args:
            request: 处理请求

        Returns:
            ProcessingResult: 处理结果

        Raises:
            DocumentProcessorError: 文档处理失败时抛出
        """

    @abstractmethod
    async def create_chunks(self, document: Document, **kwargs) -> List[DocumentChunk]:
        """
        创建文档块

        Args:
            document: 文档对象
            **kwargs: 其他参数

        Returns:
            List[DocumentChunk]: 文档块列表

        Raises:
            DocumentProcessorError: 分块失败时抛出
        """

    @abstractmethod
    async def validate_document(self, document: Document) -> bool:
        """
        验证文档是否可以处理

        Args:
            document: 文档对象

        Returns:
            bool: 文档是否有效
        """

    @abstractmethod
    async def clean_content(self, content: str) -> str:
        """
        清理文档内容

        Args:
            content: 原始内容

        Returns:
            str: 清理后的内容
        """

    @property
    @abstractmethod
    def processor_name(self) -> str:
        """
        获取处理器名称

        Returns:
            str: 处理器名称
        """

    @property
    @abstractmethod
    def supported_strategies(self) -> List[str]:
        """
        获取支持的处理策略

        Returns:
            List[str]: 支持的策略列表
        """


def register_chunking_strategy(strategy_name: ChunkingStrategy):
    """
    注册文档分块策略

    Args:
        strategy_name: 策略名称

    Returns:
        Callable: 装饰器函数
    """

    def decorator(func):
        if not hasattr(IDocumentProcessor, "chunking_strategies"):
            IDocumentProcessor.chunking_strategies = {}
        IDocumentProcessor.chunking_strategies[strategy_name] = func
        return func

    return decorator
