"""
RAG Response DTOs

This module contains all response Data Transfer Objects for RAG operations.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, field

from domain.rag_interfaces import ProcessingStatus, SearchStrategy


@dataclass
class ProcessingResponse:
    """Response DTO for document processing operations."""
    success: bool
    document_id: Optional[str] = None
    task_id: Optional[str] = None
    status: ProcessingStatus = ProcessingStatus.PENDING
    message: str = ""
    
    # Processing details
    chunks_created: int = 0
    processing_time_ms: float = 0.0
    file_size_bytes: int = 0
    
    # Error information
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class BatchProcessingResponse:
    """Response DTO for batch processing operations."""
    total_documents: int
    successful: int = 0
    failed: int = 0
    in_progress: int = 0
    
    # Individual results
    results: List[ProcessingResponse] = field(default_factory=list)
    
    # Summary statistics
    total_processing_time_ms: float = 0.0
    average_processing_time_ms: float = 0.0
    total_chunks_created: int = 0
    
    # Overall status
    batch_status: str = "completed"  # completed, partial, failed
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


@dataclass
class DocumentChunkResponse:
    """Response DTO for document chunks."""
    id: str
    document_id: str
    content: str
    chunk_index: int
    start_position: int
    end_position: int
    embedding_id: Optional[str] = None
    similarity_score: Optional[float] = None
    
    # Highlighting (for search results)
    highlighted_content: Optional[str] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class DocumentResponse:
    """Response DTO for document information."""
    id: str
    title: str
    content: Optional[str] = None  # May be truncated for large documents
    file_type: str = ""
    file_size: int = 0
    file_path: Optional[str] = None
    
    # Status and processing info
    status: ProcessingStatus = ProcessingStatus.PENDING
    processing_result: Optional[ProcessingResponse] = None
    
    # Content metadata
    author: Optional[str] = None
    category: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    language: Optional[str] = None
    
    # Statistics
    chunk_count: int = 0
    word_count: int = 0
    character_count: int = 0
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_accessed_at: Optional[datetime] = None
    
    # Custom metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Document summary (if available)
    summary: Optional[str] = None
    
    # Embedding information
    has_embeddings: bool = False
    embedding_model: Optional[str] = None


@dataclass
class SearchResultItem:
    """Individual search result item."""
    chunk: DocumentChunkResponse
    document: DocumentResponse
    relevance_score: float
    rank: int
    
    # Search-specific metadata
    match_type: str = "semantic"  # semantic, keyword, hybrid
    highlighted_passages: List[str] = field(default_factory=list)
    explanation: Optional[str] = None  # Why this result was returned


@dataclass
class SearchResponse:
    """Response DTO for search operations."""
    query: str
    strategy: SearchStrategy
    results: List[SearchResultItem] = field(default_factory=list)
    
    # Search statistics
    total_found: int = 0
    retrieved_count: int = 0
    search_time_ms: float = 0.0
    
    # Score statistics
    max_score: float = 0.0
    min_score: float = 0.0
    avg_score: float = 0.0
    
    # Query processing info
    processed_query: Optional[str] = None
    expanded_terms: List[str] = field(default_factory=list)
    query_intent: Optional[str] = None
    
    # Filters applied
    filters_applied: Dict[str, Any] = field(default_factory=dict)
    
    # Suggestions
    suggestions: List[str] = field(default_factory=list)
    corrections: List[str] = field(default_factory=list)
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class IndexResponse:
    """Response DTO for index operations."""
    name: str
    status: str = "active"  # active, creating, updating, error
    description: Optional[str] = None
    
    # Configuration
    embedding_model: str = ""
    dimension: int = 0
    distance_metric: str = ""
    
    # Statistics
    document_count: int = 0
    chunk_count: int = 0
    size_bytes: int = 0
    
    # Performance metrics
    search_performance_ms: Dict[str, float] = field(default_factory=dict)
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_indexed_at: Optional[datetime] = None
    
    # Configuration details
    configuration: Dict[str, Any] = field(default_factory=dict)
    
    # Health status
    health_status: str = "healthy"  # healthy, warning, error
    health_details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DocumentListResponse:
    """Response DTO for document listing."""
    documents: List[DocumentResponse] = field(default_factory=list)
    total_count: int = 0
    limit: int = 50
    offset: int = 0
    has_more: bool = False
    
    # Aggregations
    status_distribution: Dict[str, int] = field(default_factory=dict)
    category_distribution: Dict[str, int] = field(default_factory=dict)
    author_distribution: Dict[str, int] = field(default_factory=dict)
    
    # Statistics
    total_size_bytes: int = 0
    total_chunks: int = 0
    
    # Query metadata
    query_time_ms: float = 0.0
    filters_applied: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EmbeddingResponse:
    """Response DTO for embedding operations."""
    embeddings: List[List[float]] = field(default_factory=list)
    model: str = ""
    dimension: int = 0
    
    # Processing info
    processing_time_ms: float = 0.0
    tokens_consumed: int = 0
    
    # Statistics
    input_count: int = 0
    successful: int = 0
    failed: int = 0
    
    # Error information
    errors: List[str] = field(default_factory=list)
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SimilaritySearchResponse:
    """Response DTO for similarity search operations."""
    results: List[SearchResultItem] = field(default_factory=list)
    query_embedding: Optional[List[float]] = None
    
    # Search statistics
    total_candidates: int = 0
    retrieved_count: int = 0
    search_time_ms: float = 0.0
    
    # Score distribution
    score_distribution: Dict[str, float] = field(default_factory=dict)
    
    # Search parameters used
    similarity_threshold: float = 0.0
    distance_metric: str = ""
    
    # Metadata
    index_name: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemHealthResponse:
    """Response DTO for system health information."""
    overall_status: str = "healthy"  # healthy, degraded, unhealthy
    components: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Performance metrics
    response_times: Dict[str, float] = field(default_factory=dict)
    throughput: Dict[str, float] = field(default_factory=dict)
    
    # Resource usage
    memory_usage: Dict[str, float] = field(default_factory=dict)
    disk_usage: Dict[str, float] = field(default_factory=dict)
    
    # System statistics
    system_stats: Dict[str, Any] = field(default_factory=dict)
    
    # Health check details
    last_check: datetime = field(default_factory=datetime.utcnow)
    check_duration_ms: float = 0.0
    
    # Alerts and warnings
    alerts: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class AnalyticsResponse:
    """Response DTO for analytics and statistics."""
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    
    # Document statistics
    document_stats: Dict[str, int] = field(default_factory=dict)
    
    # Search statistics
    search_stats: Dict[str, Any] = field(default_factory=dict)
    
    # Storage statistics
    storage_stats: Dict[str, Any] = field(default_factory=dict)
    
    # Performance metrics
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    
    # Trending data
    trends: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    
    # User behavior
    usage_patterns: Dict[str, Any] = field(default_factory=dict)
    
    # Time series data
    time_series: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)


@dataclass
class ExportResponse:
    """Response DTO for export operations."""
    export_id: str
    status: str = "completed"  # pending, in_progress, completed, failed
    format: str = "json"
    
    # Export details
    document_count: int = 0
    file_size_bytes: int = 0
    compression_ratio: Optional[float] = None
    
    # Download information
    download_url: Optional[str] = None
    expires_at: Optional[datetime] = None
    
    # Processing information
    processing_time_ms: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    # Error information
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class ImportResponse:
    """Response DTO for import operations."""
    import_id: str
    status: str = "completed"  # pending, in_progress, completed, failed
    format: str = "json"
    
    # Import statistics
    total_records: int = 0
    successful_imports: int = 0
    failed_imports: int = 0
    skipped_records: int = 0
    
    # Processing information
    processing_time_ms: float = 0.0
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    # Validation results
    validation_errors: List[str] = field(default_factory=list)
    validation_warnings: List[str] = field(default_factory=list)
    
    # Import details
    imported_document_ids: List[str] = field(default_factory=list)
    failed_records: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ErrorResponse:
    """Response DTO for error information."""
    error_code: str
    error_message: str
    error_type: str = "ValidationError"
    
    # Detailed error information
    details: Dict[str, Any] = field(default_factory=dict)
    suggestions: List[str] = field(default_factory=list)
    
    # Context information
    request_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Stack trace (for development)
    stack_trace: Optional[str] = None


@dataclass
class TaskStatusResponse:
    """Response DTO for async task status."""
    task_id: str
    status: ProcessingStatus
    progress_percentage: float = 0.0
    
    # Task details
    task_type: str = ""
    description: str = ""
    
    # Progress information
    current_step: Optional[str] = None
    total_steps: Optional[int] = None
    completed_steps: int = 0
    
    # Results (if completed)
    result: Optional[Dict[str, Any]] = None
    
    # Error information (if failed)
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    
    # Timing information
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)