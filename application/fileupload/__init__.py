"""
File Upload Application

A comprehensive file management system with secure upload/download capabilities,
fine-grained access control, and enterprise-grade monitoring.

This module provides:
- Secure file upload with signed URLs
- Flexible download mechanisms with temporary access
- Fine-grained permission management
- Complete audit logging and analytics
- Integration with existing MinIO storage infrastructure
"""

__version__ = "1.0.0"
__author__ = "Research Agent RAG Team"

from .domain.entities import FileEntity, UploadSession, AccessPolicy
from .domain.value_objects import FileMetadata, AccessPermission, FileStatus
from .services.upload_service import FileUploadService
from .services.access_service import FileAccessService
from .controllers.file_controller import FileController

__all__ = [
    "FileEntity",
    "UploadSession", 
    "AccessPolicy",
    "FileMetadata",
    "AccessPermission",
    "FileStatus",
    "FileUploadService",
    "FileAccessService",
    "FileController"
]