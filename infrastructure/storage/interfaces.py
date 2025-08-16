"""
Storage infrastructure interfaces and abstractions.

This module defines the core interfaces for object storage systems including:
- File upload, download, and management
- Bucket/container operations
- Metadata management and search
- Access control and permissions
- Content delivery and optimization
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, AsyncIterator, Union, BinaryIO
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from pathlib import Path
import uuid


class StorageType(Enum):
    """Types of storage systems."""
    OBJECT_STORE = "object_store"  # S3, MinIO, etc.
    FILE_SYSTEM = "file_system"    # Local filesystem
    CLOUD_STORAGE = "cloud_storage"  # Google Cloud Storage, Azure Blob, etc.


class AccessLevel(Enum):
    """File access levels."""
    PRIVATE = "private"
    PUBLIC_READ = "public_read"
    PUBLIC_READ_WRITE = "public_read_write"
    AUTHENTICATED = "authenticated"


class ContentType(Enum):
    """Common content types."""
    # Documents
    PDF = "application/pdf"
    DOC = "application/msword"
    DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    TXT = "text/plain"
    RTF = "application/rtf"
    
    # Images
    JPEG = "image/jpeg"
    PNG = "image/png"
    GIF = "image/gif"
    SVG = "image/svg+xml"
    
    # Audio/Video
    MP3 = "audio/mpeg"
    MP4 = "video/mp4"
    AVI = "video/avi"
    
    # Archives
    ZIP = "application/zip"
    TAR = "application/x-tar"
    GZIP = "application/gzip"
    
    # Data formats
    JSON = "application/json"
    XML = "application/xml"
    CSV = "text/csv"
    
    # Default
    BINARY = "application/octet-stream"


@dataclass
class StorageMetadata:
    """Metadata for stored objects."""
    size: int = 0
    content_type: str = ContentType.BINARY.value
    created_at: datetime = field(default_factory=datetime.utcnow)
    modified_at: datetime = field(default_factory=datetime.utcnow)
    etag: Optional[str] = None
    version: Optional[str] = None
    custom_metadata: Dict[str, str] = field(default_factory=dict)
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class StorageObject:
    """Represents a stored object."""
    key: str
    bucket: str
    metadata: StorageMetadata = field(default_factory=StorageMetadata)
    access_level: AccessLevel = AccessLevel.PRIVATE
    content: Optional[bytes] = None
    
    @property
    def full_path(self) -> str:
        """Get the full path of the object."""
        return f"{self.bucket}/{self.key}"
    
    @property
    def filename(self) -> str:
        """Get the filename from the key."""
        return Path(self.key).name
    
    @property
    def extension(self) -> str:
        """Get the file extension."""
        return Path(self.key).suffix.lower()


@dataclass
class UploadOptions:
    """Options for file uploads."""
    content_type: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None
    tags: Optional[Dict[str, str]] = None
    access_level: AccessLevel = AccessLevel.PRIVATE
    encryption: bool = True
    versioning: bool = False
    expires_in: Optional[timedelta] = None


@dataclass
class DownloadOptions:
    """Options for file downloads."""
    version: Optional[str] = None
    range_start: Optional[int] = None
    range_end: Optional[int] = None
    if_modified_since: Optional[datetime] = None
    if_unmodified_since: Optional[datetime] = None


@dataclass
class ListOptions:
    """Options for listing objects."""
    prefix: Optional[str] = None
    suffix: Optional[str] = None
    max_keys: int = 1000
    continuation_token: Optional[str] = None
    include_metadata: bool = False
    recursive: bool = True


@dataclass
class SearchCriteria:
    """Criteria for searching objects."""
    content_type: Optional[str] = None
    size_min: Optional[int] = None
    size_max: Optional[int] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    tags: Optional[Dict[str, str]] = None
    metadata_filters: Optional[Dict[str, str]] = None


class IObjectStorage(ABC):
    """
    Abstract interface for object storage systems.
    
    Defines core operations for storing, retrieving, and managing objects
    in various storage backends like S3, MinIO, Azure Blob Storage, etc.
    """
    
    @abstractmethod
    async def create_bucket(
        self,
        bucket_name: str,
        region: Optional[str] = None,
        **kwargs
    ) -> bool:
        """
        Create a new bucket/container.
        
        Args:
            bucket_name: Name of the bucket to create
            region: Region to create the bucket in
            **kwargs: Additional provider-specific options
            
        Returns:
            True if bucket was created successfully
        """
        pass
    
    @abstractmethod
    async def delete_bucket(self, bucket_name: str, force: bool = False) -> bool:
        """
        Delete a bucket/container.
        
        Args:
            bucket_name: Name of the bucket to delete
            force: Whether to delete non-empty bucket
            
        Returns:
            True if bucket was deleted successfully
        """
        pass
    
    @abstractmethod
    async def bucket_exists(self, bucket_name: str) -> bool:
        """Check if a bucket exists."""
        pass
    
    @abstractmethod
    async def list_buckets(self) -> List[str]:
        """List all available buckets."""
        pass
    
    @abstractmethod
    async def upload_object(
        self,
        bucket: str,
        key: str,
        data: Union[bytes, BinaryIO, str, Path],
        options: Optional[UploadOptions] = None
    ) -> StorageObject:
        """
        Upload an object to storage.
        
        Args:
            bucket: Target bucket name
            key: Object key/path
            data: Data to upload (bytes, file-like object, or file path)
            options: Upload options
            
        Returns:
            StorageObject representing the uploaded object
        """
        pass
    
    @abstractmethod
    async def download_object(
        self,
        bucket: str,
        key: str,
        options: Optional[DownloadOptions] = None
    ) -> StorageObject:
        """
        Download an object from storage.
        
        Args:
            bucket: Source bucket name
            key: Object key/path
            options: Download options
            
        Returns:
            StorageObject with content loaded
        """
        pass
    
    @abstractmethod
    async def download_object_to_file(
        self,
        bucket: str,
        key: str,
        file_path: Union[str, Path],
        options: Optional[DownloadOptions] = None
    ) -> bool:
        """
        Download an object directly to a file.
        
        Args:
            bucket: Source bucket name
            key: Object key/path
            file_path: Local file path to save to
            options: Download options
            
        Returns:
            True if download was successful
        """
        pass
    
    @abstractmethod
    async def delete_object(self, bucket: str, key: str) -> bool:
        """
        Delete an object from storage.
        
        Args:
            bucket: Bucket name
            key: Object key/path
            
        Returns:
            True if object was deleted successfully
        """
        pass
    
    @abstractmethod
    async def object_exists(self, bucket: str, key: str) -> bool:
        """Check if an object exists."""
        pass
    
    @abstractmethod
    async def get_object_metadata(self, bucket: str, key: str) -> Optional[StorageMetadata]:
        """Get metadata for an object without downloading content."""
        pass
    
    @abstractmethod
    async def update_object_metadata(
        self,
        bucket: str,
        key: str,
        metadata: Dict[str, str]
    ) -> bool:
        """Update metadata for an existing object."""
        pass
    
    @abstractmethod
    async def list_objects(
        self,
        bucket: str,
        options: Optional[ListOptions] = None
    ) -> List[StorageObject]:
        """
        List objects in a bucket.
        
        Args:
            bucket: Bucket name
            options: Listing options
            
        Returns:
            List of StorageObject instances
        """
        pass
    
    @abstractmethod
    async def copy_object(
        self,
        source_bucket: str,
        source_key: str,
        dest_bucket: str,
        dest_key: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Copy an object within or between buckets.
        
        Args:
            source_bucket: Source bucket name
            source_key: Source object key
            dest_bucket: Destination bucket name
            dest_key: Destination object key
            metadata: Optional new metadata
            
        Returns:
            True if copy was successful
        """
        pass
    
    @abstractmethod
    async def generate_presigned_url(
        self,
        bucket: str,
        key: str,
        expiration: timedelta = timedelta(hours=1),
        method: str = "GET"
    ) -> str:
        """
        Generate a presigned URL for temporary access.
        
        Args:
            bucket: Bucket name
            key: Object key
            expiration: URL expiration time
            method: HTTP method (GET, PUT, POST, DELETE)
            
        Returns:
            Presigned URL string
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the storage system is healthy."""
        pass


