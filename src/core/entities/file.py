"""
File entity.

Represents a file in the storage system.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import uuid4
from enum import Enum


class FileStatus(str, Enum):
    """File status enumeration."""
    UPLOADING = "uploading"
    AVAILABLE = "available"
    PROCESSING = "processing"
    FAILED = "failed"
    DELETED = "deleted"
    QUARANTINED = "quarantined"


class AccessLevel(str, Enum):
    """File access level enumeration."""
    PRIVATE = "private"
    PUBLIC_READ = "public_read"
    SHARED = "shared"
    AUTHENTICATED = "authenticated"


@dataclass
class File:
    """File entity representing a stored file."""
    
    id: str = field(default_factory=lambda: str(uuid4()))
    
    # Topic association
    topic_id: Optional[int] = None
    
    # File information
    filename: str = ""
    original_name: str = ""
    file_size: int = 0
    content_type: str = ""
    
    # Storage information
    storage_bucket: str = ""
    storage_key: str = ""
    storage_url: Optional[str] = None
    file_hash: Optional[str] = None
    
    # Status and access
    status: FileStatus = FileStatus.UPLOADING
    access_level: AccessLevel = AccessLevel.PRIVATE
    download_count: int = 0
    
    # Soft delete
    is_deleted: bool = False
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def mark_as_available(self) -> None:
        """Mark file as available."""
        self.status = FileStatus.AVAILABLE
        self.updated_at = datetime.utcnow()
    
    def mark_as_processing(self) -> None:
        """Mark file as processing."""
        self.status = FileStatus.PROCESSING
        self.updated_at = datetime.utcnow()
    
    def mark_as_failed(self) -> None:
        """Mark file as failed."""
        self.status = FileStatus.FAILED
        self.updated_at = datetime.utcnow()
    
    def soft_delete(self) -> None:
        """Soft delete the file."""
        self.is_deleted = True
        self.status = FileStatus.DELETED
        self.updated_at = datetime.utcnow()
    
    def increment_download_count(self) -> None:
        """Increment download count."""
        self.download_count += 1
        self.updated_at = datetime.utcnow()
    
    def set_access_level(self, access_level: AccessLevel) -> None:
        """Set file access level."""
        self.access_level = access_level
        self.updated_at = datetime.utcnow()
    
    def update_storage_info(self, bucket: str, key: str, url: Optional[str] = None) -> None:
        """Update storage information."""
        self.storage_bucket = bucket
        self.storage_key = key
        if url:
            self.storage_url = url
        self.updated_at = datetime.utcnow()
    
    def is_available(self) -> bool:
        """Check if file is available."""
        return self.status == FileStatus.AVAILABLE and not self.is_deleted
    
    def is_processing(self) -> bool:
        """Check if file is being processed."""
        return self.status == FileStatus.PROCESSING
    
    def has_failed(self) -> bool:
        """Check if file processing has failed."""
        return self.status == FileStatus.FAILED