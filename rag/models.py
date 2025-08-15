"""
RAG系统的核心数据模型
支持基础文档处理和未来多模态扩展
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum
import uuid


class DocumentStatus(Enum):
    """文档处理状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class Document:
    """基础文档数据模型"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    source_path: str = ""
    file_type: str = ""
    file_size: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    status: DocumentStatus = DocumentStatus.PENDING
    
    def __post_init__(self):
        """初始化后的处理"""
        if not self.title and self.source_path:
            self.title = self.source_path.split('/')[-1]
        
        if not self.file_type and self.source_path:
            self.file_type = self.source_path.split('.')[-1].lower()
    
    def update_status(self, status: DocumentStatus) -> None:
        """更新文档状态"""
        self.status = status
        self.updated_at = datetime.now()
    
    def get_word_count(self) -> int:
        """获取文档字数"""
        return len(self.content.split()) if self.content else 0
    
    def get_preview(self, max_length: int = 200) -> str:
        """获取文档预览"""
        if len(self.content) <= max_length:
            return self.content
        return self.content[:max_length] + "..."


@dataclass
class DocumentChunk:
    """文档块数据模型"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    document_id: str = ""
    content: str = ""
    chunk_index: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 位置信息
    start_offset: int = 0
    end_offset: int = 0
    
    # 向量和特征
    embedding: Optional[List[float]] = None
    embedding_model: str = ""
    
    # 处理信息
    created_at: datetime = field(default_factory=datetime.now)
    
    def get_word_count(self) -> int:
        """获取块字数"""
        return len(self.content.split()) if self.content else 0
    
    def get_character_count(self) -> int:
        """获取字符数"""
        return len(self.content) if self.content else 0


@dataclass
class QueryResult:
    """查询结果数据模型"""
    query: str
    chunks: List[DocumentChunk] = field(default_factory=list)
    relevance_scores: List[float] = field(default_factory=list)
    total_found: int = 0
    query_time_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def get_top_chunks(self, k: int = 3) -> List[DocumentChunk]:
        """获取前K个最相关的块"""
        if not self.chunks:
            return []
        
        # 按相关性分数排序
        sorted_pairs = sorted(
            zip(self.chunks, self.relevance_scores), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        return [chunk for chunk, _ in sorted_pairs[:k]]
    
    def get_average_score(self) -> float:
        """获取平均相关性分数"""
        if not self.relevance_scores:
            return 0.0
        return sum(self.relevance_scores) / len(self.relevance_scores)


@dataclass
class ProcessingResult:
    """文档处理结果"""
    success: bool
    message: str = ""
    document_id: str = ""
    chunks_created: int = 0
    processing_time_ms: float = 0.0
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchFilter:
    """搜索过滤器"""
    document_ids: Optional[List[str]] = None
    file_types: Optional[List[str]] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    min_relevance_score: float = 0.0
    metadata_filters: Dict[str, Any] = field(default_factory=dict)
    
    def apply_to_chunks(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """应用过滤器到文档块列表"""
        filtered_chunks = chunks
        
        if self.document_ids:
            filtered_chunks = [c for c in filtered_chunks if c.document_id in self.document_ids]
        
        # 可以添加更多过滤逻辑
        
        return filtered_chunks


@dataclass
class IndexInfo:
    """索引信息"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    document_count: int = 0
    chunk_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


# 配置相关数据模型
@dataclass
class EmbeddingConfig:
    """嵌入模型配置"""
    model_name: str = "text-embedding-ada-002"
    api_key: str = ""
    api_base: str = ""
    dimension: int = 1536
    batch_size: int = 100
    timeout: int = 30


@dataclass
class VectorStoreConfig:
    """向量存储配置"""
    store_type: str = "chromadb"  # chromadb, qdrant, pinecone
    connection_string: str = ""
    collection_name: str = "default"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RAGConfig:
    """RAG系统总体配置"""
    chunk_size: int = 1000
    chunk_overlap: int = 100
    top_k: int = 10
    similarity_threshold: float = 0.7
    embedding_config: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    vector_store_config: VectorStoreConfig = field(default_factory=VectorStoreConfig)
    
    # 文件处理配置
    supported_file_types: List[str] = field(default_factory=lambda: ['.txt', '.md', '.pdf', '.docx'])
    max_file_size_mb: int = 100
    
    # 检索配置
    enable_reranking: bool = False
    rerank_top_k: int = 50
    
    def validate(self) -> List[str]:
        """验证配置"""
        errors = []
        
        if self.chunk_size <= 0:
            errors.append("chunk_size must be positive")
        
        if self.chunk_overlap >= self.chunk_size:
            errors.append("chunk_overlap must be less than chunk_size")
        
        if self.top_k <= 0:
            errors.append("top_k must be positive")
        
        return errors