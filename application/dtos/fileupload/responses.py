"""
File Upload Response DTOs

This module contains all response Data Transfer Objects for file upload operations.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class SignedUrlResponse:
    """Response DTO for signed URL generation."""
    file_id: str
    upload_url: str
    upload_session_id: str
    expires_at: datetime
    multipart_upload_id: Optional[str] = None
    chunk_size: Optional[int] = None
    max_chunks: Optional[int] = None


@dataclass
class UploadSessionResponse:
    """Response DTO for upload session information."""
    session_id: str
    file_id: str
    status: str
    progress_percentage: float
    uploaded_size: int
    expected_size: int
    uploaded_chunks: int
    total_chunks: int
    next_chunk_number: Optional[int] = None
    expires_at: Optional[datetime] = None
    is_resumable: bool = True


@dataclass
class FileResponse:
    """Response DTO for file information."""
    id: str
    original_name: str
    file_size: int
    content_type: str
    status: str
    access_level: str
    download_count: int
    owner_id: str
    category: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_accessed_at: Optional[datetime] = None
    is_available: bool = True
    is_public: bool = False
    file_size_mb: float = 0.0
    age_days: int = 0


@dataclass
class UploadCompletionResponse:
    """Response DTO for upload completion confirmation."""
    file_id: str
    status: str
    processing_started: bool
    task_ids: List[str] = field(default_factory=list)
    message: str = ""
    verification_result: Optional[Dict[str, Any]] = None


@dataclass
class DownloadResponse:
    """Response DTO for file download."""
    file_id: str
    download_url: str
    expires_at: datetime
    file_metadata: Dict[str, Any]
    access_type: str = "direct"
    content_disposition: str = "attachment"


@dataclass
class FileListResponse:
    """Response DTO for file list."""
    files: List[FileResponse]
    total_count: int
    limit: int
    offset: int
    has_more: bool


@dataclass
class FileStatsResponse:
    """Response DTO for file statistics."""
    total_files: int
    total_size_bytes: int
    total_size_mb: float
    files_by_status: Dict[str, int]
    files_by_access_level: Dict[str, int]
    files_by_content_type: Dict[str, int]
    average_file_size_mb: float
    total_downloads: int
    most_downloaded_files: List[FileResponse]
    recent_uploads: List[FileResponse]
    storage_usage_by_category: Dict[str, int]


@dataclass
class ErrorResponse:
    """Response DTO for errors."""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)