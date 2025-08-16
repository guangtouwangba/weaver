"""
Storage Infrastructure

Provides object storage functionality using MinIO, S3, and other storage backends.
Includes interfaces for object storage, file management, and content processing.
"""

from .interfaces import (
    IObjectStorage, IFileManager, IContentProcessor,
    StorageObject, StorageMetadata, UploadOptions, DownloadOptions,
    ListOptions, SearchCriteria, AccessLevel, ContentType,
    detect_content_type, validate_file_type, generate_unique_key,
    StorageConfig
)
from .minio_storage import MinIOStorage, MinIOFileManager

__all__ = [
    "IObjectStorage",
    "IFileManager",
    "IContentProcessor",
    "StorageObject",
    "StorageMetadata",
    "UploadOptions",
    "DownloadOptions",
    "ListOptions",
    "SearchCriteria",
    "AccessLevel",
    "ContentType",
    "detect_content_type",
    "validate_file_type",
    "generate_unique_key",
    "StorageConfig",
    "MinIOStorage",
    "MinIOFileManager",
]