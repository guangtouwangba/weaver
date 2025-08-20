"""
Knowledge Domain Interfaces

核心知识管理领域接口，定义纯业务抽象，不依赖任何技术实现。
遵循SOLID原则，特别是依赖倒置原则(DIP)和接口隔离原则(ISP)。
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, AsyncIterator
from datetime import datetime
from enum import Enum
from dataclasses import dataclass

# Domain Value Objects
@dataclass(frozen=True)
class DocumentId:
    """文档ID值对象"""
    value: str
    
    def __post_init__(self):
        if not self.value or not isinstance(self.value, str):
            raise ValueError("DocumentId must be a non-empty string")

@dataclass(frozen=True)
class ChunkId:
    """文档块ID值对象"""
    value: str
    
    def __post_init__(self):
        if not self.value or not isinstance(self.value, str):
            raise ValueError("ChunkId must be a non-empty string")

# Domain Enums
class ProcessingStatus(Enum):
    """文档处理状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class SearchStrategy(Enum):
    """搜索策略"""
    SEMANTIC = "semantic"
    KEYWORD = "keyword"
    HYBRID = "hybrid"
    FUZZY = "fuzzy"

class ChunkingStrategy(Enum):
    """文档分块策略"""
    FIXED_SIZE = "fixed_size"
    SEMANTIC = "semantic"
    PARAGRAPH = "paragraph"
    SENTENCE = "sentence"

# Domain Entities (Business Objects)
@dataclass
class KnowledgeDocument:
    """知识文档领域实体"""
    id: DocumentId
    title: str
    content: str
    content_type: str
    source_location: str
    status: ProcessingStatus
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]
    
    def mark_as_processing(self) -> None:
        """标记为处理中"""
        self.status = ProcessingStatus.PROCESSING
        self.updated_at = datetime.utcnow()
    
    def mark_as_completed(self) -> None:
        """标记为处理完成"""
        self.status = ProcessingStatus.COMPLETED
        self.updated_at = datetime.utcnow()
    
    def mark_as_failed(self, error_message: str) -> None:
        """标记为处理失败"""
        self.status = ProcessingStatus.FAILED
        self.metadata['error_message'] = error_message
        self.updated_at = datetime.utcnow()

@dataclass
class DocumentChunk:
    """文档块领域实体"""
    id: ChunkId
    document_id: DocumentId
    content: str
    chunk_index: int
    start_position: int
    end_position: int
    metadata: Dict[str, Any]
    embedding_vector: Optional[List[float]] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()

@dataclass
class SearchQuery:
    """搜索查询领域对象"""
    text: str
    strategy: SearchStrategy
    max_results: int = 10
    filters: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.filters is None:
            self.filters = {}

@dataclass
class SearchResult:
    """搜索结果领域对象"""
    chunk: DocumentChunk
    document: KnowledgeDocument
    relevance_score: float
    rank: int
    explanation: Optional[str] = None

# Domain Interfaces (按职责分离)
class IKnowledgeRepository(ABC):
    """知识存储仓储接口 - 负责持久化"""
    
    @abstractmethod
    async def save_document(self, document: KnowledgeDocument) -> None:
        """保存文档"""
        pass
    
    @abstractmethod
    async def find_document_by_id(self, document_id: DocumentId) -> Optional[KnowledgeDocument]:
        """根据ID查找文档"""
        pass
    
    @abstractmethod
    async def find_documents_by_status(self, status: ProcessingStatus) -> List[KnowledgeDocument]:
        """根据状态查找文档"""
        pass
    
    @abstractmethod
    async def save_chunks(self, chunks: List[DocumentChunk]) -> None:
        """保存文档块"""
        pass
    
    @abstractmethod
    async def find_chunks_by_document_id(self, document_id: DocumentId) -> List[DocumentChunk]:
        """查找文档的所有块"""
        pass

class IDocumentProcessor(ABC):
    """文档处理器接口 - 负责业务逻辑"""
    
    @abstractmethod
    async def extract_content(self, source_location: str, content_type: str) -> str:
        """从源位置提取内容"""
        pass
    
    @abstractmethod
    async def chunk_document(self, 
                           document: KnowledgeDocument, 
                           strategy: ChunkingStrategy,
                           chunk_size: int = 1000,
                           overlap: int = 200) -> List[DocumentChunk]:
        """将文档分块"""
        pass
    
    @abstractmethod
    async def validate_document(self, document: KnowledgeDocument) -> bool:
        """验证文档"""
        pass

class IVectorService(ABC):
    """向量服务接口 - 负责向量操作"""
    
    @abstractmethod
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """生成文本向量"""
        pass
    
    @abstractmethod
    async def store_vectors(self, chunks: List[DocumentChunk]) -> None:
        """存储向量"""
        pass
    
    @abstractmethod
    async def search_similar(self, 
                           query_vector: List[float], 
                           max_results: int,
                           filters: Dict[str, Any] = None) -> List[ChunkId]:
        """向量相似性搜索"""
        pass

class ISearchService(ABC):
    """搜索服务接口 - 负责搜索逻辑"""
    
    @abstractmethod
    async def search(self, query: SearchQuery) -> List[SearchResult]:
        """执行搜索"""
        pass
    
    @abstractmethod
    async def semantic_search(self, 
                            query_text: str, 
                            max_results: int,
                            filters: Dict[str, Any] = None) -> List[SearchResult]:
        """语义搜索"""
        pass
    
    @abstractmethod
    async def keyword_search(self, 
                           query_text: str, 
                           max_results: int,
                           filters: Dict[str, Any] = None) -> List[SearchResult]:
        """关键词搜索"""
        pass

# Domain Services (复杂业务逻辑)
class IKnowledgeManagementService(ABC):
    """知识管理领域服务 - 负责复杂业务规则"""
    
    @abstractmethod
    async def ingest_document(self, 
                            source_location: str,
                            content_type: str,
                            title: str,
                            metadata: Dict[str, Any] = None) -> DocumentId:
        """文档摄取业务流程"""
        pass
    
    @abstractmethod
    async def process_document(self, document_id: DocumentId) -> None:
        """处理文档业务流程"""
        pass
    
    @abstractmethod
    async def delete_document(self, document_id: DocumentId) -> None:
        """删除文档业务流程"""
        pass

# Domain Events
@dataclass(frozen=True)
class DocumentIngested:
    """文档摄取完成事件"""
    document_id: DocumentId
    source_location: str
    occurred_at: datetime

@dataclass(frozen=True)
class DocumentProcessed:
    """文档处理完成事件"""
    document_id: DocumentId
    chunk_count: int
    processing_time_ms: float
    occurred_at: datetime

@dataclass(frozen=True)
class DocumentProcessingFailed:
    """文档处理失败事件"""
    document_id: DocumentId
    error_message: str
    occurred_at: datetime