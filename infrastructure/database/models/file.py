"""
File database model.
"""
from enum import Enum
import uuid

from sqlalchemy import Column, Integer, String, Text, Boolean, BigInteger, ForeignKey, Enum as SQLAlchemyEnum
from sqlalchemy.dialects.postgresql import UUID
from .base import BaseModel


class FileStatus(str, Enum):
    """File status enumeration."""
    uploading = "uploading"
    available = "available"
    processing = "processing"
    failed = "failed"
    deleted = "deleted"
    quarantined = "quarantined"


class File(BaseModel):
    """File model."""
    
    __tablename__ = "files"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    original_name = Column(String(255), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    content_type = Column(String(128), nullable=False)
    storage_bucket = Column(String(128), nullable=False)
    storage_key = Column(String(512), nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=True)
    status = Column(SQLAlchemyEnum(FileStatus, name='file_status_enum'), nullable=False, default=FileStatus.uploading)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 确保状态字段有默认值
        if self.status is None:
            self.status = FileStatus.uploading

    @property
    def is_available(self) -> bool:
        """Check if file is available for download."""
        return self.status == FileStatus.available and not self.is_deleted

    @property
    def is_processing(self) -> bool:
        """Check if file is being processed."""
        return self.status == FileStatus.processing

    @property
    def is_failed(self) -> bool:
        """Check if file processing failed."""
        return self.status == FileStatus.failed

    @property
    def is_deleted_status(self) -> bool:
        """Check if file has deleted status."""
        return self.status == FileStatus.DELETED

    def mark_as_available(self) -> None:
        """Mark file as available for download."""
        if self.status == FileStatus.UPLOADING:
            self.status = FileStatus.AVAILABLE

    def mark_as_processing(self) -> None:
        """Mark file as being processed."""
        self.status = FileStatus.PROCESSING

    def mark_as_failed(self) -> None:
        """Mark file processing as failed."""
        self.status = FileStatus.FAILED

    def mark_as_deleted(self) -> None:
        """Mark file as deleted."""
        self.status = FileStatus.DELETED
        self.is_deleted = True

    def restore(self) -> None:
        """Restore a deleted file."""
        if self.status == FileStatus.DELETED:
            self.status = FileStatus.AVAILABLE
            self.is_deleted = False


class FileUploadSession(BaseModel):
    """File upload session model."""

    __tablename__ = "upload_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    file_id = Column(UUID(as_uuid=True), ForeignKey("files.id"), nullable=False)
    user_id = Column(String(36), nullable=False)  # User ID who uploaded the file
    status = Column(SQLAlchemyEnum(FileStatus), nullable=False, default=FileStatus.uploading)
    created_at = Column(BigInteger, nullable=False)  # Timestamp of creation
    updated_at = Column(BigInteger, nullable=False)  # Timestamp of last update

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.status is None:
            self.status = FileStatus.uploading