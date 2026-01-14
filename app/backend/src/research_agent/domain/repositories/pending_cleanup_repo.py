"""Pending cleanup repository interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class PendingCleanup:
    """Pending cleanup domain entity."""

    id: UUID
    file_path: str
    storage_type: str  # "local", "supabase", or "both"
    attempts: int
    max_attempts: int
    last_error: str | None
    created_at: datetime
    last_attempt_at: datetime | None
    document_id: UUID | None
    project_id: UUID | None


class PendingCleanupRepository(ABC):
    """Abstract pending cleanup repository interface."""

    @abstractmethod
    async def add(
        self,
        file_path: str,
        storage_type: str = "both",
        document_id: UUID | None = None,
        project_id: UUID | None = None,
    ) -> PendingCleanup:
        """Add a new pending cleanup record."""
        pass

    @abstractmethod
    async def find_by_id(self, cleanup_id: UUID) -> PendingCleanup | None:
        """Find pending cleanup by ID."""
        pass

    @abstractmethod
    async def find_pending(self, limit: int = 100) -> list[PendingCleanup]:
        """Find pending cleanups that haven't exceeded max attempts."""
        pass

    @abstractmethod
    async def increment_attempt(
        self, cleanup_id: UUID, error: str | None = None
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
