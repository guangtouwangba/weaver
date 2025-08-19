"""
Domain layer for file management.

This module exports all file-related domain entities, value objects, and enums.
"""

from .file import (
    # Enums
    AccessLevel,
    FileStatus,
    UploadStatus,
    
    # Domain entities and value objects
    FileMetadata,
    StorageLocation,
    AccessPermission,
    FileEntity,
    UploadSession
)

# Repository interfaces
from .repository import IFileRepository, IUploadSessionRepository

__all__ = [
    # Enums
    'AccessLevel',
    'FileStatus',
    'UploadStatus',
    
    # Entities and Value Objects
    'FileMetadata',
    'StorageLocation',
    'AccessPermission',
    'FileEntity',
    'UploadSession',
    
    # Repository Interfaces
    'IFileRepository',
    'IUploadSessionRepository'
]