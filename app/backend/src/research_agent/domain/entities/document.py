"""Document domain entity."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID, uuid4


class DocumentStatus(str, Enum):
    """Document processing status."""

    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"


class DocumentType(str, Enum):
    """Supported document types for multi-format processing."""

    PDF = "pdf"
    DOCX = "docx"
    PPTX = "pptx"
    DOC = "doc"
    PPT = "ppt"
    AUDIO = "audio"
    VIDEO = "video"
    UNKNOWN = "unknown"

    @classmethod
    def from_mime_type(cls, mime_type: str) -> "DocumentType":
        """
        Get DocumentType from MIME type string.

        Args:
            mime_type: MIME type string (e.g., "application/pdf").

        Returns:
            Corresponding DocumentType.
        """
        mime_map = {
            "application/pdf": cls.PDF,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": cls.DOCX,
            "application/vnd.openxmlformats-officedocument.presentationml.presentation": cls.PPTX,
            "application/msword": cls.DOC,
            "application/vnd.ms-powerpoint": cls.PPT,
            "audio/mpeg": cls.AUDIO,
            "audio/wav": cls.AUDIO,
            "audio/mp3": cls.AUDIO,
            "video/mp4": cls.VIDEO,
            "video/mpeg": cls.VIDEO,
        }
        return mime_map.get(mime_type, cls.UNKNOWN)


@dataclass
class Document:
    """Document entity - represents an uploaded document (PDF, Word, PPT, Audio, Video)."""

    id: UUID = field(default_factory=uuid4)
    project_id: Optional[UUID] = None
    filename: str = ""
    original_filename: str = ""
    file_path: str = ""
    file_size: int = 0
    mime_type: str = "application/pdf"
    page_count: int = 0
    status: DocumentStatus = DocumentStatus.PENDING
    summary: Optional[str] = None  # Generated summary of the document
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    # Long context mode fields
    full_content: Optional[str] = None  # Full document content for long context
    content_token_count: Optional[int] = None  # Cached token count
    parsing_metadata: Optional[Dict[str, Any]] = None  # Parsing metadata (layout, OCR, etc.)

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

    @property
    def document_type(self) -> DocumentType:
        """Get the document type based on MIME type."""
        return DocumentType.from_mime_type(self.mime_type)

    @property
    def has_ocr(self) -> bool:
        """Check if OCR was applied during parsing."""
        if self.parsing_metadata:
            return self.parsing_metadata.get("has_ocr", False)
        return False

    @property
    def is_audio_video(self) -> bool:
        """Check if document is an audio or video file."""
        doc_type = self.document_type
        return doc_type in (DocumentType.AUDIO, DocumentType.VIDEO)

    @property
    def duration_seconds(self) -> Optional[float]:
        """Get duration for audio/video documents."""
        if self.parsing_metadata and self.is_audio_video:
            return self.parsing_metadata.get("duration_seconds")
        return None
