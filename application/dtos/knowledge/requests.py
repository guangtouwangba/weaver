"""
Knowledge Management Request DTOs

输入数据传输对象，用于API层向应用层传递数据。
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum

from domain.file import StorageLocation
# 导入Domain层的枚举，但不导入实体
from domain.knowledge import SearchStrategy, ChunkingStrategy, ProcessingStatus


@dataclass
class DocumentIngestionRequest:
    """文档摄取请求DTO"""
    source_location: Optional[StorageLocation]
    title: Optional[str] = None
    content_type: str = "text/plain"
    metadata: Optional[Dict[str, Any]] = None
    process_immediately: bool = False
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass  
class DocumentProcessingRequest:
    """文档处理请求DTO"""
    document_id: str
    generate_embeddings: bool = True
    chunking_strategy: Optional[ChunkingStrategy] = None
    chunk_size: Optional[int] = None
    chunk_overlap: Optional[int] = None
    
    def __post_init__(self):
        if self.chunking_strategy is None:
            self.chunking_strategy = ChunkingStrategy.FIXED_SIZE
        if self.chunk_size is None:
            self.chunk_size = 1000
        if self.chunk_overlap is None:
            self.chunk_overlap = 200


@dataclass
class SearchRequest:
    """搜索请求DTO"""
    query_text: str
    strategy: SearchStrategy = SearchStrategy.SEMANTIC
    max_results: int = 10
    filters: Optional[Dict[str, Any]] = None
    include_metadata: bool = True
    
    def __post_init__(self):
        if self.filters is None:
            self.filters = {}


@dataclass
class DocumentListRequest:
    """文档列表请求DTO"""
    status_filter: Optional[ProcessingStatus] = None
    limit: Optional[int] = None
    offset: Optional[int] = None
    sort_by: str = "created_at"
    sort_order: str = "desc"
    
    def __post_init__(self):
        if self.limit is None:
            self.limit = 50
        if self.offset is None:
            self.offset = 0


@dataclass
class BatchIngestionRequest:
    """批量摄取请求DTO"""
    requests: List[DocumentIngestionRequest]
    max_concurrent: int = 5
    fail_fast: bool = False
    
    def __post_init__(self):
        if not self.requests:
            raise ValueError("Batch ingestion requests cannot be empty")


@dataclass
class DocumentUpdateRequest:
    """文档更新请求DTO"""
    document_id: str
    title: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    reprocess: bool = False


@dataclass
class DocumentDeleteRequest:
    """文档删除请求DTO"""
    document_id: str
    delete_vectors: bool = True
    cascade_delete: bool = False