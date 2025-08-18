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
from application.fileupload_controller import FileController
from application.dtos.fileupload import (
    GetSignedUrlRequest, InitiateUploadRequest, DownloadFileRequest, SignedUrlResponse, UploadSessionResponse, FileResponse, DownloadResponse
)
from domain.fileupload import AccessLevel, FileStatus
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


async def get_file_controller() -> FileController:
    """Get file controller instance with real MinIO dependencies."""
    from application.fileupload_controller import FileController
    from services.fileupload_services import FileUploadService, FileAccessService
    from infrastructure.config import get_config
    from infrastructure.storage.factory import create_storage_from_env
    
    # Get configuration
    config = get_config()
    
    # Initialize storage with multi-provider support
    storage = create_storage_from_env()
    
    # Helper function to ensure bucket exists
    async def ensure_bucket_exists(storage, bucket_name: str):
        """Ensure the specified bucket exists, create if not."""
        try:
            # Check if bucket exists and create if not
            if not await storage.bucket_exists(bucket_name):
                await storage.create_bucket(bucket_name)
                logger.info(f"Created bucket: {bucket_name}")
            else:
                logger.debug(f"Bucket exists: {bucket_name}")
        except Exception as e:
            logger.error(f"Failed to ensure bucket exists: {e}")
            raise
    
    # Ensure bucket exists
    try:
        await ensure_bucket_exists(storage, config.storage.default_bucket)
    except Exception as e:
        logger.warning(f"Could not ensure bucket exists: {e}")
    
    # Mock repositories for now - in real implementation these would be injected
    class MockFileRepository:
        async def save(self, entity): 
            """Save file entity and trigger RAG processing."""
            try:
                # Save to database (simplified - would use real repository)
                import asyncpg
                import json
                import uuid
                
                file_id = entity.id if hasattr(entity, 'id') else str(uuid.uuid4())
                
                conn = await asyncpg.connect('postgresql://rag_user:rag_password@localhost:5432/rag_db')
                await conn.execute('''
                    INSERT INTO files (
                        id, owner_id, original_name, file_size, content_type, 
                        storage_bucket, storage_key, category, tags, status, 
                        access_level, download_count, topic_id, custom_metadata,
                        created_at, updated_at, is_deleted
                    ) VALUES ($1::uuid, $2, $3, $4, $5, $6, $7, $8, $9, $10::file_status_enum, 
                             $11::access_level_enum, $12, $13, $14::jsonb, $15, $16, $17)
                    ON CONFLICT (id) DO UPDATE SET
                        status = EXCLUDED.status,
                        updated_at = EXCLUDED.updated_at
                ''', 
                    file_id, 
                    entity.owner_id, 
                    entity.metadata.original_name if entity.metadata else "unknown",
                    entity.metadata.file_size if entity.metadata else 0,
                    entity.metadata.content_type if entity.metadata else "application/octet-stream",
                    entity.storage_location.bucket if entity.storage_location else config.storage.default_bucket,
                    entity.storage_location.key if entity.storage_location else f"uploads/{file_id}",
                    entity.metadata.category if entity.metadata else None,
                    entity.metadata.tags if entity.metadata else [],
                    entity.status.value,
                    entity.access_permission.level.value,
                    entity.download_count,
                    entity.topic_id,
                    json.dumps(entity.metadata.custom_metadata if entity.metadata else {}),
                    entity.created_at, 
                    entity.updated_at, 
                    False
                )
                await conn.close()
                logger.info(f"Saved file metadata for {file_id} with topic_id: {entity.topic_id}")
                
                # Trigger async RAG task creation after file metadata is saved
                if entity.status == FileStatus.AVAILABLE and entity.storage_location:
                    await process_file_complete(
                        file_id=file_id,
                        file_path=entity.storage_location.key,
                        file_name=entity.metadata.original_name if entity.metadata else "unknown",
                        file_size=entity.metadata.file_size if entity.metadata else 0,
                        mime_type=entity.metadata.content_type if entity.metadata else "application/octet-stream",
                        topic_id=entity.topic_id,
                        user_id=entity.owner_id,
                        priority=TaskPriority.NORMAL
                    )
                    logger.info(f"Triggered RAG task for file {file_id} with topic_id: {entity.topic_id}")
                
            except Exception as e:
                logger.error(f"Failed to save file metadata: {e}")
                # Continue anyway
        
        async def get_by_id(self, id): 
            return None
    
    class MockUploadSessionRepository:
        async def save(self, entity): 
            pass
        async def get_by_id(self, id): 
            return None
    
    # Create service instances
    upload_service = FileUploadService(
        storage=storage,
        file_repository=MockFileRepository(),
        upload_session_repository=MockUploadSessionRepository(),
        default_bucket=config.storage.default_bucket
    )
    
    access_service = FileAccessService(
        storage=storage,
        file_repository=MockFileRepository()
    )
    
    return FileController(upload_service, access_service)


# API Routes

@router.post("/upload/signed-url", response_model=SignedUrlResponse, status_code=201)
async def get_signed_upload_url(
    request: GetSignedUrlAPI,
    user_id: str = Depends(get_current_user_id),
    controller: FileController = Depends(get_file_controller)
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


@router.post("/upload/initiate", response_model=UploadSessionResponse, status_code=201)
async def initiate_upload(
    request: InitiateUploadAPI,
    user_id: str = Depends(get_current_user_id),
    controller: FileController = Depends(get_file_controller)
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
    controller: FileController = Depends(get_file_controller)
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
    controller: FileController = Depends(get_file_controller)
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
async def health_check(controller: FileController = Depends(get_file_controller)):
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