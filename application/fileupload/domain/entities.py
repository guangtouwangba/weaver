"""
Domain entities for file upload application.

This module contains the core business entities that represent
the main concepts in the file management domain.
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Set
from dataclasses import dataclass, field

from .value_objects import (
    FileMetadata, AccessPermission, StorageLocation, FileStatus,
    AccessLevel, UploadStatus, UploadConfiguration, FileValidationResult
)


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
    metadata: FileMetadata = None
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
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entity to dictionary."""
        return {
            "id": self.id,
            "owner_id": self.owner_id,
            "original_name": self.metadata.original_name if self.metadata else None,
            "file_size": self.metadata.file_size if self.metadata else None,
            "content_type": self.metadata.content_type if self.metadata else None,
            "status": self.status.value,
            "access_level": self.access_permission.level.value,
            "download_count": self.download_count,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_accessed_at": self.last_accessed_at.isoformat() if self.last_accessed_at else None,
            "is_available": self.is_available,
            "is_public": self.is_public
        }


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
    
    def extend_expiration(self, hours: int = 24) -> None:
        """Extend the session expiration time."""
        self.expires_at = datetime.utcnow() + timedelta(hours=hours)
        self.updated_at = datetime.utcnow()
    
    def increment_retry(self) -> None:
        """Increment retry counter."""
        self.retry_count += 1
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary."""
        return {
            "id": self.id,
            "file_id": self.file_id,
            "user_id": self.user_id,
            "original_filename": self.original_filename,
            "expected_size": self.expected_size,
            "uploaded_size": self.uploaded_size,
            "progress_percentage": self.progress_percentage,
            "status": self.status.value,
            "uploaded_chunks": len(self.uploaded_chunks),
            "total_chunks": self.max_chunks or 0,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "is_expired": self.is_expired,
            "is_resumable": self.is_resumable
        }


@dataclass
class AccessPolicy:
    """
    Entity representing access policies for files and collections.
    
    This entity allows for complex access control scenarios including
    time-based access, conditional permissions, and audit requirements.
    """
    
    # Identity
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: Optional[str] = None
    
    # Core permission
    base_permission: AccessPermission = field(
        default_factory=lambda: AccessPermission(level=AccessLevel.PRIVATE)
    )
    
    # Advanced controls
    conditions: Dict[str, Any] = field(default_factory=dict)
    requirements: Set[str] = field(default_factory=set)
    
    # Scope
    applies_to_file_ids: Set[str] = field(default_factory=set)
    applies_to_categories: Set[str] = field(default_factory=set)
    applies_to_content_types: Set[str] = field(default_factory=set)
    
    # Management
    is_active: bool = True
    priority: int = 0  # Higher priority policies override lower ones
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def is_effective(self) -> bool:
        """Check if policy is currently effective."""
        return (
            self.is_active and
            not self.base_permission.is_expired
        )
    
    def applies_to_file(self, file_entity: FileEntity) -> bool:
        """Check if this policy applies to a given file."""
        if not self.is_effective:
            return False
        
        # Check file ID
        if self.applies_to_file_ids and file_entity.id not in self.applies_to_file_ids:
            return False
        
        # Check category
        if self.applies_to_categories and file_entity.metadata:
            if file_entity.metadata.category not in self.applies_to_categories:
                return False
        
        # Check content type
        if self.applies_to_content_types and file_entity.metadata:
            if file_entity.metadata.content_type not in self.applies_to_content_types:
                return False
        
        return True
    
    def evaluate_access(self, user_id: Optional[str], groups: Set[str] = None, 
                       context: Dict[str, Any] = None) -> bool:
        """Evaluate if access should be granted based on this policy."""
        if not self.is_effective:
            return False
        
        # Check base permission
        if not self.base_permission.can_read(user_id, groups):
            return False
        
        # Check additional conditions
        if self.conditions and context:
            for condition_key, condition_value in self.conditions.items():
                if condition_key not in context:
                    return False
                if context[condition_key] != condition_value:
                    return False
        
        return True
    
    def add_file(self, file_id: str) -> None:
        """Add a file to this policy's scope."""
        self.applies_to_file_ids.add(file_id)
        self.updated_at = datetime.utcnow()
    
    def remove_file(self, file_id: str) -> None:
        """Remove a file from this policy's scope."""
        self.applies_to_file_ids.discard(file_id)
        self.updated_at = datetime.utcnow()
    
    def activate(self) -> None:
        """Activate this policy."""
        self.is_active = True
        self.updated_at = datetime.utcnow()
    
    def deactivate(self) -> None:
        """Deactivate this policy."""
        self.is_active = False
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert policy to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "access_level": self.base_permission.level.value,
            "is_active": self.is_active,
            "is_effective": self.is_effective,
            "priority": self.priority,
            "file_count": len(self.applies_to_file_ids),
            "categories": list(self.applies_to_categories),
            "content_types": list(self.applies_to_content_types),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }