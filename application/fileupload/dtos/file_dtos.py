"""
Data Transfer Objects for file upload application.

This module defines all request and response DTOs for the file upload API,
providing clear contracts for client-server communication.
"""

from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from ..domain.value_objects import AccessLevel, FileStatus, UploadStatus


# Request DTOs

@dataclass
class GetSignedUrlRequest:
    """Request DTO for generating signed upload URL."""
    filename: str
    file_size: int
    content_type: str
    access_level: AccessLevel = AccessLevel.PRIVATE
    expires_in_hours: int = 1
    category: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    enable_multipart: bool = True
    topic_id: Optional[int] = None  # Link file to a specific topic
    
    def __post_init__(self):
        """Validate request data."""
        if not self.filename:
            raise ValueError("Filename cannot be empty")
        if self.file_size <= 0:
            raise ValueError("File size must be positive")
        if not self.content_type:
            raise ValueError("Content type cannot be empty")
        if self.expires_in_hours <= 0 or self.expires_in_hours > 24:
            raise ValueError("Expiration hours must be between 1 and 24")


@dataclass
class InitiateUploadRequest:
    """Request DTO for initiating a new upload session."""
    filename: str
    file_size: int
    content_type: str
    access_level: AccessLevel = AccessLevel.PRIVATE
    chunk_size: int = 5 * 1024 * 1024  # 5MB default
    category: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate request data."""
        if not self.filename:
            raise ValueError("Filename cannot be empty")
        if self.file_size <= 0:
            raise ValueError("File size must be positive")
        if self.chunk_size <= 0:
            raise ValueError("Chunk size must be positive")


@dataclass
class CompleteUploadRequest:
    """Request DTO for completing an upload session."""
    upload_session_id: str
    file_hash: Optional[str] = None
    
    def __post_init__(self):
        """Validate request data."""
        if not self.upload_session_id:
            raise ValueError("Upload session ID cannot be empty")


@dataclass
class DownloadFileRequest:
    """Request DTO for file download."""
    file_id: str
    expires_in_hours: int = 1
    access_type: str = "direct"  # direct, redirect, inline
    force_download: bool = False
    
    def __post_init__(self):
        """Validate request data."""
        if not self.file_id:
            raise ValueError("File ID cannot be empty")
        if self.expires_in_hours <= 0 or self.expires_in_hours > 168:  # Max 1 week
            raise ValueError("Expiration hours must be between 1 and 168")
        if self.access_type not in ["direct", "redirect", "inline"]:
            raise ValueError("Access type must be one of: direct, redirect, inline")


@dataclass
class UpdateFileAccessRequest:
    """Request DTO for updating file access permissions."""
    file_id: str
    access_level: AccessLevel
    expires_at: Optional[datetime] = None
    allowed_users: List[str] = field(default_factory=list)
    allowed_groups: List[str] = field(default_factory=list)
    max_downloads: Optional[int] = None
    
    def __post_init__(self):
        """Validate request data."""
        if not self.file_id:
            raise ValueError("File ID cannot be empty")
        if self.max_downloads is not None and self.max_downloads < 0:
            raise ValueError("Max downloads cannot be negative")


@dataclass
class FileSearchRequest:
    """Request DTO for searching files."""
    query: Optional[str] = None
    category: Optional[str] = None
    content_type: Optional[str] = None
    status: Optional[FileStatus] = None
    access_level: Optional[AccessLevel] = None
    owner_id: Optional[str] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    size_min: Optional[int] = None
    size_max: Optional[int] = None
    tags: List[str] = field(default_factory=list)
    limit: int = 50
    offset: int = 0
    sort_by: str = "created_at"
    sort_order: str = "desc"
    
    def __post_init__(self):
        """Validate search parameters."""
        if self.limit <= 0 or self.limit > 1000:
            raise ValueError("Limit must be between 1 and 1000")
        if self.offset < 0:
            raise ValueError("Offset cannot be negative")
        if self.sort_by not in ["created_at", "updated_at", "file_size", "download_count", "name"]:
            raise ValueError("Invalid sort field")
        if self.sort_order not in ["asc", "desc"]:
            raise ValueError("Sort order must be 'asc' or 'desc'")


# Response DTOs

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
    
    @classmethod
    def from_domain(cls, file_entity, upload_session, signed_url: str) -> 'SignedUrlResponse':
        """Create response from domain objects."""
        return cls(
            file_id=file_entity.id,
            upload_url=signed_url,
            upload_session_id=upload_session.id,
            expires_at=upload_session.expires_at,
            multipart_upload_id=upload_session.upload_id,
            chunk_size=upload_session.chunk_size,
            max_chunks=upload_session.max_chunks
        )


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
    next_chunk_number: int
    expires_at: datetime
    is_resumable: bool
    
    @classmethod
    def from_domain(cls, upload_session) -> 'UploadSessionResponse':
        """Create response from domain object."""
        return cls(
            session_id=upload_session.id,
            file_id=upload_session.file_id,
            status=upload_session.status.value,
            progress_percentage=upload_session.progress_percentage,
            uploaded_size=upload_session.uploaded_size,
            expected_size=upload_session.expected_size,
            uploaded_chunks=len(upload_session.uploaded_chunks),
            total_chunks=upload_session.max_chunks or 0,
            next_chunk_number=upload_session.next_chunk_number,
            expires_at=upload_session.expires_at,
            is_resumable=upload_session.is_resumable
        )


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
    owner_id: Optional[str]
    category: Optional[str]
    tags: List[str]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    last_accessed_at: Optional[datetime]
    is_available: bool
    is_public: bool
    file_size_mb: float
    age_days: int
    
    @classmethod
    def from_domain(cls, file_entity) -> 'FileResponse':
        """Create response from domain object."""
        return cls(
            id=file_entity.id,
            original_name=file_entity.metadata.original_name if file_entity.metadata else "",
            file_size=file_entity.metadata.file_size if file_entity.metadata else 0,
            content_type=file_entity.metadata.content_type if file_entity.metadata else "",
            status=file_entity.status.value,
            access_level=file_entity.access_permission.level.value,
            download_count=file_entity.download_count,
            owner_id=file_entity.owner_id,
            category=file_entity.metadata.category if file_entity.metadata else None,
            tags=list(file_entity.metadata.tags) if file_entity.metadata else [],
            metadata=file_entity.metadata.custom_attributes if file_entity.metadata else {},
            created_at=file_entity.created_at,
            updated_at=file_entity.updated_at,
            last_accessed_at=file_entity.last_accessed_at,
            is_available=file_entity.is_available,
            is_public=file_entity.is_public,
            file_size_mb=file_entity.file_size_mb,
            age_days=file_entity.age_days
        )


@dataclass
class DownloadResponse:
    """Response DTO for file download."""
    file_id: str
    download_url: str
    expires_at: datetime
    file_metadata: Dict[str, Any]
    access_type: str
    content_disposition: str
    
    @classmethod
    def from_domain(cls, file_entity, download_url: str, expires_at: datetime, 
                   access_type: str = "direct", force_download: bool = False) -> 'DownloadResponse':
        """Create response from domain object."""
        content_disposition = "attachment" if force_download else "inline"
        
        return cls(
            file_id=file_entity.id,
            download_url=download_url,
            expires_at=expires_at,
            file_metadata={
                "original_name": file_entity.metadata.original_name if file_entity.metadata else "",
                "file_size": file_entity.metadata.file_size if file_entity.metadata else 0,
                "content_type": file_entity.metadata.content_type if file_entity.metadata else "",
                "uploaded_at": file_entity.created_at.isoformat()
            },
            access_type=access_type,
            content_disposition=content_disposition
        )


@dataclass
class FileListResponse:
    """Response DTO for file listing."""
    files: List[FileResponse]
    total_count: int
    limit: int
    offset: int
    has_more: bool
    
    @classmethod
    def from_domain(cls, file_entities: List, total_count: int, 
                   limit: int, offset: int) -> 'FileListResponse':
        """Create response from domain objects."""
        file_responses = [FileResponse.from_domain(file_entity) for file_entity in file_entities]
        has_more = offset + len(file_entities) < total_count
        
        return cls(
            files=file_responses,
            total_count=total_count,
            limit=limit,
            offset=offset,
            has_more=has_more
        )


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
    most_downloaded_files: List[Dict[str, Any]]
    recent_uploads: List[Dict[str, Any]]
    storage_usage_by_category: Dict[str, float]
    
    @classmethod
    def create(cls, stats_data: Dict[str, Any]) -> 'FileStatsResponse':
        """Create response from statistics data."""
        total_size_bytes = stats_data.get('total_size_bytes', 0)
        total_files = stats_data.get('total_files', 0)
        
        return cls(
            total_files=total_files,
            total_size_bytes=total_size_bytes,
            total_size_mb=total_size_bytes / (1024 * 1024) if total_size_bytes > 0 else 0,
            files_by_status=stats_data.get('files_by_status', {}),
            files_by_access_level=stats_data.get('files_by_access_level', {}),
            files_by_content_type=stats_data.get('files_by_content_type', {}),
            average_file_size_mb=stats_data.get('average_file_size_mb', 0),
            total_downloads=stats_data.get('total_downloads', 0),
            most_downloaded_files=stats_data.get('most_downloaded_files', []),
            recent_uploads=stats_data.get('recent_uploads', []),
            storage_usage_by_category=stats_data.get('storage_usage_by_category', {})
        )


@dataclass
class ErrorResponse:
    """Response DTO for API errors."""
    error: str
    message: str
    code: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    @classmethod
    def validation_error(cls, message: str, details: Dict[str, Any] = None) -> 'ErrorResponse':
        """Create validation error response."""
        return cls(
            error="validation_error",
            message=message,
            code="VALIDATION_FAILED",
            details=details
        )
    
    @classmethod
    def not_found_error(cls, resource: str, resource_id: str) -> 'ErrorResponse':
        """Create not found error response."""
        return cls(
            error="not_found",
            message=f"{resource} with ID {resource_id} not found",
            code="RESOURCE_NOT_FOUND",
            details={"resource": resource, "id": resource_id}
        )
    
    @classmethod
    def access_denied_error(cls, message: str = "Access denied") -> 'ErrorResponse':
        """Create access denied error response."""
        return cls(
            error="access_denied",
            message=message,
            code="ACCESS_DENIED"
        )
    
    @classmethod
    def internal_error(cls, message: str = "Internal server error") -> 'ErrorResponse':
        """Create internal server error response."""
        return cls(
            error="internal_error",
            message=message,
            code="INTERNAL_ERROR"
        )


# Utility DTOs

@dataclass
class ChunkUploadInfo:
    """Information for uploading a specific chunk."""
    chunk_number: int
    upload_url: str
    start_byte: int
    end_byte: int
    chunk_size: int
    
    @classmethod
    def create(cls, chunk_number: int, upload_url: str, 
              chunk_size: int, total_file_size: int) -> 'ChunkUploadInfo':
        """Create chunk upload info."""
        start_byte = chunk_number * chunk_size
        end_byte = min(start_byte + chunk_size - 1, total_file_size - 1)
        actual_chunk_size = end_byte - start_byte + 1
        
        return cls(
            chunk_number=chunk_number,
            upload_url=upload_url,
            start_byte=start_byte,
            end_byte=end_byte,
            chunk_size=actual_chunk_size
        )


@dataclass
class HealthCheckResponse:
    """Response DTO for health check."""
    status: str
    service: str
    timestamp: datetime
    dependencies: Dict[str, str]
    version: str = "1.0.0"
    
    @classmethod
    def healthy(cls, dependencies: Dict[str, str] = None) -> 'HealthCheckResponse':
        """Create healthy response."""
        return cls(
            status="healthy",
            service="file_upload_api",
            timestamp=datetime.utcnow(),
            dependencies=dependencies or {}
        )
    
    @classmethod
    def unhealthy(cls, dependencies: Dict[str, str] = None) -> 'HealthCheckResponse':
        """Create unhealthy response."""
        return cls(
            status="unhealthy",
            service="file_upload_api",
            timestamp=datetime.utcnow(),
            dependencies=dependencies or {}
        )