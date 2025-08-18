"""File metadata value object."""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime


class ContentType(Enum):
    """Supported content types."""
    TEXT_PLAIN = "text/plain"
    TEXT_MARKDOWN = "text/markdown"
    APPLICATION_PDF = "application/pdf"
    APPLICATION_DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    APPLICATION_JSON = "application/json"
    TEXT_CSV = "text/csv"
    
    @classmethod
    def from_file_extension(cls, extension: str) -> 'ContentType':
        """Get content type from file extension."""
        extension_map = {
            '.txt': cls.TEXT_PLAIN,
            '.md': cls.TEXT_MARKDOWN,
            '.markdown': cls.TEXT_MARKDOWN,
            '.pdf': cls.APPLICATION_PDF,
            '.docx': cls.APPLICATION_DOCX,
            '.json': cls.APPLICATION_JSON,
            '.csv': cls.TEXT_CSV,
        }
        return extension_map.get(extension.lower(), cls.TEXT_PLAIN)


@dataclass(frozen=True)
class FileMetadata:
    """Immutable file metadata value object."""
    
    filename: str
    file_size: int
    content_type: ContentType
    file_hash: Optional[str] = None
    encoding: str = "utf-8"
    language: Optional[str] = None
    
    # File system metadata
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    
    # Custom metadata
    custom_metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        """Post-initialization validation."""
        if not self.filename.strip():
            raise ValueError("Filename cannot be empty")
        if self.file_size < 0:
            raise ValueError("File size cannot be negative")
        if self.custom_metadata is None:
            object.__setattr__(self, 'custom_metadata', {})
    
    @property
    def file_extension(self) -> str:
        """Get file extension."""
        return self.filename.split('.')[-1].lower() if '.' in self.filename else ''
    
    @property
    def file_size_mb(self) -> float:
        """Get file size in MB."""
        return self.file_size / (1024 * 1024)
    
    @property
    def is_text_file(self) -> bool:
        """Check if file is a text file."""
        return self.content_type in [
            ContentType.TEXT_PLAIN,
            ContentType.TEXT_MARKDOWN,
            ContentType.TEXT_CSV,
            ContentType.APPLICATION_JSON
        ]
    
    @property
    def is_binary_file(self) -> bool:
        """Check if file is a binary file."""
        return not self.is_text_file
    
    def with_hash(self, file_hash: str) -> 'FileMetadata':
        """Create new instance with file hash."""
        return FileMetadata(
            filename=self.filename,
            file_size=self.file_size,
            content_type=self.content_type,
            file_hash=file_hash,
            encoding=self.encoding,
            language=self.language,
            created_at=self.created_at,
            modified_at=self.modified_at,
            custom_metadata=self.custom_metadata.copy()
        )
    
    def with_custom_metadata(self, key: str, value: Any) -> 'FileMetadata':
        """Create new instance with additional custom metadata."""
        new_metadata = self.custom_metadata.copy()
        new_metadata[key] = value
        
        return FileMetadata(
            filename=self.filename,
            file_size=self.file_size,
            content_type=self.content_type,
            file_hash=self.file_hash,
            encoding=self.encoding,
            language=self.language,
            created_at=self.created_at,
            modified_at=self.modified_at,
            custom_metadata=new_metadata
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'filename': self.filename,
            'file_size': self.file_size,
            'file_size_mb': self.file_size_mb,
            'content_type': self.content_type.value,
            'file_extension': self.file_extension,
            'file_hash': self.file_hash,
            'encoding': self.encoding,
            'language': self.language,
            'is_text_file': self.is_text_file,
            'is_binary_file': self.is_binary_file,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'modified_at': self.modified_at.isoformat() if self.modified_at else None,
            'custom_metadata': self.custom_metadata
        }
