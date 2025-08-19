"""
FastAPI routes for file upload and management.

This module provides REST API endpoints for file upload, download,
and management operations with comprehensive documentation and validation.
"""

import logging
from typing import Optional, List, Dict, Any, Set
from fastapi import APIRouter, HTTPException, Depends, Path
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

# Application layer imports
from application.file.file_upload import FileApplication

# Registry dependency injection
from infrastructure.denpendency_injection import DependsFileApplication
from application.dtos.fileupload import (
    GetSignedUrlRequest, InitiateUploadRequest, ConfirmUploadCompletionRequest, DownloadFileRequest, 
    SignedUrlResponse, UploadSessionResponse, UploadCompletionResponse, FileResponse, DownloadResponse
)
from domain.file import AccessLevel, FileStatus
from infrastructure.messaging.redis_event_bus import RedisEventBus
from infrastructure.tasks.models import TaskPriority
from infrastructure.tasks.service import process_file_complete

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/files", tags=["file-upload"])


# Pydantic models for API validation

class GetSignedUrlAPI(BaseModel):
    """API model for signed URL request."""
    model_config = ConfigDict(from_attributes=True)
    
    filename: str = Field(..., min_length=1, max_length=255, description="Original filename")
    file_size: int = Field(..., gt=0, le=1024*1024*1024, description="File size in bytes (max 1GB)")
    content_type: str = Field(..., min_length=1, description="MIME content type")
    access_level: AccessLevel = Field(AccessLevel.PRIVATE, description="File access level")
    expires_in_hours: int = Field(1, ge=1, le=24, description="URL expiration in hours")
    category: Optional[str] = Field(None, max_length=100, description="File category")
    tags: List[str] = Field(default_factory=list, description="File tags")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom metadata")
    enable_multipart: bool = Field(True, description="Enable multipart upload for large files")
    topic_id: Optional[int] = Field(None, description="Link file to a specific topic")


class InitiateUploadAPI(BaseModel):
    """API model for upload session initiation."""
    model_config = ConfigDict(from_attributes=True)
    
    filename: str = Field(..., min_length=1, max_length=255)
    file_size: int = Field(..., gt=0, le=1024*1024*1024)
    content_type: str = Field(..., min_length=1)
    access_level: AccessLevel = Field(AccessLevel.PRIVATE)
    chunk_size: int = Field(5*1024*1024, ge=1024*1024, le=100*1024*1024)  # 1MB - 100MB
    category: Optional[str] = Field(None, max_length=100)
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CompleteUploadAPI(BaseModel):
    """API model for upload completion."""
    model_config = ConfigDict(from_attributes=True)
    
    upload_session_id: str = Field(..., description="Upload session ID")
    file_hash: Optional[str] = Field(None, description="SHA256 hash for verification")


class ConfirmUploadCompletionAPI(BaseModel):
    """API model for confirming upload completion."""
    model_config = ConfigDict(from_attributes=True)
    
    file_hash: Optional[str] = Field(None, description="SHA256 hash for verification")
    actual_file_size: Optional[int] = Field(None, ge=0, description="Actual uploaded file size in bytes")


class DownloadFileAPI(BaseModel):
    """API model for download request."""
    model_config = ConfigDict(from_attributes=True)
    
    expires_in_hours: int = Field(1, ge=1, le=168, description="URL expiration in hours")
    access_type: str = Field("direct", pattern="^(direct|redirect|inline)$")
    force_download: bool = Field(False, description="Force download instead of inline display")


class UpdateFileAccessAPI(BaseModel):
    """API model for access permission updates."""
    model_config = ConfigDict(from_attributes=True)
    
    access_level: AccessLevel
    expires_at: Optional[datetime] = None
    allowed_users: List[str] = Field(default_factory=list)
    allowed_groups: List[str] = Field(default_factory=list)
    max_downloads: Optional[int] = Field(None, ge=0)


