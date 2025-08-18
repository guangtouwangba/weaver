"""
RAG Request DTOs

This module contains all request Data Transfer Objects for RAG operations.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

from domain.rag_interfaces import SearchStrategy, ProcessingStatus


class DocumentFormat(str, Enum):
    """Supported document formats."""
    TEXT = "text"
    PDF = "pdf"
    DOCX = "docx"
    HTML = "html"
    MARKDOWN = "markdown"
    JSON = "json"
    CSV = "csv"


class ChunkStrategy(str, Enum):
    """Document chunking strategies."""
    FIXED_SIZE = "fixed_size"
    SEMANTIC = "semantic"
    SENTENCE = "sentence"
    PARAGRAPH = "paragraph"
    RECURSIVE = "recursive"


@dataclass
class DocumentIngestionRequest:
    """Request DTO for document ingestion."""
    source: str  # File path, URL, or content
    source_type: str = "file"  # file, url, content
    document_format: Optional[DocumentFormat] = None
    title: Optional[str] = None
    author: Optional[str] = None
    category: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Processing configuration
    chunk_strategy: ChunkStrategy = ChunkStrategy.FIXED_SIZE
    chunk_size: int = 1000
    chunk_overlap: int = 200
    enable_ocr: bool = False
    extract_images: bool = False
    
    # Indexing configuration
    index_name: Optional[str] = None
    enable_auto_tagging: bool = True
    enable_summary: bool = True
    
    def __post_init__(self):
        """Validate request data."""
        if not self.source:
            raise ValueError("Source cannot be empty")
        if self.chunk_size <= 0:
            raise ValueError("Chunk size must be positive")
        if self.chunk_overlap < 0:
            raise ValueError("Chunk overlap cannot be negative")
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("Chunk overlap must be less than chunk size")


@dataclass
class BatchIngestionRequest:
    """Request DTO for batch document ingestion."""
    sources: List[str]
    common_config: Optional[DocumentIngestionRequest] = None
    per_source_config: Optional[Dict[str, DocumentIngestionRequest]] = None
    max_parallel: int = 5
    fail_fast: bool = False
    
    def __post_init__(self):
        """Validate request data."""
        if not self.sources:
            raise ValueError("Sources list cannot be empty")
        if self.max_parallel <= 0:
            raise ValueError("Max parallel must be positive")


@dataclass
class SearchRequest:
    """Request DTO for knowledge search."""
    query: str
    strategy: SearchStrategy = SearchStrategy.SEMANTIC
    top_k: int = 10
    similarity_threshold: float = 0.7
    
    # Filters
    document_ids: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    authors: Optional[List[str]] = None
    file_types: Optional[List[str]] = None
    
    # Hybrid search configuration
    semantic_weight: float = 0.7
    keyword_weight: float = 0.3
    
    # Advanced options
    enable_reranking: bool = True
    enable_highlighting: bool = True
    include_metadata: bool = True
    expand_query: bool = False
    
    def __post_init__(self):
        """Validate request data."""
        if not self.query or not self.query.strip():
            raise ValueError("Query cannot be empty")
        if self.top_k <= 0:
            raise ValueError("Top K must be positive")
        if not 0 <= self.similarity_threshold <= 1:
            raise ValueError("Similarity threshold must be between 0 and 1")
        if not 0 <= self.semantic_weight <= 1:
            raise ValueError("Semantic weight must be between 0 and 1")
        if not 0 <= self.keyword_weight <= 1:
            raise ValueError("Keyword weight must be between 0 and 1")
        if abs((self.semantic_weight + self.keyword_weight) - 1.0) > 0.01:
            raise ValueError("Semantic weight + keyword weight must equal 1.0")


@dataclass
class CreateIndexRequest:
    """Request DTO for creating a new index."""
    name: str
    description: Optional[str] = None
    embedding_model: str = "text-embedding-ada-002"
    dimension: int = 1536
    distance_metric: str = "cosine"  # cosine, euclidean, dot_product
    configuration: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate request data."""
        if not self.name or not self.name.strip():
            raise ValueError("Index name cannot be empty")
        if self.dimension <= 0:
            raise ValueError("Dimension must be positive")
        if self.distance_metric not in ["cosine", "euclidean", "dot_product"]:
            raise ValueError("Invalid distance metric")


@dataclass
class UpdateDocumentRequest:
    """Request DTO for updating a document."""
    document_id: str
    title: Optional[str] = None
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = None
    
    # Processing options
    reprocess: bool = False
    reindex: bool = False
    preserve_chunks: bool = True
    
    def __post_init__(self):
        """Validate request data."""
        if not self.document_id:
            raise ValueError("Document ID cannot be empty")
        if not any([self.title, self.content, self.metadata, self.tags, self.category]):
            raise ValueError("At least one field must be provided for update")


