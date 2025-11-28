"""Document domain entity."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4


class DocumentStatus(str, Enum):
    """Document processing status."""

    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"


@dataclass
class Document:
    """Document entity - represents an uploaded PDF document."""

    id: UUID = field(default_factory=uuid4)
    project_id: Optional[UUID] = None
    filename: str = ""
    original_filename: str = ""
    file_path: str = ""
    file_size: int = 0
    mime_type: str = "application/pdf"
    page_count: int = 0
    status: DocumentStatus = DocumentStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def mark_processing(self) -> None:
        """Mark document as processing."""
        self.status = DocumentStatus.PROCESSING

    def mark_ready(self, page_count: int) -> None:
        """Mark document as ready with page count."""
        self.page_count = page_count
        self.status = DocumentStatus.READY

    def mark_error(self) -> None:
        """Mark document as error."""
        self.status = DocumentStatus.ERROR

    @property
    def is_ready(self) -> bool:
        """Check if document is ready for use."""
        return self.status == DocumentStatus.READY