class FileSearchAPI(BaseModel):
    """API model for file search."""
    model_config = ConfigDict(from_attributes=True)
    
    query: Optional[str] = Field(None, description="Search query")
    category: Optional[str] = None
    content_type: Optional[str] = None
    status: Optional[FileStatus] = None
    access_level: Optional[AccessLevel] = None
    owner_id: Optional[str] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    size_min: Optional[int] = Field(None, ge=0)
    size_max: Optional[int] = Field(None, ge=0)
    tags: List[str] = Field(default_factory=list)
    limit: int = Field(50, ge=1, le=1000)
    offset: int = Field(0, ge=0)
    sort_by: str = Field("created_at", pattern="^(created_at|updated_at|file_size|download_count|name)$")
    sort_order: str = Field("desc", pattern="^(asc|desc)$")


# Mock dependency functions (to be replaced with actual authentication)

async def get_current_user_id() -> str:
    """Get current authenticated user ID (simplified for testing)."""
    # This would integrate with your authentication system
    return "user_123"  # Mock user ID


async def get_optional_user() -> Optional[str]:
    """Get current user ID if authenticated, None otherwise."""
    # This would integrate with your authentication system
    return "user_123"  # Mock user ID


async def get_user_groups(user_id: str = Depends(get_current_user_id)) -> Set[str]:
    """Get user groups for authorization."""
    # This would integrate with your authorization system
    return {"default_group"}  # Mock groups


# Legacy factory function has been replaced by Registry dependency injection
# All routes now use DependsFileApplication for automatic dependency injection
# The complex mock implementation has been moved to services.py with proper DI support


# API Routes