class IFileManager(ABC):
    """
    High-level interface for file management operations.
    
    Provides convenient methods for common file operations with
    automatic handling of metadata, thumbnails, and content processing.
    """
    
    @abstractmethod
    async def save_file(
        self,
        file_data: Union[bytes, BinaryIO, str, Path],
        filename: Optional[str] = None,
        folder: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        public: bool = False
    ) -> str:
        """
        Save a file with automatic organization and metadata extraction.
        
        Args:
            file_data: File data to save
            filename: Original filename (will be auto-generated if not provided)
            folder: Logical folder to organize files
            tags: Tags for categorization
            public: Whether the file should be publicly accessible
            
        Returns:
            Unique file ID or key
        """
        pass
    
    @abstractmethod
    async def get_file(self, file_id: str) -> Optional[StorageObject]:
        """Get a file by its ID."""
        pass
    
    @abstractmethod
    async def get_file_url(
        self,
        file_id: str,
        expiration: Optional[timedelta] = None
    ) -> Optional[str]:
        """Get a URL to access a file."""
        pass
    
    @abstractmethod
    async def delete_file(self, file_id: str) -> bool:
        """Delete a file by its ID."""
        pass
    
    @abstractmethod
    async def search_files(
        self,
        criteria: SearchCriteria,
        limit: int = 100,
        offset: int = 0
    ) -> List[StorageObject]:
        """Search files based on criteria."""
        pass
    
    @abstractmethod
    async def get_file_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        pass


