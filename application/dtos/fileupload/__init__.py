"""
File Upload DTOs Package

This module contains all Data Transfer Objects related to file upload operations.
"""

from .requests import (
    GetSignedUrlRequest,
    InitiateUploadRequest, 
    CompleteUploadRequest,
    ConfirmUploadCompletionRequest,
    DownloadFileRequest,
    UpdateFileAccessRequest,
    FileSearchRequest
)

from .responses import (
    SignedUrlResponse,
    UploadSessionResponse,
    UploadCompletionResponse,
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
    "ConfirmUploadCompletionRequest",
    "DownloadFileRequest",
    "UpdateFileAccessRequest",
    "FileSearchRequest",
    
    # Response DTOs
    "SignedUrlResponse",
    "UploadSessionResponse",
    "UploadCompletionResponse",
    "FileResponse",
    "DownloadResponse",
    "FileListResponse",
    "FileStatsResponse",
    "ErrorResponse"
]