@dataclass
class DeleteDocumentRequest:
    """Request DTO for deleting a document."""
    document_id: str
    hard_delete: bool = False  # If False, soft delete (mark as deleted)
    delete_from_vector_store: bool = True
    delete_chunks: bool = True
    
    def __post_init__(self):
        """Validate request data."""
        if not self.document_id:
            raise ValueError("Document ID cannot be empty")


@dataclass
class DocumentListRequest:
    """Request DTO for listing documents."""
    limit: int = 50
    offset: int = 0
    sort_by: str = "created_at"  # created_at, updated_at, title, file_size
    sort_order: str = "desc"  # asc, desc
    
    # Filters
    status: Optional[ProcessingStatus] = None
    categories: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    authors: Optional[List[str]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    search_text: Optional[str] = None
    
    def __post_init__(self):
        """Validate request data."""
        if self.limit <= 0 or self.limit > 1000:
            raise ValueError("Limit must be between 1 and 1000")
        if self.offset < 0:
            raise ValueError("Offset cannot be negative")
        if self.sort_by not in ["created_at", "updated_at", "title", "file_size"]:
            raise ValueError("Invalid sort_by field")
        if self.sort_order not in ["asc", "desc"]:
            raise ValueError("Sort order must be 'asc' or 'desc'")


@dataclass
class EmbeddingRequest:
    """Request DTO for generating embeddings."""
    texts: List[str]
    model: str = "text-embedding-ada-002"
    normalize: bool = True
    
    def __post_init__(self):
        """Validate request data."""
        if not self.texts:
            raise ValueError("Texts list cannot be empty")
        if any(not text.strip() for text in self.texts):
            raise ValueError("All texts must be non-empty")


@dataclass
class SimilaritySearchRequest:
    """Request DTO for similarity search using embeddings."""
    embedding: List[float]
    top_k: int = 10
    similarity_threshold: float = 0.0
    index_name: Optional[str] = None
    document_ids: Optional[List[str]] = None
    metadata_filters: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Validate request data."""
        if not self.embedding:
            raise ValueError("Embedding cannot be empty")
        if self.top_k <= 0:
            raise ValueError("Top K must be positive")
        if not 0 <= self.similarity_threshold <= 1:
            raise ValueError("Similarity threshold must be between 0 and 1")


@dataclass
class AnalyticsRequest:
    """Request DTO for analytics and statistics."""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    metrics: List[str] = field(default_factory=lambda: ["documents", "searches", "storage"])
    group_by: Optional[str] = None  # day, week, month, category, author
    include_details: bool = False
    
    def __post_init__(self):
        """Validate request data."""
        if self.metrics and not all(m in ["documents", "searches", "storage", "performance"] for m in self.metrics):
            raise ValueError("Invalid metrics specified")
        if self.group_by and self.group_by not in ["day", "week", "month", "category", "author"]:
            raise ValueError("Invalid group_by value")


@dataclass
class SystemHealthRequest:
    """Request DTO for system health check."""
    check_components: List[str] = field(default_factory=lambda: ["all"])
    include_metrics: bool = True
    include_performance: bool = False
    detailed: bool = False
    
    def __post_init__(self):
        """Validate request data."""
        valid_components = ["all", "vector_store", "index", "embedding", "storage", "database"]
        if not all(c in valid_components for c in self.check_components):
            raise ValueError("Invalid component specified")


@dataclass
class ExportRequest:
    """Request DTO for exporting documents and data."""
    format: str = "json"  # json, csv, parquet
    document_ids: Optional[List[str]] = None
    filters: Optional[Dict[str, Any]] = None
    include_embeddings: bool = False
    include_chunks: bool = True
    include_metadata: bool = True
    compression: bool = True
    
    def __post_init__(self):
        """Validate request data."""
        if self.format not in ["json", "csv", "parquet"]:
            raise ValueError("Invalid export format")


@dataclass
class ImportRequest:
    """Request DTO for importing documents and data."""
    source: str  # File path or URL
    format: str = "json"  # json, csv, parquet
    mapping: Optional[Dict[str, str]] = None  # Field mapping
    batch_size: int = 100
    overwrite_existing: bool = False
    validate_schema: bool = True
    
    def __post_init__(self):
        """Validate request data."""
        if not self.source:
            raise ValueError("Source cannot be empty")
        if self.format not in ["json", "csv", "parquet"]:
            raise ValueError("Invalid import format")
        if self.batch_size <= 0:
            raise ValueError("Batch size must be positive")