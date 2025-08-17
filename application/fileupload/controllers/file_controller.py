"""
File Controller

This controller handles all file-related HTTP operations including upload,
download, access control, and file management through REST API endpoints.
"""

import logging
from typing import Optional, Dict, Any, Set
from datetime import datetime

from ..services.upload_service import FileUploadService
from ..services.access_service import FileAccessService
from ..dtos.file_dtos import (
    GetSignedUrlRequest, InitiateUploadRequest, CompleteUploadRequest,
    DownloadFileRequest, UpdateFileAccessRequest, FileSearchRequest,
    SignedUrlResponse, UploadSessionResponse, FileResponse, DownloadResponse,
    FileListResponse, FileStatsResponse, ErrorResponse
)

logger = logging.getLogger(__name__)


class FileController:
    """
    File management HTTP controller.
    
    This controller orchestrates file operations by coordinating between
    HTTP requests and application services, handling authentication,
    validation, and response formatting.
    """
    
    def __init__(
        self,
        upload_service: FileUploadService,
        access_service: FileAccessService
    ):
        self.upload_service = upload_service
        self.access_service = access_service
    
    # Upload Operations
    
    async def get_signed_upload_url(
        self, 
        request: GetSignedUrlRequest, 
        user_id: str
    ) -> SignedUrlResponse:
        """
        Generate a signed URL for file upload.
        
        This implements the core getSignedURL functionality.
        """
        try:
            logger.info(f"Processing signed URL request for {request.filename} by user {user_id}")
            
            # Validate request
            self._validate_upload_request(request)
            
            # Call service layer
            response = await self.upload_service.get_signed_upload_url(request, user_id)
            
            logger.info(f"Generated signed URL for file {response.file_id}")
            return response
            
        except ValueError as e:
            logger.warning(f"Validation error in get_signed_upload_url: {e}")
            raise
        except Exception as e:
            logger.error(f"Error generating signed URL: {e}")
            raise
    
    async def initiate_upload(
        self, 
        request: InitiateUploadRequest, 
        user_id: str
    ) -> UploadSessionResponse:
        """
        Initiate a new upload session for chunked uploads.
        """
        try:
            logger.info(f"Initiating upload session for {request.filename} by user {user_id}")
            
            # Validate request
            self._validate_upload_request(request)
            
            # Call service layer
            response = await self.upload_service.initiate_upload(request, user_id)
            
            logger.info(f"Initiated upload session {response.session_id}")
            return response
            
        except ValueError as e:
            logger.warning(f"Validation error in initiate_upload: {e}")
            raise
        except Exception as e:
            logger.error(f"Error initiating upload: {e}")
            raise
    
    async def get_chunk_upload_url(
        self, 
        session_id: str, 
        chunk_number: int, 
        user_id: str
    ) -> Dict[str, Any]:
        """
        Get a signed URL for uploading a specific chunk.
        """
        try:
            logger.info(f"Getting chunk upload URL for session {session_id}, chunk {chunk_number}")
            
            # Validate parameters
            if chunk_number < 0:
                raise ValueError("Chunk number must be non-negative")
            
            # Call service layer
            upload_url = await self.upload_service.get_chunk_upload_url(
                session_id, chunk_number, user_id
            )
            
            return {
                "chunk_number": chunk_number,
                "upload_url": upload_url,
                "expires_at": (datetime.utcnow().isoformat() + "Z")  # 1 hour default
            }
            
        except ValueError as e:
            logger.warning(f"Validation error in get_chunk_upload_url: {e}")
            raise
        except Exception as e:
            logger.error(f"Error getting chunk upload URL: {e}")
            raise
    
    async def complete_upload(
        self, 
        request: CompleteUploadRequest, 
        user_id: str
    ) -> FileResponse:
        """
        Complete an upload session and finalize the file.
        """
        try:
            logger.info(f"Completing upload session {request.upload_session_id}")
            
            # Call service layer
            response = await self.upload_service.complete_upload(request, user_id)
            
            logger.info(f"Completed upload for file {response.id}")
            return response
            
        except ValueError as e:
            logger.warning(f"Validation error in complete_upload: {e}")
            raise
        except Exception as e:
            logger.error(f"Error completing upload: {e}")
            raise
    
    async def get_upload_status(
        self, 
        session_id: str, 
        user_id: str
    ) -> UploadSessionResponse:
        """
        Get the current status of an upload session.
        """
        try:
            return await self.upload_service.get_upload_status(session_id, user_id)
        except Exception as e:
            logger.error(f"Error getting upload status: {e}")
            raise
    
    async def cancel_upload(
        self, 
        session_id: str, 
        user_id: str
    ) -> Dict[str, Any]:
        """
        Cancel an upload session.
        """
        try:
            success = await self.upload_service.cancel_upload(session_id, user_id)
            return {"cancelled": success, "session_id": session_id}
        except Exception as e:
            logger.error(f"Error cancelling upload: {e}")
            raise
    
    # Download Operations
    
    async def get_download_url(
        self, 
        request: DownloadFileRequest, 
        user_id: Optional[str] = None,
        user_groups: Set[str] = None
    ) -> DownloadResponse:
        """
        Generate a download URL for a file.
        
        This implements the core downloadFile functionality.
        """
        try:
            logger.info(f"Processing download request for file {request.file_id} by user {user_id}")
            
            # Validate request
            self._validate_download_request(request)
            
            # Call service layer
            response = await self.access_service.get_download_url(
                request, user_id, user_groups or set()
            )
            
            logger.info(f"Generated download URL for file {request.file_id}")
            return response
            
        except ValueError as e:
            logger.warning(f"Validation error in get_download_url: {e}")
            raise
        except PermissionError as e:
            logger.warning(f"Access denied in get_download_url: {e}")
            raise
        except Exception as e:
            logger.error(f"Error generating download URL: {e}")
            raise
    
    async def stream_file(
        self, 
        file_id: str, 
        user_id: Optional[str] = None,
        user_groups: Set[str] = None
    ) -> Dict[str, Any]:
        """
        Stream a file directly (for redirect access type).
        """
        try:
            # Get file info and validate access
            file_info = await self.access_service.get_file_info(
                file_id, user_id, user_groups or set()
            )
            
            # This would typically return a streaming response
            # For now, we'll return file metadata
            return {
                "file_id": file_id,
                "stream_url": f"/api/v1/files/{file_id}/stream",
                "content_type": file_info.content_type,
                "content_length": file_info.file_size,
                "filename": file_info.original_name
            }
            
        except Exception as e:
            logger.error(f"Error streaming file {file_id}: {e}")
            raise
    
    # File Management Operations
    
    async def get_file_info(
        self, 
        file_id: str, 
        user_id: Optional[str] = None,
        user_groups: Set[str] = None
    ) -> FileResponse:
        """
        Get detailed information about a file.
        """
        try:
            return await self.access_service.get_file_info(
                file_id, user_id, user_groups or set()
            )
        except Exception as e:
            logger.error(f"Error getting file info for {file_id}: {e}")
            raise
    
    async def update_file_access(
        self, 
        request: UpdateFileAccessRequest, 
        user_id: str
    ) -> FileResponse:
        """
        Update file access permissions.
        """
        try:
            logger.info(f"Updating access for file {request.file_id} by user {user_id}")
            
            # Validate request
            self._validate_access_update_request(request)
            
            # Call service layer
            response = await self.access_service.update_file_access(request, user_id)
            
            logger.info(f"Updated access for file {request.file_id}")
            return response
            
        except ValueError as e:
            logger.warning(f"Validation error in update_file_access: {e}")
            raise
        except PermissionError as e:
            logger.warning(f"Access denied in update_file_access: {e}")
            raise
        except Exception as e:
            logger.error(f"Error updating file access: {e}")
            raise
    
    async def delete_file(
        self, 
        file_id: str, 
        user_id: str, 
        hard_delete: bool = False
    ) -> Dict[str, Any]:
        """
        Delete a file.
        """
        try:
            logger.info(f"Deleting file {file_id} by user {user_id} (hard={hard_delete})")
            
            success = await self.access_service.delete_file(file_id, user_id, hard_delete)
            
            if success:
                logger.info(f"Successfully deleted file {file_id}")
                return {"deleted": True, "file_id": file_id, "hard_delete": hard_delete}
            else:
                raise ValueError(f"File {file_id} not found or could not be deleted")
                
        except Exception as e:
            logger.error(f"Error deleting file {file_id}: {e}")
            raise
    
    # Search and Listing Operations
    
    async def search_files(
        self, 
        request: FileSearchRequest, 
        user_id: Optional[str] = None,
        user_groups: Set[str] = None
    ) -> FileListResponse:
        """
        Search files with filters.
        """
        try:
            logger.info(f"Searching files for user {user_id}")
            
            # Validate request
            self._validate_search_request(request)
            
            # Call service layer
            response = await self.access_service.search_files(
                request, user_id, user_groups or set()
            )
            
            logger.info(f"Found {len(response.files)} files for user {user_id}")
            return response
            
        except ValueError as e:
            logger.warning(f"Validation error in search_files: {e}")
            raise
        except Exception as e:
            logger.error(f"Error searching files: {e}")
            raise
    
    async def list_user_files(
        self, 
        user_id: str, 
        limit: int = 50, 
        offset: int = 0
    ) -> FileListResponse:
        """
        List files owned by a specific user.
        """
        try:
            # Validate parameters
            if limit <= 0 or limit > 1000:
                raise ValueError("Limit must be between 1 and 1000")
            if offset < 0:
                raise ValueError("Offset must be non-negative")
            
            return await self.access_service.list_user_files(user_id, limit, offset)
            
        except ValueError as e:
            logger.warning(f"Validation error in list_user_files: {e}")
            raise
        except Exception as e:
            logger.error(f"Error listing files for user {user_id}: {e}")
            raise
    
    async def get_public_files(
        self, 
        limit: int = 50, 
        offset: int = 0
    ) -> FileListResponse:
        """
        Get publicly accessible files.
        """
        try:
            # Validate parameters
            if limit <= 0 or limit > 1000:
                raise ValueError("Limit must be between 1 and 1000")
            if offset < 0:
                raise ValueError("Offset must be non-negative")
            
            return await self.access_service.get_public_files(limit, offset)
            
        except ValueError as e:
            logger.warning(f"Validation error in get_public_files: {e}")
            raise
        except Exception as e:
            logger.error(f"Error getting public files: {e}")
            raise
    
    # Statistics and Analytics
    
    async def get_file_stats(
        self, 
        user_id: Optional[str] = None
    ) -> FileStatsResponse:
        """
        Get file statistics.
        """
        try:
            return await self.access_service.get_file_stats(user_id)
        except Exception as e:
            logger.error(f"Error getting file stats: {e}")
            raise
    
    # Health Check
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check for the file upload service.
        """
        try:
            # This could include checks for storage connectivity, database health, etc.
            return {
                "status": "healthy",
                "service": "file_upload_controller",
                "timestamp": datetime.utcnow().isoformat(),
                "version": "1.0.0"
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "service": "file_upload_controller",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
    
    # Private validation methods
    
    def _validate_upload_request(self, request) -> None:
        """Validate upload request parameters."""
        if not request.filename:
            raise ValueError("Filename is required")
        
        if len(request.filename) > 255:
            raise ValueError("Filename too long (max 255 characters)")
        
        if request.file_size <= 0:
            raise ValueError("File size must be positive")
        
        if request.file_size > 1024 * 1024 * 1024:  # 1GB limit
            raise ValueError("File size exceeds maximum allowed (1GB)")
        
        if not request.content_type:
            raise ValueError("Content type is required")
        
        # Validate expires_in_hours if present
        if hasattr(request, 'expires_in_hours'):
            if request.expires_in_hours <= 0 or request.expires_in_hours > 24:
                raise ValueError("Expiration hours must be between 1 and 24")
    
    def _validate_download_request(self, request: DownloadFileRequest) -> None:
        """Validate download request parameters."""
        if not request.file_id:
            raise ValueError("File ID is required")
        
        if request.expires_in_hours <= 0 or request.expires_in_hours > 168:  # Max 1 week
            raise ValueError("Expiration hours must be between 1 and 168")
        
        if request.access_type not in ["direct", "redirect", "inline"]:
            raise ValueError("Access type must be one of: direct, redirect, inline")
    
    def _validate_access_update_request(self, request: UpdateFileAccessRequest) -> None:
        """Validate access update request parameters."""
        if not request.file_id:
            raise ValueError("File ID is required")
        
        if request.max_downloads is not None and request.max_downloads < 0:
            raise ValueError("Max downloads cannot be negative")
        
        if request.expires_at and request.expires_at <= datetime.utcnow():
            raise ValueError("Expiration time must be in the future")
    
    def _validate_search_request(self, request: FileSearchRequest) -> None:
        """Validate search request parameters."""
        if request.limit <= 0 or request.limit > 1000:
            raise ValueError("Limit must be between 1 and 1000")
        
        if request.offset < 0:
            raise ValueError("Offset must be non-negative")
        
        if request.sort_by not in ["created_at", "updated_at", "file_size", "download_count", "name"]:
            raise ValueError("Invalid sort field")
        
        if request.sort_order not in ["asc", "desc"]:
            raise ValueError("Sort order must be 'asc' or 'desc'")
        
        if request.size_min is not None and request.size_min < 0:
            raise ValueError("Minimum size cannot be negative")
        
        if request.size_max is not None and request.size_max < 0:
            raise ValueError("Maximum size cannot be negative")
        
        if (request.size_min is not None and request.size_max is not None and 
            request.size_min > request.size_max):
            raise ValueError("Minimum size cannot be greater than maximum size")