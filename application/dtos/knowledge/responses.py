"""
Knowledge Management Response DTOs

输出数据传输对象，用于应用层向API层返回数据。
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime

# 导入Domain层的枚举
from domain.knowledge import ProcessingStatus, SearchStrategy


@dataclass
class DocumentIngestionResponse:
    """文档摄取响应DTO"""
    success: bool
    document_id: Optional[str] = None
    status: ProcessingStatus = ProcessingStatus.PENDING
    message: str = ""
    processing_time_ms: float = 0.0
    errors: List[str] = field(default_factory=list)


@dataclass
class DocumentProcessingResponse:
    """文档处理响应DTO"""
    success: bool
    document_id: str
    status: ProcessingStatus
    message: str = ""
    chunks_created: int = 0
    processing_time_ms: float = 0.0
    errors: List[str] = field(default_factory=list)


@dataclass
class DocumentSummaryResponse:
    """文档摘要响应DTO"""
    id: str
    title: str
    content_type: str
    status: ProcessingStatus
    chunk_count: int
    word_count: int
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchResultItemResponse:
    """搜索结果项响应DTO"""
    chunk_id: str
    document_id: str
    content: str
    relevance_score: float
    rank: int
    document_title: str
    document_metadata: Dict[str, Any] = field(default_factory=dict)
    explanation: Optional[str] = None


@dataclass
class SearchResponse:
    """搜索响应DTO"""
    success: bool
    query: str
    strategy: str
    results: List[SearchResultItemResponse] = field(default_factory=list)
    total_found: int = 0
    search_time_ms: float = 0.0
    max_score: float = 0.0
    min_score: float = 0.0
    avg_score: float = 0.0
    errors: List[str] = field(default_factory=list)


@dataclass
class DocumentListResponse:
    """文档列表响应DTO"""
    success: bool
    documents: List[DocumentSummaryResponse] = field(default_factory=list)
    total_count: int = 0
    limit: int = 50
    offset: int = 0
    has_more: bool = False
    errors: List[str] = field(default_factory=list)


@dataclass
class BatchIngestionResponse:
    """批量摄取响应DTO"""
    success: bool
    total_documents: int
    successful: int = 0
    failed: int = 0
    results: List[DocumentIngestionResponse] = field(default_factory=list)
    processing_time_ms: float = 0.0
    errors: List[str] = field(default_factory=list)


@dataclass
class SystemHealthResponse:
    """系统健康状态响应DTO"""
    overall_status: str
    components: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    check_duration_ms: float = 0.0
    alerts: List[str] = field(default_factory=list)


@dataclass
class ProcessingStatisticsResponse:
    """处理统计响应DTO"""
    total_documents: int
    pending_count: int
    processing_count: int
    completed_count: int
    failed_count: int
    avg_processing_time_ms: float
    total_chunks: int
    total_vectors: int