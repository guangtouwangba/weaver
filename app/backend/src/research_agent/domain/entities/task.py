"""Task domain entity for background job processing."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID, uuid4


class TaskStatus(str, Enum):
    """Task processing status."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(str, Enum):
    """Types of background tasks."""

    PROCESS_DOCUMENT = "process_document"
    EXTRACT_GRAPH = "extract_graph"
    SYNC_CANVAS = "sync_canvas"
    CLEANUP_CANVAS = "cleanup_canvas"  # Async cleanup of old generation canvas items
    FILE_CLEANUP = "file_cleanup"  # Async cleanup of orphan files from storage
    GENERATE_THUMBNAIL = "thumbnail_generator"  # Generate PDF thumbnail image
    PROCESS_URL = "process_url"  # Extract content from URL


@dataclass
class Task:
    """Task entity - represents a background job in the queue."""

    id: UUID = field(default_factory=uuid4)
    task_type: TaskType = TaskType.PROCESS_DOCUMENT
    payload: Dict[str, Any] = field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    priority: int = 0
    attempts: int = 0
    max_attempts: int = 3
    error_message: Optional[str] = None
    scheduled_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def mark_processing(self) -> None:
        """Mark task as processing."""
        self.status = TaskStatus.PROCESSING
        self.started_at = datetime.utcnow()
        self.attempts += 1
        self.updated_at = datetime.utcnow()

    def mark_completed(self) -> None:
        """Mark task as completed."""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def mark_failed(self, error_message: str) -> None:
        """Mark task as failed."""
        self.error_message = error_message
        self.updated_at = datetime.utcnow()

        if self.attempts >= self.max_attempts:
            self.status = TaskStatus.FAILED
        else:
            # Reset to pending for retry
            self.status = TaskStatus.PENDING

    def mark_cancelled(self) -> None:
        """Mark task as cancelled."""
        self.status = TaskStatus.CANCELLED
        self.updated_at = datetime.utcnow()

    @property
    def can_retry(self) -> bool:
        """Check if task can be retried."""
        return self.attempts < self.max_attempts and self.status != TaskStatus.CANCELLED

    @property
    def is_terminal(self) -> bool:
        """Check if task is in a terminal state."""
        return self.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED)
