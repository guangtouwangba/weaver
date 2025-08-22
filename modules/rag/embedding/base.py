"""
嵌入服务接口定义

定义向量嵌入生成的标准接口，支持多种嵌入模型。
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, Union


class EmbeddingProvider(Enum):
    """嵌入服务提供商"""

    OPENAI = "openai"
    HUGGINGFACE = "huggingface"
    LOCAL = "local"


class EmbeddingConfig:
    """嵌入配置"""

    def __init__(
        self,
        provider: EmbeddingProvider,
        model_name: str,
        dimension: int,
        max_tokens: Optional[int] = None,
        api_key: Optional[str] = None,
        model_path: Optional[str] = None,
        batch_size: int = 100,
        **kwargs,
    ):
        self.provider = provider
        self.model_name = model_name
        self.dimension = dimension
        self.max_tokens = max_tokens
        self.api_key = api_key
        self.model_path = model_path
        self.batch_size = batch_size
        self.extra_params = kwargs


class EmbeddingResult:
    """嵌入结果"""

    def __init__(
        self,
        vectors: List[List[float]],
        texts: List[str],
        model_name: str,
        dimension: int,
        processing_time_ms: float,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.vectors = vectors
        self.texts = texts
        self.model_name = model_name
        self.dimension = dimension
        self.processing_time_ms = processing_time_ms
        self.metadata = metadata or {}


class EmbeddingError(Exception):
    """嵌入服务错误"""

    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        error_code: Optional[str] = None,
        original_error: Optional[Exception] = None,
    ):
        self.provider = provider
        self.error_code = error_code
        self.original_error = original_error
        super().__init__(message)


class IEmbeddingService(ABC):
    """嵌入服务接口"""

    @abstractmethod
    async def initialize(self) -> None:
        """
        初始化嵌入服务

        Raises:
            EmbeddingError: 初始化失败时抛出
        """
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """清理嵌入服务资源"""
        pass

    @abstractmethod
    async def generate_embeddings(self, texts: List[str]) -> EmbeddingResult:
        """
        生成文本嵌入向量

        Args:
            texts: 待嵌入的文本列表

        Returns:
            EmbeddingResult: 嵌入结果

        Raises:
            EmbeddingError: 嵌入生成失败时抛出
        """
        pass

    @abstractmethod
    async def generate_single_embedding(self, text: str) -> List[float]:
        """
        生成单个文本的嵌入向量

        Args:
            text: 待嵌入的文本

        Returns:
            List[float]: 嵌入向量

        Raises:
            EmbeddingError: 嵌入生成失败时抛出
        """
        pass

    @abstractmethod
    async def get_embedding_dimension(self) -> int:
        """
        获取嵌入向量维度

        Returns:
            int: 向量维度
        """
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        健康检查

        Returns:
            Dict[str, Any]: 健康状态信息
        """
        pass

    @property
    @abstractmethod
    def service_name(self) -> str:
        """
        获取服务名称

        Returns:
            str: 服务名称
        """
        pass

    @property
    @abstractmethod
    def config(self) -> EmbeddingConfig:
        """
        获取配置信息

        Returns:
            EmbeddingConfig: 配置对象
        """
        pass

    @property
    @abstractmethod
    def supported_languages(self) -> List[str]:
        """
        获取支持的语言列表

        Returns:
            List[str]: 支持的语言代码列表
        """
        pass
