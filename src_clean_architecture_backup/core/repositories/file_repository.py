"""
File repository interface.

Defines the contract for file data access operations.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from ..entities.file import File, FileStatus, AccessLevel


class FileRepository(ABC):
    """Abstract repository interface for file operations."""
    
    @abstractmethod
    async def save(self, file: File) -> None:
        """Save a file."""
        pass
    
    @abstractmethod
    async def get_by_id(self, file_id: str) -> Optional[File]:
        """Get file by ID."""
        pass
    
    @abstractmethod
    async def get_by_topic_id(self, topic_id: int) -> List[File]:
        """Get files by topic ID."""
        pass
    
    @abstractmethod
    async def get_by_filename(self, filename: str) -> List[File]:
        """Get files by filename."""
        pass
    
    @abstractmethod
    async def get_by_hash(self, file_hash: str) -> Optional[File]:
        """Get file by hash."""
        pass
    
    @abstractmethod
    async def list_by_status(self, status: FileStatus, limit: int = 100) -> List[File]:
        """List files by status."""
        pass
    
    @abstractmethod
    async def list_by_access_level(self, access_level: AccessLevel, limit: int = 100) -> List[File]:
        """List files by access level."""
        pass
    
    @abstractmethod
    async def search_by_name(self, name_pattern: str, limit: int = 10) -> List[File]:
        """Search files by name pattern."""
        pass
    
    @abstractmethod
    async def search_by_content_type(self, content_type: str, limit: int = 10) -> List[File]:
        """Search files by content type."""
        pass
    
    @abstractmethod
    async def update_status(self, file_id: str, status: FileStatus) -> bool:
        """Update file status."""
        pass
    
    @abstractmethod
    async def update_access_level(self, file_id: str, access_level: AccessLevel) -> bool:
        """Update file access level."""
        pass
    
    @abstractmethod
    async def increment_download_count(self, file_id: str) -> bool:
        """Increment file download count."""
        pass
    
    @abstractmethod
    async def soft_delete(self, file_id: str) -> bool:
        """Soft delete a file."""
        pass
    
    @abstractmethod
    async def hard_delete(self, file_id: str) -> bool:
        """Hard delete a file."""
        pass
    
    @abstractmethod
    async def list_deleted_files(self, limit: int = 100) -> List[File]:
        """List soft-deleted files."""
        pass
    
    @abstractmethod
    async def restore_file(self, file_id: str) -> bool:
        """Restore a soft-deleted file."""
        pass
    
    @abstractmethod
    async def count_by_status(self, status: FileStatus) -> int:
        """Count files by status."""
        pass
    
    @abstractmethod
    async def get_total_size_by_topic(self, topic_id: int) -> int:
        """Get total file size for a topic."""
        pass