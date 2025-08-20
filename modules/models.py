"""
统一数据模型

定义整个RAG系统中使用的核心数据结构。
替代分散在各个层次中的复杂领域模型。
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
import uuid


class ContentType(Enum):
    """内容类型枚举"""
    TEXT = "text/plain"
    PDF = "application/pdf"
    DOC = "application/msword"
    DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    HTML = "text/html"
    MARKDOWN = "text/markdown"
    JSON = "application/json"
    CSV = "text/csv"
    UNKNOWN = "application/octet-stream"


class ProcessingStatus(Enum):
    """处理状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ChunkingStrategy(Enum):
    """分块策略枚举"""
    FIXED_SIZE = "fixed_size"
    SEMANTIC = "semantic"
    PARAGRAPH = "paragraph"
    SENTENCE = "sentence"


@dataclass
class Document:
    """文档数据模型"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    content: str = ""
    content_type: ContentType = ContentType.TEXT
    source_path: Optional[str] = None
    source_url: Optional[str] = None
    file_size: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """后处理初始化"""
        if not self.title and self.source_path:
            # 从文件路径提取标题
            import os
            self.title = os.path.basename(self.source_path)
        
        if self.content:
            self.file_size = len(self.content.encode('utf-8'))
    
    @property
    def is_empty(self) -> bool:
        """检查文档是否为空"""
        return not self.content.strip()
    
    @property
    def word_count(self) -> int:
        """获取单词数量"""
        return len(self.content.split())
    
    @property
    def char_count(self) -> int:
        """获取字符数量"""
        return len(self.content)


@dataclass
class DocumentChunk:
    """文档块数据模型"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    document_id: str = ""
    content: str = ""
    chunk_index: int = 0
    start_position: int = 0
    end_position: int = 0
    chunk_size: int = 0
    overlap_size: int = 0
    strategy: ChunkingStrategy = ChunkingStrategy.FIXED_SIZE
    embedding_vector: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        """后处理初始化"""
        if not self.chunk_size:
            self.chunk_size = len(self.content)
        
        if not self.end_position and self.start_position:
            self.end_position = self.start_position + len(self.content)
    
    @property
    def has_embedding(self) -> bool:
        """检查是否有嵌入向量"""
        return self.embedding_vector is not None and len(self.embedding_vector) > 0
    
    @property
    def word_count(self) -> int:
        """获取单词数量"""
        return len(self.content.split())


@dataclass
class ProcessingResult:
    """处理结果数据模型"""
    document_id: str
    status: ProcessingStatus = ProcessingStatus.PENDING
    chunks_created: int = 0
    chunks: List[DocumentChunk] = field(default_factory=list)
    processing_time_ms: float = 0.0
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def is_successful(self) -> bool:
        """检查处理是否成功"""
        return self.status == ProcessingStatus.COMPLETED and self.error_message is None
    
    @property
    def has_chunks(self) -> bool:
        """检查是否有生成的块"""
        return len(self.chunks) > 0


@dataclass
class SearchQuery:
    """搜索查询数据模型"""
    query_text: str
    max_results: int = 10
    similarity_threshold: float = 0.7
    include_metadata: bool = True
    filters: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SearchResult:
    """搜索结果数据模型"""
    chunk: DocumentChunk
    document: Document
    relevance_score: float = 0.0
    rank: int = 0
    explanation: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FileLoadRequest:
    """文件加载请求数据模型"""
    file_path: str
    content_type: Optional[ContentType] = None
    encoding: str = "utf-8"
    max_file_size_mb: int = 100
    extract_metadata: bool = True
    custom_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProcessingRequest:
    """处理请求数据模型"""
    document: Document
    chunking_strategy: ChunkingStrategy = ChunkingStrategy.FIXED_SIZE
    chunk_size: int = 1000
    chunk_overlap: int = 200
    generate_embeddings: bool = True
    custom_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModuleConfig:
    """模块配置数据模型"""
    module_name: str
    enabled: bool = True
    max_file_size_mb: int = 100
    timeout_seconds: int = 60
    retry_attempts: int = 3
    custom_params: Dict[str, Any] = field(default_factory=dict)


# 类型别名，提高代码可读性
DocumentID = str
ChunkID = str
EmbeddingVector = List[float]
Metadata = Dict[str, Any]

# 常用配置常量
DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 200
DEFAULT_MAX_FILE_SIZE_MB = 100
DEFAULT_SIMILARITY_THRESHOLD = 0.7

