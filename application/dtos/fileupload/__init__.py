"""
File Upload DTOs Package

This module contains all Data Transfer Objects related to file upload operations.
"""

from .requests import (
    GetSignedUrlRequest,
    InitiateUploadRequest, 
    CompleteUploadRequest,
    DownloadFileRequest,
    UpdateFileAccessRequest,
    FileSearchRequest
)

from .responses import (
    SignedUrlResponse,
    UploadSessionResponse,
    FileResponse,
    DownloadResponse,
    FileListResponse,
    FileStatsResponse,
    ErrorResponse
)

__all__ = [
    # Request DTOs
    "GetSignedUrlRequest",
    "InitiateUploadRequest", 
    "CompleteUploadRequest",
    "DownloadFileRequest",
    "UpdateFileAccessRequest",
    "FileSearchRequest",
    
    # Response DTOs
    "SignedUrlResponse",
    "UploadSessionResponse",
    "FileResponse",
    "DownloadResponse",
    "FileListResponse",
    "FileStatsResponse",
    "ErrorResponse"
]