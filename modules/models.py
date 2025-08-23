"""
数据模型

定义RAG系统的核心数据模型和API请求响应模型。
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


# 枚举类型
class ContentType(str, Enum):
    """内容类型"""

    PDF = "pdf"
    DOC = "doc"
    DOCX = "docx"
    TXT = "txt"
    HTML = "html"
    MD = "md"
    JSON = "json"
    CSV = "csv"


class ChunkingStrategy(str, Enum):
    """分块策略"""

    FIXED_SIZE = "fixed_size"
    SENTENCE = "sentence"
    PARAGRAPH = "paragraph"
    SEMANTIC = "semantic"


# 核心数据模型


@dataclass
class DocumentChunk:
    """文档块数据模型"""

    id: str
    document_id: str
    content: str
    chunk_index: int
    start_char: Optional[int] = None
    end_char: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class SearchQuery:
    """搜索查询模型"""

    query: str
    limit: int = 10
    filters: Optional[Dict[str, Any]] = None


@dataclass
class SearchResult:
    """搜索结果模型"""

    document_id: str
    title: str
    content: str
    score: float
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class SearchResponse:
    """搜索响应模型"""

    results: List[SearchResult]
    total: int
    query: str


@dataclass
class FileLoadRequest:
    """文件加载请求"""

    file_path: str
    content_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ModuleConfig:
    """模块配置"""

    name: str
    enabled: bool = True
    settings: Optional[Dict[str, Any]] = None


# 接口定义
class ModuleInterface:
    """模块接口基类"""

    pass


# 处理状态枚举
class ProcessingStatus(str, Enum):
    """处理状态"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# 请求和结果模型
@dataclass
class ProcessingRequest:
    """处理请求"""

    document_id: str
    chunking_strategy: ChunkingStrategy = ChunkingStrategy.FIXED_SIZE
    chunk_size: int = 1000
    chunk_overlap: int = 200


@dataclass
class ProcessingResult:
    """处理结果"""

    success: bool
    document_id: str
    chunks_created: int = 0
    error_message: Optional[str] = None


@dataclass
class SearchRequest:
    """搜索请求"""

    query: str
    limit: int = 10
    filters: Optional[Dict[str, Any]] = None


@dataclass
class OrchestrationRequest:
    """编排请求"""

    file_path: str
    chunking_strategy: ChunkingStrategy = ChunkingStrategy.FIXED_SIZE
    chunk_size: int = 1000
    chunk_overlap: int = 200


@dataclass
class OrchestrationResult:
    """编排结果"""

    success: bool
    document_id: str
    file_path: str
    chunks_created: int = 0
    processing_time: float = 0.0
    error_message: Optional[str] = None


# 工具函数
# 异常类
class FileLoaderError(Exception):
    """文件加载异常"""

    pass


class DocumentProcessorError(Exception):
    """文档处理异常"""

    pass


# API请求响应模型 (Pydantic)
class UploadUrlRequest(BaseModel):
    """上传URL请求模型"""

    filename: str
    content_type: str
    topic_id: Optional[int] = None
    expires_in: int = 3600


class UploadUrlResponse(BaseModel):
    """上传URL响应模型"""

    file_id: str
    upload_url: str
    method: str
    headers: Dict[str, str]
    fields: Dict[str, str]
    expires_at: str
    max_file_size: int
    allowed_types: list


class ConfirmUploadRequest(BaseModel):
    """确认上传请求模型"""

    file_id: str
    actual_size: Optional[int] = None
    file_hash: Optional[str] = None


class ConfirmUploadResponse(BaseModel):
    """确认上传响应模型"""

    success: bool
    file_id: str
    status: str
    message: str
    file_size: Optional[int] = None
    download_url: Optional[str] = None
    error: Optional[str] = None
