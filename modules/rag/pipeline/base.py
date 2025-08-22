"""
文档处理管道接口定义

定义端到端文档处理管道的标准接口，协调文件解析、分块、嵌入生成和向量存储。
"""

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, AsyncIterator, Dict, List, Optional

from modules.schemas.enums import ContentType


class PipelineStatus(Enum):
    """管道状态"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ProcessingStage(Enum):
    """处理阶段"""

    FILE_LOADING = "file_loading"
    DOCUMENT_PARSING = "document_parsing"
    TEXT_CHUNKING = "text_chunking"
    EMBEDDING_GENERATION = "embedding_generation"
    VECTOR_STORAGE = "vector_storage"
    INDEXING = "indexing"


class PipelineConfig:
    """管道配置"""

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        enable_embeddings: bool = True,
        enable_vector_storage: bool = True,
        batch_size: int = 100,
        max_concurrent_chunks: int = 5,
        retry_attempts: int = 3,
        timeout_seconds: int = 300,
        **kwargs,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.enable_embeddings = enable_embeddings
        self.enable_vector_storage = enable_vector_storage
        self.batch_size = batch_size
        self.max_concurrent_chunks = max_concurrent_chunks
        self.retry_attempts = retry_attempts
        self.timeout_seconds = timeout_seconds
        self.extra_params = kwargs


class DocumentProcessingRequest:
    """文档处理请求"""

    def __init__(
        self,
        file_id: str,
        file_path: str,
        content_type: Optional[ContentType] = None,
        topic_id: Optional[int] = None,
        config: Optional[PipelineConfig] = None,
        metadata: Optional[Dict[str, Any]] = None,
        priority: int = 0,
    ):
        self.file_id = file_id
        self.file_path = file_path
        self.topic_id = topic_id
        self.config = config or PipelineConfig()
        self.metadata = metadata or {}
        self.priority = priority
        self.created_at = datetime.utcnow()
        self.content_type = content_type or ContentType.TXT  # default to text content


class ProcessingStageResult:
    """处理阶段结果"""

    def __init__(
        self,
        stage: ProcessingStage,
        status: PipelineStatus,
        processing_time_ms: float,
        items_processed: int = 0,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.stage = stage
        self.status = status
        self.processing_time_ms = processing_time_ms
        self.items_processed = items_processed
        self.error_message = error_message
        self.metadata = metadata or {}


class DocumentProcessingResult:
    """文档处理结果"""

    def __init__(
        self,
        request_id: str,
        file_id: str,
        status: PipelineStatus,
        document_id: Optional[str] = None,
        total_chunks: int = 0,
        embedded_chunks: int = 0,
        stored_vectors: int = 0,
        total_processing_time_ms: float = 0,
        stage_results: Optional[List[ProcessingStageResult]] = None,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.request_id = request_id
        self.file_id = file_id
        self.status = status
        self.document_id = document_id
        self.total_chunks = total_chunks
        self.embedded_chunks = embedded_chunks
        self.stored_vectors = stored_vectors
        self.total_processing_time_ms = total_processing_time_ms
        self.stage_results = stage_results or []
        self.error_message = error_message
        self.metadata = metadata or {}
        self.completed_at = datetime.utcnow()


class ProcessingProgress:
    """处理进度"""

    def __init__(
        self,
        request_id: str,
        current_stage: ProcessingStage,
        progress_percentage: float,
        current_status: PipelineStatus,
        estimated_remaining_ms: Optional[float] = None,
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.request_id = request_id
        self.current_stage = current_stage
        self.progress_percentage = progress_percentage
        self.current_status = current_status
        self.estimated_remaining_ms = estimated_remaining_ms
        self.message = message
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow()


class BatchProcessingResult:
    """批量处理结果"""

    def __init__(
        self,
        batch_id: str,
        total_files: int,
        completed_files: int,
        failed_files: int,
        total_processing_time_ms: float,
        individual_results: List[DocumentProcessingResult],
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.batch_id = batch_id
        self.total_files = total_files
        self.completed_files = completed_files
        self.failed_files = failed_files
        self.total_processing_time_ms = total_processing_time_ms
        self.individual_results = individual_results
        self.metadata = metadata or {}


class PipelineError(Exception):
    """管道处理错误"""

    def __init__(
        self,
        message: str,
        stage: Optional[ProcessingStage] = None,
        error_code: Optional[str] = None,
        original_error: Optional[Exception] = None,
    ):
        self.stage = stage
        self.error_code = error_code
        self.original_error = original_error
        super().__init__(message)


class IDocumentPipeline(ABC):
    """文档处理管道接口"""

    @abstractmethod
    async def initialize(self) -> None:
        """
        初始化管道

        Raises:
            PipelineError: 初始化失败时抛出
        """
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """清理管道资源"""
        pass

    @abstractmethod
    async def process_document(
        self, request: DocumentProcessingRequest
    ) -> DocumentProcessingResult:
        """
        处理单个文档

        Args:
            request: 文档处理请求

        Returns:
            DocumentProcessingResult: 处理结果

        Raises:
            PipelineError: 处理失败时抛出
        """
        pass

    @abstractmethod
    async def process_documents_batch(
        self, requests: List[DocumentProcessingRequest]
    ) -> AsyncIterator[DocumentProcessingResult]:
        """
        批量处理文档

        Args:
            requests: 文档处理请求列表

        Yields:
            DocumentProcessingResult: 每个文档的处理结果

        Raises:
            PipelineError: 处理失败时抛出
        """
        pass

    @abstractmethod
    async def get_processing_status(self, request_id: str) -> Optional[ProcessingProgress]:
        """
        获取处理状态

        Args:
            request_id: 请求ID

        Returns:
            Optional[ProcessingProgress]: 处理进度，不存在返回None
        """
        pass

    @abstractmethod
    async def cancel_processing(self, request_id: str) -> bool:
        """
        取消处理

        Args:
            request_id: 请求ID

        Returns:
            bool: 取消是否成功
        """
        pass

    @abstractmethod
    async def retry_failed_processing(self, request_id: str) -> DocumentProcessingResult:
        """
        重试失败的处理

        Args:
            request_id: 请求ID

        Returns:
            DocumentProcessingResult: 重试处理结果

        Raises:
            PipelineError: 重试失败时抛出
        """
        pass

    @abstractmethod
    async def get_pipeline_metrics(self) -> Dict[str, Any]:
        """
        获取管道性能指标

        Returns:
            Dict[str, Any]: 性能指标
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
    def pipeline_name(self) -> str:
        """
        获取管道名称

        Returns:
            str: 管道名称
        """
        pass

    @property
    @abstractmethod
    def config(self) -> PipelineConfig:
        """
        获取配置信息

        Returns:
            PipelineConfig: 配置对象
        """
        pass

    @property
    @abstractmethod
    def supported_file_types(self) -> List[str]:
        """
        获取支持的文件类型

        Returns:
            List[str]: 支持的文件扩展名列表
        """
        pass