class IContentProcessor(ABC):
    """
    Interface for processing file content.
    
    Handles tasks like thumbnail generation, content extraction,
    format conversion, and optimization.
    """
    
    @abstractmethod
    async def extract_text(self, storage_object: StorageObject) -> Optional[str]:
        """Extract text content from a file."""
        pass
    
    @abstractmethod
    async def generate_thumbnail(
        self,
        storage_object: StorageObject,
        size: tuple = (200, 200)
    ) -> Optional[bytes]:
        """Generate a thumbnail for an image or document."""
        pass
    
    @abstractmethod
    async def get_file_info(self, storage_object: StorageObject) -> Dict[str, Any]:
        """Extract detailed file information and metadata."""
        pass
    
    @abstractmethod
    async def convert_format(
        self,
        storage_object: StorageObject,
        target_format: str
    ) -> Optional[bytes]:
        """Convert file to a different format."""
        pass
    
    @abstractmethod
    async def optimize_file(self, storage_object: StorageObject) -> Optional[bytes]:
        """Optimize file size while maintaining quality."""
        pass


# Common storage configurations
class StorageConfig:
    """Configuration for storage systems."""
    
    # Default buckets for different content types
    DOCUMENTS_BUCKET = "documents"
    IMAGES_BUCKET = "images"
    VIDEOS_BUCKET = "videos"
    TEMP_BUCKET = "temp"
    BACKUPS_BUCKET = "backups"
    
    # Default access patterns
    DEFAULT_EXPIRATION = timedelta(hours=1)
    TEMP_FILE_EXPIRATION = timedelta(hours=24)
    BACKUP_RETENTION = timedelta(days=30)
    
    # File size limits (in bytes)
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
    MAX_IMAGE_SIZE = 10 * 1024 * 1024   # 10MB
    MAX_DOCUMENT_SIZE = 50 * 1024 * 1024  # 50MB
    
    # Supported file types
    ALLOWED_DOCUMENT_TYPES = {'.pdf', '.doc', '.docx', '.txt', '.rtf'}
    ALLOWED_IMAGE_TYPES = {'.jpg', '.jpeg', '.png', '.gif', '.svg'}
    ALLOWED_VIDEO_TYPES = {'.mp4', '.avi', '.mov', '.wmv'}
    ALLOWED_AUDIO_TYPES = {'.mp3', '.wav', '.flac', '.ogg'}


# Common content type detection
def detect_content_type(filename: str) -> str:
    """Detect content type from filename extension."""
    extension = Path(filename).suffix.lower()
    
    content_type_map = {
        '.pdf': ContentType.PDF.value,
        '.doc': ContentType.DOC.value,
        '.docx': ContentType.DOCX.value,
        '.txt': ContentType.TXT.value,
        '.rtf': ContentType.RTF.value,
        '.jpg': ContentType.JPEG.value,
        '.jpeg': ContentType.JPEG.value,
        '.png': ContentType.PNG.value,
        '.gif': ContentType.GIF.value,
        '.svg': ContentType.SVG.value,
        '.mp3': ContentType.MP3.value,
        '.mp4': ContentType.MP4.value,
        '.avi': ContentType.AVI.value,
        '.zip': ContentType.ZIP.value,
        '.tar': ContentType.TAR.value,
        '.gz': ContentType.GZIP.value,
        '.json': ContentType.JSON.value,
        '.xml': ContentType.XML.value,
        '.csv': ContentType.CSV.value,
    }
    
    return content_type_map.get(extension, ContentType.BINARY.value)


def validate_file_type(filename: str, allowed_types: set) -> bool:
    """Validate if file type is allowed."""
    extension = Path(filename).suffix.lower()
    return extension in allowed_types


def generate_unique_key(filename: str, folder: Optional[str] = None) -> str:
    """Generate a unique storage key for a file."""
    timestamp = datetime.utcnow().strftime("%Y/%m/%d")
    unique_id = str(uuid.uuid4())
    file_extension = Path(filename).suffix
    
    if folder:
        return f"{folder}/{timestamp}/{unique_id}{file_extension}"
    else:
        return f"{timestamp}/{unique_id}{file_extension}"