# 支持的文件类型映射
CONTENT_TYPE_MAPPING = {
    '.txt': ContentType.TEXT,
    '.pdf': ContentType.PDF,
    '.doc': ContentType.DOC,
    '.docx': ContentType.DOCX,
    '.html': ContentType.HTML,
    '.htm': ContentType.HTML,
    '.md': ContentType.MARKDOWN,
    '.markdown': ContentType.MARKDOWN,
    '.json': ContentType.JSON,
    '.csv': ContentType.CSV,
}


def detect_content_type(file_path: str) -> ContentType:
    """根据文件扩展名检测内容类型"""
    import os
    ext = os.path.splitext(file_path)[1].lower()
    return CONTENT_TYPE_MAPPING.get(ext, ContentType.UNKNOWN)


def create_document_from_path(file_path: str, content: str = "") -> Document:
    """从文件路径创建文档对象"""
    import os
    
    return Document(
        title=os.path.basename(file_path),
        content=content,
        content_type=detect_content_type(file_path),
        source_path=file_path,
        file_size=len(content.encode('utf-8')) if content else 0
    )


def create_processing_request(document: Document, **kwargs) -> ProcessingRequest:
    """创建处理请求对象"""
    return ProcessingRequest(
        document=document,
        chunking_strategy=kwargs.get('chunking_strategy', ChunkingStrategy.FIXED_SIZE),
        chunk_size=kwargs.get('chunk_size', DEFAULT_CHUNK_SIZE),
        chunk_overlap=kwargs.get('chunk_overlap', DEFAULT_CHUNK_OVERLAP),
        generate_embeddings=kwargs.get('generate_embeddings', True),
        custom_params=kwargs.get('custom_params', {})
    )


# 编排相关模型
@dataclass
class OrchestrationRequest:
    """编排请求"""
    source_path: str
    chunking_strategy: ChunkingStrategy = ChunkingStrategy.FIXED_SIZE
    chunk_size: int = DEFAULT_CHUNK_SIZE
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP
    generate_embeddings: bool = False
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class OrchestrationResult:
    """编排结果"""
    operation_id: str
    document_id: str
    status: ProcessingStatus
    chunks_created: int
    total_processing_time_ms: float
    steps_completed: List[Dict[str, Any]] = field(default_factory=list)
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class RouterError(Exception):
    """路由器错误"""
    pass


class OrchestrationError(Exception):
    """编排错误"""
    
    def __init__(self, message: str, operation: Optional[str] = None, 
                 error_code: Optional[str] = None, original_error: Optional[Exception] = None):
        self.operation = operation
        self.error_code = error_code
        self.original_error = original_error
        super().__init__(message)


# 搜索相关模型
@dataclass
class SearchRequest:
    """搜索请求"""
    query: str
    limit: int = 10
    filters: Optional[Dict[str, Any]] = None
    document_ids: Optional[List[str]] = None
    content_types: Optional[List[ContentType]] = None
    tags: Optional[List[str]] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD


@dataclass
class SearchResult:
    """搜索结果"""
    query: str
    chunks: List[DocumentChunk] = field(default_factory=list)
    total_results: int = 0
    search_time_ms: float = 0.0
    metadata: Optional[Dict[str, Any]] = None


# 兼容性模型（为了与旧的router兼容）
@dataclass
class SearchQuery:
    """搜索查询（兼容性类）"""
    query: str
    max_results: int = 10
    document_ids: Optional[List[str]] = None
    content_types: Optional[List[ContentType]] = None
    tags: Optional[List[str]] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None


@dataclass  
class SearchResponse:
    """搜索响应（兼容性类）"""
    query: str
    results: List['SearchResult'] = field(default_factory=list)
    total_results: int = 0
    processing_time_ms: float = 0.0
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ModuleConfig:
    """模块配置"""
    chunk_size: int = DEFAULT_CHUNK_SIZE
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP
    max_file_size_mb: int = DEFAULT_MAX_FILE_SIZE_MB
    similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD
    enable_caching: bool = True
    max_concurrent_operations: int = 5


class ModuleInterface:
    """模块接口基类"""
    
    def __init__(self, config: ModuleConfig = None):
        self.config = config or ModuleConfig()
        self._initialized = False
    
    async def initialize(self):
        """初始化模块"""
        self._initialized = True
    
    async def cleanup(self):
        """清理模块资源"""
        self._initialized = False
    
    def get_status(self) -> Dict[str, Any]:
        """获取模块状态"""
        return {
            "initialized": self._initialized,
            "config": self.config.__dict__ if hasattr(self.config, '__dict__') else str(self.config)
        }


# 错误类
class FileLoaderError(Exception):
    """文件加载器错误"""
    pass


class DocumentProcessorError(Exception):
    """文档处理器错误"""
    pass