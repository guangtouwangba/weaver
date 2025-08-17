"""
Value objects for file upload domain.

This module defines immutable value objects that represent
core concepts in the file management domain.
"""

from enum import Enum
from typing import Dict, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import uuid


class FileStatus(str, Enum):
    """File lifecycle status."""
    UPLOADING = "uploading"
    AVAILABLE = "available"
    PROCESSING = "processing"
    FAILED = "failed"
    ARCHIVED = "archived"
    DELETED = "deleted"


class AccessLevel(str, Enum):
    """File access levels."""
    PRIVATE = "private"
    PUBLIC_READ = "public_read"
    SHARED = "shared"
    AUTHENTICATED = "authenticated"


class UploadStatus(str, Enum):
    """Upload session status."""
    INITIATED = "initiated"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class FileMetadata:
    """Immutable file metadata value object."""
    original_name: str
    file_size: int
    content_type: str
    file_hash: Optional[str] = None
    category: Optional[str] = None
    tags: frozenset = field(default_factory=frozenset)
    custom_attributes: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate metadata on creation."""
        if not self.original_name:
            raise ValueError("Original name cannot be empty")
        if self.file_size < 0:
            raise ValueError("File size cannot be negative")
        if not self.content_type:
            raise ValueError("Content type cannot be empty")
    
    @property
    def file_extension(self) -> str:
        """Get file extension from original name."""
        return Path(self.original_name).suffix.lower()
    
    @property
    def base_name(self) -> str:
        """Get base name without extension."""
        return Path(self.original_name).stem
    
    def with_hash(self, file_hash: str) -> 'FileMetadata':
        """Return new instance with updated hash."""
        return FileMetadata(
            original_name=self.original_name,
            file_size=self.file_size,
            content_type=self.content_type,
            file_hash=file_hash,
            category=self.category,
            tags=self.tags,
            custom_attributes=self.custom_attributes
        )
    
    def with_tags(self, tags: Set[str]) -> 'FileMetadata':
        """Return new instance with updated tags."""
        return FileMetadata(
            original_name=self.original_name,
            file_size=self.file_size,
            content_type=self.content_type,
            file_hash=self.file_hash,
            category=self.category,
            tags=frozenset(tags),
            custom_attributes=self.custom_attributes
        )


@dataclass(frozen=True)
class AccessPermission:
    """File access permission configuration."""
    level: AccessLevel
    expires_at: Optional[datetime] = None
    allowed_users: frozenset = field(default_factory=frozenset)
    allowed_groups: frozenset = field(default_factory=frozenset)
    allowed_operations: frozenset = field(default_factory=lambda: frozenset({'read'}))
    max_downloads: Optional[int] = None
    ip_whitelist: frozenset = field(default_factory=frozenset)
    
    def __post_init__(self):
        """Validate permissions on creation."""
        valid_operations = {'read', 'write', 'delete', 'share'}
        if not self.allowed_operations.issubset(valid_operations):
            raise ValueError(f"Invalid operations. Must be subset of {valid_operations}")
        
        if self.max_downloads is not None and self.max_downloads < 0:
            raise ValueError("Max downloads cannot be negative")
        
        if self.expires_at and self.expires_at <= datetime.utcnow():
            raise ValueError("Expiration time must be in the future")
    
    @property
    def is_expired(self) -> bool:
        """Check if permission has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_public(self) -> bool:
        """Check if this is a public permission."""
        return self.level in [AccessLevel.PUBLIC_READ]
    
    def can_read(self, user_id: Optional[str] = None, groups: Set[str] = None) -> bool:
        """Check if read operation is allowed."""
        if 'read' not in self.allowed_operations:
            return False
        
        if self.is_public:
            return True
        
        if self.level == AccessLevel.PRIVATE:
            return user_id in self.allowed_users if user_id else False
        
        if self.level == AccessLevel.SHARED:
            if user_id and user_id in self.allowed_users:
                return True
            if groups and self.allowed_groups.intersection(groups):
                return True
        
        return False
    
    def with_expiration(self, expires_at: datetime) -> 'AccessPermission':
        """Return new instance with updated expiration."""
        return AccessPermission(
            level=self.level,
            expires_at=expires_at,
            allowed_users=self.allowed_users,
            allowed_groups=self.allowed_groups,
            allowed_operations=self.allowed_operations,
            max_downloads=self.max_downloads,
            ip_whitelist=self.ip_whitelist
        )


@dataclass(frozen=True)
class StorageLocation:
    """Storage location information."""
    bucket: str
    key: str
    region: Optional[str] = None
    storage_class: str = "STANDARD"
    
    def __post_init__(self):
        """Validate storage location."""
        if not self.bucket:
            raise ValueError("Bucket cannot be empty")
        if not self.key:
            raise ValueError("Key cannot be empty")
    
    @property
    def full_path(self) -> str:
        """Get full storage path."""
        return f"{self.bucket}/{self.key}"
    
    @property
    def url_path(self) -> str:
        """Get URL-safe path."""
        return f"/{self.bucket}/{self.key}"


@dataclass(frozen=True)
class UploadConfiguration:
    """Upload configuration parameters."""
    max_file_size: int = 100 * 1024 * 1024  # 100MB default
    allowed_content_types: frozenset = field(default_factory=lambda: frozenset({
        'application/pdf', 'image/jpeg', 'image/png', 'text/plain',
        'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    }))
    chunk_size: int = 5 * 1024 * 1024  # 5MB chunks for multipart
    presigned_url_expiration: timedelta = field(default_factory=lambda: timedelta(hours=1))
    enable_virus_scan: bool = True
    enable_content_analysis: bool = False
    auto_generate_thumbnails: bool = False
    
    def __post_init__(self):
        """Validate configuration."""
        if self.max_file_size <= 0:
            raise ValueError("Max file size must be positive")
        if self.chunk_size <= 0:
            raise ValueError("Chunk size must be positive")
        if self.presigned_url_expiration.total_seconds() <= 0:
            raise ValueError("Expiration time must be positive")
    
    def is_content_type_allowed(self, content_type: str) -> bool:
        """Check if content type is allowed."""
        return content_type in self.allowed_content_types
    
    def is_file_size_allowed(self, file_size: int) -> bool:
        """Check if file size is within limits."""
        return 0 < file_size <= self.max_file_size


@dataclass(frozen=True)
class FileValidationResult:
    """Result of file validation."""
    is_valid: bool
    errors: frozenset = field(default_factory=frozenset)
    warnings: frozenset = field(default_factory=frozenset)
    
    @classmethod
    def valid(cls) -> 'FileValidationResult':
        """Create a valid result."""
        return cls(is_valid=True)
    
    @classmethod
    def invalid(cls, errors: Set[str]) -> 'FileValidationResult':
        """Create an invalid result with errors."""
        return cls(is_valid=False, errors=frozenset(errors))
    
    def with_warnings(self, warnings: Set[str]) -> 'FileValidationResult':
        """Add warnings to the result."""
        return FileValidationResult(
            is_valid=self.is_valid,
            errors=self.errors,
            warnings=frozenset(warnings)
        )