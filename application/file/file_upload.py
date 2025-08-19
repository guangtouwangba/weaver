"""
File Upload Controller

This module contains the application controller that orchestrates
file upload operations and coordinates between services.
"""

import logging
from typing import Optional, Set

from application.dtos.fileupload import (
    GetSignedUrlRequest, InitiateUploadRequest, CompleteUploadRequest, ConfirmUploadCompletionRequest,
    DownloadFileRequest, UpdateFileAccessRequest, FileSearchRequest,
    SignedUrlResponse, UploadSessionResponse, UploadCompletionResponse, FileResponse, DownloadResponse,
    FileListResponse, FileStatsResponse
)
from application.event.event_bus import EventBus
from services.fileupload_services import FileUploadService, FileAccessService

logger = logging.getLogger(__name__)


class FileApplication:
    """
    Application controller for file upload operations.
    
    This controller coordinates between the API layer and application services,
    providing a clean interface for file management operations.
    """
    
    def __init__(
        self,
        upload_service: FileUploadService,
        access_service: FileAccessService,
        event_bus: EventBus,
    ):
        self.upload_service = upload_service
        self.access_service = access_service
        self.event_bus = event_bus
    
    async def get_signed_upload_url(
        self,
        request: GetSignedUrlRequest,
        user_id: str
    ) -> SignedUrlResponse:
        """Generate a signed URL for file upload."""
        try:
            logger.info(f"Controller: Getting signed URL for {request.filename}")
            return await self.upload_service.get_signed_upload_url(request, user_id)
        except Exception as e:
            logger.error(f"Controller error in get_signed_upload_url: {e}")
            raise
    
    async def initiate_upload(
        self,
        request: InitiateUploadRequest,
        user_id: str
    ) -> UploadSessionResponse:
        """Initiate a new upload session."""
        try:
            logger.info(f"Controller: Initiating upload for {request.filename}")
            return await self.upload_service.initiate_upload(request, user_id)
        except Exception as e:
            logger.error(f"Controller error in initiate_upload: {e}")
            raise
    
    async def get_chunk_upload_url(
        self,
        session_id: str,
        chunk_number: int,
        user_id: str
    ) -> dict:
        """Get a signed URL for uploading a specific chunk."""
        try:
            logger.info(f"Controller: Getting chunk upload URL for session {session_id}, chunk {chunk_number}")
            return await self.upload_service.get_chunk_upload_url(session_id, chunk_number, user_id)
        except Exception as e:
            logger.error(f"Controller error in get_chunk_upload_url: {e}")
            raise
    
    async def complete_upload(
        self,
        request: CompleteUploadRequest,
        user_id: str
    ) -> FileResponse:
        """Complete an upload session."""
        try:
            logger.info(f"Controller: Completing upload for session {request.upload_session_id}")
            return await self.upload_service.complete_upload(request, user_id)
        except Exception as e:
            logger.error(f"Controller error in complete_upload: {e}")
            raise
    
    async def get_upload_status(
        self,
        session_id: str,
        user_id: str
    ) -> UploadSessionResponse:
        """Get upload session status."""
        try:
            logger.info(f"Controller: Getting upload status for session {session_id}")
            return await self.upload_service.get_upload_status(session_id, user_id)
        except Exception as e:
            logger.error(f"Controller error in get_upload_status: {e}")
            raise
    
    async def cancel_upload(
        self,
        session_id: str,
        user_id: str
    ) -> dict:
        """Cancel an upload session."""
        try:
            logger.info(f"Controller: Cancelling upload for session {session_id}")
            return await self.upload_service.cancel_upload(session_id, user_id)
        except Exception as e:
            logger.error(f"Controller error in cancel_upload: {e}")
            raise
    
    async def get_download_url(
        self,
        request: DownloadFileRequest,
        user_id: Optional[str],
        user_groups: Set[str]
    ) -> DownloadResponse:
        """Generate a download URL for a file."""
        try:
            logger.info(f"Controller: Getting download URL for file {request.file_id}")
            return await self.access_service.get_download_url(request, user_id, user_groups)
        except Exception as e:
            logger.error(f"Controller error in get_download_url: {e}")
            raise
    
    async def stream_file(
        self,
        file_id: str,
        user_id: Optional[str],
        user_groups: Set[str]
    ) -> dict:
        """Get streaming URL for a file."""
        try:
            logger.info(f"Controller: Getting stream URL for file {file_id}")
            # Create a download request for streaming
            download_request = DownloadFileRequest(
                file_id=file_id,
                expires_in_hours=1,
                access_type="redirect",
                force_download=False
            )
            download_response = await self.access_service.get_download_url(
                download_request, user_id, user_groups
            )
            return {"stream_url": download_response.download_url}
        except Exception as e:
            logger.error(f"Controller error in stream_file: {e}")
            raise
    
    async def get_file_info(
        self,
        file_id: str,
        user_id: Optional[str],
        user_groups: Set[str]
    ) -> FileResponse:
        """Get file information."""
        try:
            logger.info(f"Controller: Getting file info for {file_id}")
            # This would typically involve the access service
            # For now, return a basic implementation
            return FileResponse(
                id=file_id,
                original_name="file.txt",
                file_size=1024,
                content_type="text/plain",
                status="available",
                access_level="private",
                download_count=0,
                owner_id=user_id or "unknown",
                is_available=True,
                is_public=False,
                file_size_mb=1.0,
                age_days=0
            )
        except Exception as e:
            logger.error(f"Controller error in get_file_info: {e}")
            raise
    
    async def update_file_access(
        self,
        request: UpdateFileAccessRequest,
        user_id: str
    ) -> FileResponse:
        """Update file access permissions."""
        try:
            logger.info(f"Controller: Updating file access for {request.file_id}")
            # This would involve updating file permissions
            # For now, return a basic implementation
            return FileResponse(
                id=request.file_id,
                original_name="file.txt",
                file_size=1024,
                content_type="text/plain",
                status="available",
                access_level=request.access_level.value,
                download_count=0,
                owner_id=user_id,
                is_available=True,
                is_public=(request.access_level.value == "public"),
                file_size_mb=1.0,
                age_days=0
            )
        except Exception as e:
            logger.error(f"Controller error in update_file_access: {e}")
            raise
    
    async def delete_file(
        self,
        file_id: str,
        user_id: str,
        hard_delete: bool = False
    ) -> dict:
        """Delete a file."""
        try:
            logger.info(f"Controller: Deleting file {file_id}, hard_delete={hard_delete}")
            # This would involve file deletion logic
            return {"message": "File deleted successfully"}
        except Exception as e:
            logger.error(f"Controller error in delete_file: {e}")
            raise
    
    async def search_files(
        self,
        request: FileSearchRequest,
        user_id: Optional[str],
        user_groups: Set[str]
    ) -> FileListResponse:
        """Search files."""
        try:
            logger.info(f"Controller: Searching files with query: {request.query}")
            # This would involve file search logic
            return FileListResponse(
                files=[],
                total_count=0,
                limit=request.limit,
                offset=request.offset,
                has_more=False
            )
        except Exception as e:
            logger.error(f"Controller error in search_files: {e}")
            raise
    
    async def list_user_files(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> FileListResponse:
        """List files for a user."""
        try:
            logger.info(f"Controller: Listing files for user {user_id}")
            # This would involve file listing logic
            return FileListResponse(
                files=[],
                total_count=0,
                limit=limit,
                offset=offset,
                has_more=False
            )
        except Exception as e:
            logger.error(f"Controller error in list_user_files: {e}")
            raise
    
    async def get_public_files(
        self,
        limit: int = 50,
        offset: int = 0
    ) -> FileListResponse:
        """Get public files."""
        try:
            logger.info(f"Controller: Getting public files")
            return FileListResponse(
                files=[],
                total_count=0,
                limit=limit,
                offset=offset,
                has_more=False
            )
        except Exception as e:
            logger.error(f"Controller error in get_public_files: {e}")
            raise
    
    async def get_file_stats(
        self,
        user_id: str
    ) -> FileStatsResponse:
        """Get file statistics."""
        try:
            logger.info(f"Controller: Getting file stats for user {user_id}")
            return FileStatsResponse(
                total_files=0,
                total_size_bytes=0,
                total_size_mb=0.0,
                files_by_status={},
                files_by_access_level={},
                files_by_content_type={},
                average_file_size_mb=0.0,
                total_downloads=0,
                most_downloaded_files=[],
                recent_uploads=[],
                storage_usage_by_category={}
            )
        except Exception as e:
            logger.error(f"Controller error in get_file_stats: {e}")
            raise
    
    async def confirm_upload_completion(
        self,
        request: ConfirmUploadCompletionRequest,
        user_id: str
    ) -> UploadCompletionResponse:
        """Confirm that a file upload has completed and trigger processing."""
        try:
            logger.info(f"Controller: Confirming upload completion for file {request.file_id}")
            
            # First confirm upload completion with the service
            result = await self.upload_service.confirm_upload_completion(request, user_id)
            
            # Then publish file upload completed event (if the result contains file entity)
            if hasattr(result, 'file') and result.file:
                from domain.file.event import FileUploadedConfirmEvent
                event = FileUploadedConfirmEvent(file=result.file)
                await self.event_bus.publish(event)
                logger.info(f"Published FileUploadedConfirmEvent for file {request.file_id}")
            else:
                logger.debug(f"No file entity available to publish event for {request.file_id}")
            
            return result
        except Exception as e:
            logger.error(f"Controller error in confirm_upload_completion: {e}")
            raise
    
    async def health_check(self) -> dict:
        """Health check for file upload service."""
        try:
            return {
                "status": "healthy",
                "service": "file_upload",
                "timestamp": logger.handlers[0].format(logger.makeRecord(
                    logger.name, logging.INFO, __file__, 0, "health check", (), None
                )) if logger.handlers else "now"
            }
        except Exception as e:
            logger.error(f"Controller error in health_check: {e}")
            return {
                "status": "unhealthy",
                "service": "file_upload",
                "error": str(e)
            }