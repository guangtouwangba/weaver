"""
File upload domain entities and value objects.

This module contains the core business entities and value objects
for the file management domain, following DDD principles.
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Set
from dataclasses import dataclass, field
from enum import Enum


# Value Objects
class AccessLevel(str, Enum):
    """File access level enumeration."""
    PRIVATE = "private"
    SHARED = "shared"
    PUBLIC = "public"
    RESTRICTED = "restricted"


class FileStatus(str, Enum):
    """File status enumeration."""
    UPLOADING = "uploading"
    AVAILABLE = "available"
    PROCESSING = "processing"
    FAILED = "failed"
    DELETED = "deleted"
    QUARANTINED = "quarantined"


class UploadStatus(str, Enum):
    """Upload session status enumeration."""
    INITIATED = "initiated"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


@dataclass
class FileMetadata:
    """File metadata value object."""
    original_name: str
    file_size: int
    content_type: str
    file_hash: Optional[str] = None
    category: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    custom_metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def file_extension(self) -> str:
        """Get file extension from original name."""
        return self.original_name.split('.')[-1].lower() if '.' in self.original_name else ''
    
    @property
    def is_image(self) -> bool:
        """Check if file is an image."""
        return self.content_type.startswith('image/')
    
    @property
    def is_document(self) -> bool:
        """Check if file is a document."""
        document_types = [
            'application/pdf', 'application/msword',
            'application/vnd.openxmlformats-officedocument',
            'text/plain', 'text/csv'
        ]
        return any(self.content_type.startswith(dt) for dt in document_types)

    @property
    def get(self):
        return {
            "original_name": self.original_name,
            "file_size": self.file_size,
            "content_type": self.content_type,
            "file_hash": self.file_hash,
            "category": self.category,
            "tags": self.tags,
            "custom_metadata": self.custom_metadata
        }


@dataclass
class StorageLocation:
    """Storage location value object."""
    bucket: str
    key: str
    provider: str = "minio"
    region: Optional[str] = None
    
    @property
    def full_path(self) -> str:
        """Get full storage path."""
        return f"{self.provider}://{self.bucket}/{self.key}"


@dataclass
class AccessPermission:
    """Access permission value object."""
    level: AccessLevel = AccessLevel.PRIVATE
    allowed_users: Set[str] = field(default_factory=set)
    allowed_groups: Set[str] = field(default_factory=set)
    expires_at: Optional[datetime] = None
    max_downloads: Optional[int] = None
    current_downloads: int = 0
    
    @property
    def is_expired(self) -> bool:
        """Check if permission has expired."""
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        return False
    
    @property
    def is_public(self) -> bool:
        """Check if permission allows public access."""
        return self.level == AccessLevel.PUBLIC
    
    @property
    def downloads_exceeded(self) -> bool:
        """Check if download limit exceeded."""
        if self.max_downloads:
            return self.current_downloads >= self.max_downloads
        return False
    
    def can_read(self, user_id: Optional[str] = None, groups: Set[str] = None) -> bool:
        """Check if user can read with this permission."""
        if self.is_expired or self.downloads_exceeded:
            return False
        
        if self.level == AccessLevel.PUBLIC:
            return True
        
        if user_id and user_id in self.allowed_users:
            return True
        
        if groups and self.allowed_groups.intersection(groups):
            return True
        
        return False


# Domain Entities
@dataclass
class FileEntity:
    """
    Core file entity representing a managed file in the system.
    
    This entity encapsulates all information about a file including
    its metadata, storage location, access permissions, and lifecycle.
    """
    
    # Identity
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    owner_id: Optional[str] = None
    
    # Core attributes
    metadata: Optional[FileMetadata] = None
    storage_location: Optional[StorageLocation] = None
    status: FileStatus = FileStatus.UPLOADING
    
    # Access control
    access_permission: AccessPermission = field(
        default_factory=lambda: AccessPermission(level=AccessLevel.PRIVATE)
    )
    
    # Tracking
    upload_session_id: Optional[str] = None
    download_count: int = 0
    last_accessed_at: Optional[datetime] = None
    
    # Topic relationship
    topic_id: Optional[int] = None
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = None
    
    # Computed properties
    @property
    def is_available(self) -> bool:
        """Check if file is available for download."""
        return (
            self.status == FileStatus.AVAILABLE and
            not self.access_permission.is_expired and
            self.deleted_at is None
        )
    
    @property
    def is_public(self) -> bool:
        """Check if file has public access."""
        return self.access_permission.is_public
    
    @property
    def file_size_mb(self) -> float:
        """Get file size in megabytes."""
        if not self.metadata:
            return 0.0
        return self.metadata.file_size / (1024 * 1024)
    
    @property
    def age_days(self) -> int:
        """Get file age in days."""
        return (datetime.utcnow() - self.created_at).days
    
    # Business methods
    def mark_as_available(self) -> None:
        """Mark file as available for download."""
        if self.status == FileStatus.UPLOADING:
            self.status = FileStatus.AVAILABLE
            self.updated_at = datetime.utcnow()
    
    def mark_as_failed(self, error_message: str = None) -> None:
        """Mark file upload as failed."""
        self.status = FileStatus.FAILED
        self.updated_at = datetime.utcnow()
    
    def mark_accessed(self) -> None:
        """Record file access."""
        self.last_accessed_at = datetime.utcnow()
        self.download_count += 1
        self.access_permission.current_downloads += 1
        self.updated_at = datetime.utcnow()
    
    def update_access_permission(self, permission: AccessPermission) -> None:
        """Update file access permissions."""
        self.access_permission = permission
        self.updated_at = datetime.utcnow()
    
    def soft_delete(self) -> None:
        """Soft delete the file."""
        self.status = FileStatus.DELETED
        self.deleted_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def restore(self) -> None:
        """Restore a soft-deleted file."""
        if self.status == FileStatus.DELETED:
            self.status = FileStatus.AVAILABLE
            self.deleted_at = None
            self.updated_at = datetime.utcnow()
    
    def can_be_accessed_by(self, user_id: Optional[str] = None, groups: Set[str] = None) -> bool:
        """Check if file can be accessed by user."""
        if not self.is_available:
            return False
        
        # Owner always has access
        if user_id and user_id == self.owner_id:
            return True
        
        return self.access_permission.can_read(user_id, groups)
    
    def generate_download_key(self) -> str:
        """Generate a unique download tracking key."""
        return f"{self.id}_{uuid.uuid4().hex[:8]}_{int(datetime.utcnow().timestamp())}"


@dataclass
class UploadSession:
    """
    Represents a file upload session for tracking multi-part uploads.
    
    This entity manages the state of file uploads, especially for
    large files that require chunked/resumable uploads.
    """
    
    # Identity
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    file_id: str = ""
    user_id: Optional[str] = None
    
    # Upload details
    original_filename: str = ""
    expected_size: int = 0
    uploaded_size: int = 0
    content_type: str = ""
    
    # Configuration
    chunk_size: int = 5 * 1024 * 1024  # 5MB default
    max_chunks: Optional[int] = None
    
    # State tracking
    status: UploadStatus = UploadStatus.INITIATED
    uploaded_chunks: List[int] = field(default_factory=list)
    failed_chunks: List[int] = field(default_factory=list)
    
    # Storage details
    storage_key: Optional[str] = None
    upload_id: Optional[str] = None  # For multipart upload
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime = field(
        default_factory=lambda: datetime.utcnow() + timedelta(hours=24)
    )
    completed_at: Optional[datetime] = None
    
    # Error tracking
    error_message: Optional[str] = None
    retry_count: int = 0
    
    @property
    def progress_percentage(self) -> float:
        """Calculate upload progress percentage."""
        if self.expected_size == 0:
            return 0.0
        return (self.uploaded_size / self.expected_size) * 100
    
    @property
    def is_expired(self) -> bool:
        """Check if upload session has expired."""
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_resumable(self) -> bool:
        """Check if upload can be resumed."""
        return (
            self.status == UploadStatus.IN_PROGRESS and
            not self.is_expired and
            self.uploaded_size < self.expected_size
        )
    
    @property
    def remaining_chunks(self) -> List[int]:
        """Get list of chunks that still need to be uploaded."""
        if not self.max_chunks:
            return []
        
        all_chunks = set(range(self.max_chunks))
        uploaded_chunks = set(self.uploaded_chunks)
        return sorted(list(all_chunks - uploaded_chunks))
    
    @property
    def next_chunk_number(self) -> int:
        """Get the next chunk number to upload."""
        remaining = self.remaining_chunks
        return remaining[0] if remaining else -1
    
    def start_upload(self, storage_key: str, upload_id: Optional[str] = None) -> None:
        """Start the upload process."""
        self.status = UploadStatus.IN_PROGRESS
        self.storage_key = storage_key
        self.upload_id = upload_id
        self.updated_at = datetime.utcnow()
        
        # Calculate max chunks
        if self.expected_size > 0:
            self.max_chunks = (self.expected_size + self.chunk_size - 1) // self.chunk_size
    
    def mark_chunk_uploaded(self, chunk_number: int, chunk_size: int) -> None:
        """Mark a chunk as successfully uploaded."""
        if chunk_number not in self.uploaded_chunks:
            self.uploaded_chunks.append(chunk_number)
            self.uploaded_size += chunk_size
            self.updated_at = datetime.utcnow()
        
        # Remove from failed chunks if it was there
        if chunk_number in self.failed_chunks:
            self.failed_chunks.remove(chunk_number)
    
    def mark_chunk_failed(self, chunk_number: int, error: str = None) -> None:
        """Mark a chunk upload as failed."""
        if chunk_number not in self.failed_chunks:
            self.failed_chunks.append(chunk_number)
            self.error_message = error
            self.updated_at = datetime.utcnow()
    
    def complete_upload(self) -> None:
        """Mark upload as completed."""
        self.status = UploadStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def fail_upload(self, error_message: str) -> None:
        """Mark upload as failed."""
        self.status = UploadStatus.FAILED
        self.error_message = error_message
        self.updated_at = datetime.utcnow()
    
    def cancel_upload(self) -> None:
        """Cancel the upload."""
        self.status = UploadStatus.CANCELLED
        self.updated_at = datetime.utcnow()