@router.post("/upload/signed-url", response_model=SignedUrlResponse, status_code=201)
async def get_signed_upload_url(
    request: GetSignedUrlAPI,
    user_id: str = Depends(get_current_user_id),
    controller: FileApplication = DependsFileApplication
):
    """
    Generate a signed URL for file upload.
    
    This is the core **getSignedURL** endpoint that generates secure upload URLs.
    """
    try:
        # Convert API model to DTO
        upload_request = GetSignedUrlRequest(
            filename=request.filename,
            file_size=request.file_size,
            content_type=request.content_type,
            access_level=request.access_level,
            expires_in_hours=request.expires_in_hours,
            category=request.category,
            tags=request.tags,
            metadata=request.metadata,
            enable_multipart=request.enable_multipart,
            topic_id=request.topic_id
        )
        
        response = await controller.get_signed_upload_url(upload_request, user_id)
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in get_signed_upload_url: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/{file_id}/upload/confirm", 
    response_model=UploadCompletionResponse, 
    status_code=200,
    summary="Confirm Upload Completion",
    description="Confirm that a file upload has completed and trigger RAG processing pipeline",
    responses={
        200: {
            "description": "Upload confirmed successfully and processing started",
            "content": {
                "application/json": {
                    "example": {
                        "file_id": "a2385d89-8824-474c-8740-8a93ef0d5469",
                        "status": "available",
                        "processing_started": True,
                        "task_ids": ["task_embedding_uuid_1", "task_parsing_uuid_2"],
                        "message": "Upload completion confirmed and processing started",
                        "verification_result": {
                            "exists": True,
                            "storage_size": 2048000,
                            "size_verified": True
                        }
                    }
                }
            }
        },
        400: {
            "description": "File already confirmed or invalid status",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "File is already in available status"
                    }
                }
            }
        },
        403: {
            "description": "Permission denied - user doesn't own the file",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "User user_123 does not own file a2385d89-8824-474c-8740-8a93ef0d5469"
                    }
                }
            }
        },
        404: {
            "description": "File not found or upload verification failed",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "File was not found in storage. Upload may have failed."
                    }
                }
            }
        }
    },
    tags=["file-upload"]
)
async def confirm_upload_completion(
    file_id: str = Path(..., description="UUID of the file to confirm upload completion", example="a2385d89-8824-474c-8740-8a93ef0d5469"),
    request: ConfirmUploadCompletionAPI = ConfirmUploadCompletionAPI(),
    user_id: str = Depends(get_current_user_id),
    controller: FileApplication = DependsFileApplication
):
    """
    ## Confirm Upload Completion and Trigger Processing
    
    This endpoint must be called by the client after successfully uploading a file via the signed URL
    to notify the server that the upload is complete and trigger the RAG processing pipeline.
    
    ### Upload Workflow:
    1. **Request signed URL** using `POST /upload/signed-url`
    2. **Upload file directly** to storage using the signed URL
    3. **Call this endpoint** to confirm completion and start processing
    
    ### What This Endpoint Does:
    - ✅ Verifies the file exists in storage
    - ✅ Updates file status from `UPLOADING` to `AVAILABLE`
    - ✅ Validates file size and integrity (if hash provided)
    - ✅ Triggers automatic RAG processing (embedding, parsing, analysis)
    - ✅ Returns processing task IDs for status tracking
    
    ### Security & Validation:
    - User ownership verification (only file owner can confirm)
    - Storage existence check (file must exist in MinIO/S3)
    - Optional file hash validation for integrity verification
    - Size validation to detect partial uploads
    
    ### Processing Pipeline:
    Upon successful confirmation, the following tasks are automatically created:
    - **Document Parsing**: Extract text and metadata
    - **Embedding Generation**: Create vector embeddings for semantic search
    - **Content Analysis**: Keyword extraction, sentiment analysis, classification
    
    ### Error Handling:
    - If file doesn't exist in storage: Returns 404
    - If user doesn't own file: Returns 403
    - If file already confirmed: Returns 400 with current status
    - If storage verification fails: Returns 404 with error details
    
    ### Background Recovery:
    If this endpoint is not called, the background monitor service will automatically
    detect orphaned uploads after 30 minutes and confirm them if they exist in storage.
    """
    try:
        completion_request = ConfirmUploadCompletionRequest(
            file_id=file_id,
            file_hash=request.file_hash,
            actual_file_size=request.actual_file_size
        )

        logger.info(f"Confirming upload completion for file {file_id} with request {completion_request}")
        
        response = await controller.confirm_upload_completion(completion_request, user_id)
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error in confirm_upload_completion: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/upload/initiate", response_model=UploadSessionResponse, status_code=201)
async def initiate_upload(
    request: InitiateUploadAPI,
    user_id: str = Depends(get_current_user_id),
    controller: FileApplication = DependsFileApplication
):
    """Initiate a new upload session for chunked uploads."""
    try:
        upload_request = InitiateUploadRequest(
            filename=request.filename,
            file_size=request.file_size,
            content_type=request.content_type,
            access_level=request.access_level,
            chunk_size=request.chunk_size,
            category=request.category,
            tags=request.tags,
            metadata=request.metadata
        )
        
        response = await controller.initiate_upload(upload_request, user_id)
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in initiate_upload: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{file_id}/download", response_model=DownloadResponse)
async def get_download_url(
    file_id: str = Path(..., description="File ID"),
    request: DownloadFileAPI = DownloadFileAPI(),
    user_id: Optional[str] = Depends(get_optional_user),
    user_groups: Set[str] = Depends(get_user_groups),
    controller: FileApplication = DependsFileApplication
):
    """Generate a download URL for a file."""
    try:
        download_request = DownloadFileRequest(
            file_id=file_id,
            expires_in_hours=request.expires_in_hours,
            access_type=request.access_type,
            force_download=request.force_download
        )
        
        response = await controller.get_download_url(download_request, user_id, user_groups)
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error in get_download_url: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{file_id}", response_model=FileResponse)
async def get_file_info(
    file_id: str = Path(..., description="File ID"),
    user_id: Optional[str] = Depends(get_optional_user),
    user_groups: Set[str] = Depends(get_user_groups),
    controller: FileApplication = DependsFileApplication
):
    """Get detailed information about a file."""
    try:
        response = await controller.get_file_info(file_id, user_id, user_groups)
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error in get_file_info: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/health")
async def health_check(controller: FileApplication = DependsFileApplication):
    """Health check endpoint for file upload service."""
    try:
        response = await controller.health_check()
        status_code = 200 if response["status"] == "healthy" else 503
        return JSONResponse(status_code=status_code, content=response)
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": "file_upload_api",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
        )