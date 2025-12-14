"""Storage service abstract interface."""

from abc import ABC, abstractmethod
from typing import BinaryIO


class StorageService(ABC):
    """Abstract storage service interface."""

    @abstractmethod
    async def save(self, path: str, content: BinaryIO) -> str:
        """Save file and return the full path."""
        pass

    @abstractmethod
    async def delete(self, path: str) -> bool:
        """Delete file and return success status."""
        pass

    @abstractmethod
    async def exists(self, path: str) -> bool:
        """Check if file exists."""
        pass

    @abstractmethod
    def get_full_path(self, path: str) -> str:
        """Get full file system path."""
        pass

    @abstractmethod
    async def delete_directory(self, path: str) -> bool:
        """Delete directory and all its contents. Return success status."""
        pass

