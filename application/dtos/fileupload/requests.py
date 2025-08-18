"""
File Upload Request DTOs

This module contains all request Data Transfer Objects for file upload operations.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, field

from domain.fileupload import AccessLevel, FileStatus


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
class ConfirmUploadCompletionRequest:
    """Request DTO for confirming upload completion."""
    file_id: str
    file_hash: Optional[str] = None
    actual_file_size: Optional[int] = None
    
    def __post_init__(self):
        """Validate request data."""
        if not self.file_id:
            raise ValueError("File ID cannot be empty")


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


@dataclass
class FileSearchRequest:
    """Request DTO for file search."""
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
        """Validate request data."""
        if self.limit <= 0 or self.limit > 1000:
            raise ValueError("Limit must be between 1 and 1000")
        if self.offset < 0:
            raise ValueError("Offset must be non-negative")
        if self.sort_by not in ["created_at", "updated_at", "file_size", "download_count", "name"]:
            raise ValueError("Invalid sort_by field")
        if self.sort_order not in ["asc", "desc"]:
            raise ValueError("Sort order must be 'asc' or 'desc'")