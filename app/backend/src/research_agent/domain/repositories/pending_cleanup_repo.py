"""Pending cleanup repository interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from uuid import UUID


@dataclass
class PendingCleanup:
    """Pending cleanup domain entity."""

    id: UUID
    file_path: str
    storage_type: str  # "local", "supabase", or "both"
    attempts: int
    max_attempts: int
    last_error: Optional[str]
    created_at: datetime
    last_attempt_at: Optional[datetime]
    document_id: Optional[UUID]
    project_id: Optional[UUID]


class PendingCleanupRepository(ABC):
    """Abstract pending cleanup repository interface."""

    @abstractmethod
    async def add(
        self,
        file_path: str,
        storage_type: str = "both",
        document_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
    ) -> PendingCleanup:
        """Add a new pending cleanup record."""
        pass

    @abstractmethod
    async def find_by_id(self, cleanup_id: UUID) -> Optional[PendingCleanup]:
        """Find pending cleanup by ID."""
        pass

    @abstractmethod
    async def find_pending(self, limit: int = 100) -> List[PendingCleanup]:
        """Find pending cleanups that haven't exceeded max attempts."""
        pass

    @abstractmethod
    async def increment_attempt(
        self, cleanup_id: UUID, error: Optional[str] = None
    ) -> bool:
        """Increment attempt count and record error if any."""
        pass

    @abstractmethod
    async def remove(self, cleanup_id: UUID) -> bool:
        """Remove a cleanup record after successful deletion."""
        pass

    @abstractmethod
    async def remove_by_file_path(self, file_path: str) -> bool:
        """Remove all cleanup records for a file path."""
        pass
