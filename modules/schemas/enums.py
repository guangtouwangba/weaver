"""
Enum definitions

Centrally define all enum types used throughout the system.
"""

from enum import Enum


class FileStatus(str, Enum):
    """File status enum - matches database file_status_enum"""

    UPLOADING = "uploading"  # Uploading
    AVAILABLE = "available"  # Available
    PROCESSING = "processing"  # Processing
    FAILED = "failed"  # Processing failed
    DELETED = "deleted"  # Deleted
    QUARANTINED = "quarantined"  # Quarantined


class TopicStatus(str, Enum):
    """Topic status enum - matches database topic_status_enum"""

    ACTIVE = "active"  # Active
    ARCHIVED = "archived"  # Archived
    DRAFT = "draft"  # Draft
    COMPLETED = "completed"  # Completed


class ContentType(str, Enum):
    """Content type enum"""

    TEXT = "text"
    TXT = "txt"
    PDF = "pdf"
    DOC = "doc"
    DOCX = "docx"
    HTML = "html"
    MD = "md"
    JSON = "json"
    CSV = "csv"
    XML = "xml"
    RTF = "rtf"


class ChunkingStrategy(str, Enum):
    """Chunking strategy enum"""

    FIXED_SIZE = "fixed_size"  # Fixed size
    SENTENCE = "sentence"  # By sentence
    PARAGRAPH = "paragraph"  # By paragraph
    SEMANTIC = "semantic"  # Semantic chunking
    RECURSIVE = "recursive"  # Recursive chunking


class ProcessingStatus(str, Enum):
    """Processing status enum"""

    PENDING = "pending"
    PROCESSING = "processing"  # Standardize on this from models.py
    RUNNING = "running"  # Keep for backward compatibility
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SearchType(str, Enum):
    """Search type enum"""

    SEMANTIC = "semantic"  # Semantic search
    KEYWORD = "keyword"  # Keyword search
    HYBRID = "hybrid"  # Hybrid search
    EXACT = "exact"  # Exact search


class TaskName(str, Enum):
    """Task name enum"""

    # File related tasks
    FILE_UPLOAD = "file_upload"  # File upload
    FILE_UPLOAD_CONFIRM = "file_upload_confirm"  # File upload confirmation
    FILE_PROCESSING = "file_processing"  # File processing
    FILE_ANALYZE_CONTENT = "file.analyze_content"  # File content analysis
    FILE_CLEANUP_TEMP = "file.cleanup_temp"  # Temporary file cleanup
    FILE_CONVERT_FORMAT = "file.convert_format"  # File format conversion
    
    # Document related tasks
    DOCUMENT_CREATE = "document.create"  # Document creation
    DOCUMENT_UPDATE_METADATA = "document.update_metadata"  # Document metadata update
    
    # RAG related tasks
    RAG_PROCESS_DOCUMENT = "rag.process_document"  # RAG document processing
    RAG_PROCESS_DOCUMENT_ASYNC = "rag.process_document_async"  # RAG async document processing
    RAG_GENERATE_EMBEDDINGS = "rag.generate_embeddings"  # Generate embeddings
    RAG_STORE_VECTORS = "rag.store_vectors"  # Store vectors
    RAG_SEMANTIC_SEARCH = "rag.semantic_search"  # Semantic search
    RAG_CLEANUP_DOCUMENT = "rag.cleanup_document"  # Cleanup document
    
    # Summary related tasks
    SUMMARY_GENERATE_DOCUMENT = "summary.generate_document"  # Generate document summary
    SUMMARY_UPDATE_INDEX = "summary.update_index"  # Update summary index
    
    # Topic related tasks
    TOPIC_CREATION = "topic_creation"  # Topic creation
    TOPIC_PROCESSING = "topic_processing"  # Topic processing
    
    # Search and orchestration tasks
    SEARCH = "search"  # Search
    ORCHESTRATION = "orchestration"  # Orchestration processing
