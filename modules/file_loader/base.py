"""
文件加载器接口定义

定义文件加载的标准接口和异常处理。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from ..models import Document, FileLoadRequest
from ..schemas.enums import ContentType


class FileLoaderError(Exception):
    """文件加载错误"""

    def __init__(
        self, message: str, file_path: Optional[str] = None, error_code: Optional[str] = None
    ):
        self.file_path = file_path
        self.error_code = error_code
        super().__init__(message)


class IFileLoader(ABC):
    """文件加载器接口"""

    @abstractmethod
    async def load_document(self, request: FileLoadRequest) -> Document:
        """
        加载文档

        Args:
            request: 文件加载请求

        Returns:
            Document: 加载的文档对象

        Raises:
            FileLoaderError: 文件加载失败时抛出
        """
        pass

    @abstractmethod
    def supports_content_type(self, content_type: ContentType) -> bool:
        """
        检查是否支持指定的内容类型

        Args:
            content_type: 内容类型

        Returns:
            bool: 是否支持
        """
        pass

    @abstractmethod
    async def validate_file(self, file_path: str) -> bool:
        """
        验证文件是否可以加载

        Args:
            file_path: 文件路径

        Returns:
            bool: 文件是否有效
        """
        pass

    @property
    @abstractmethod
    def loader_name(self) -> str:
        """
        获取加载器名称

        Returns:
            str: 加载器名称
        """
        pass
