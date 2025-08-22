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
    RUNNING = "running"
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

    FILE_UPLOAD = "file_upload"  # File upload
    FILE_UPLOAD_CONFIRM = "file_upload_confirm"  # File upload confirmation
    FILE_PROCESSING = "file_processing"  # File processing
    TOPIC_CREATION = "topic_creation"  # Topic creation
    TOPIC_PROCESSING = "topic_processing"  # Topic processing
    SEARCH = "search"  # Search
    ORCHESTRATION = "orchestration"  # Orchestration processing
