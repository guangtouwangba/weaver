"""
File Upload Services

This module contains application services for file upload operations,
orchestrating domain logic with infrastructure concerns.
"""

import logging
from typing import Optional, Dict, Any, Set
from datetime import datetime, timedelta

from domain.file import (
    FileEntity, UploadSession, FileMetadata, AccessPermission, 
    StorageLocation, FileStatus, IFileRepository, IUploadSessionRepository
)
from application.dtos.fileupload import (
    GetSignedUrlRequest, InitiateUploadRequest, CompleteUploadRequest, ConfirmUploadCompletionRequest,
    DownloadFileRequest, SignedUrlResponse, UploadSessionResponse, UploadCompletionResponse, FileResponse, DownloadResponse
)

logger = logging.getLogger(__name__)


class FileUploadService:
    """
    Application service for file upload operations.
    
    This service orchestrates the file upload process, including:
    - Signed URL generation for secure uploads
    - Multi-part upload session management
    - File validation and processing
    - Storage integration and metadata management
    """
    
    def __init__(
        self,
        storage,  # IObjectStorage interface
        file_repository: IFileRepository,  # File repository interface
        upload_session_repository: IUploadSessionRepository,  # Upload session repository interface
        default_bucket: str = "files"
    ):
        self.storage = storage
        self.file_repository = file_repository
        self.upload_session_repository = upload_session_repository
        self.default_bucket = default_bucket
    
    async def get_signed_upload_url(
        self, 
        request: GetSignedUrlRequest, 
        user_id: str
    ) -> SignedUrlResponse:
        """
        Generate a signed URL for file upload.
        
        This is the core implementation of the getSignedURL endpoint.
        """
        try:
            logger.info(f"Generating signed URL for file: {request.filename} by user: {user_id}")
            
            # Validate request
            self._validate_upload_request(request)
            
            # Create file metadata
            file_metadata = FileMetadata(
                original_name=request.filename,
                file_size=request.file_size,
                content_type=request.content_type,
                category=request.category,
                tags=request.tags,
                custom_metadata=request.metadata
            )
            
            # Create access permission
            access_permission = AccessPermission(
                level=request.access_level,
                expires_at=datetime.utcnow() + timedelta(hours=request.expires_in_hours),
                allowed_users={user_id}
            )
            
            # Create file entity
            file_entity = FileEntity(
                owner_id=user_id,
                metadata=file_metadata,
                status=FileStatus.UPLOADING,
                access_permission=access_permission,
                topic_id=request.topic_id
            )
            
            # Generate storage location
            storage_key = self._generate_storage_key(user_id, file_entity.id, request.filename)
            storage_location = StorageLocation(
                bucket=self.default_bucket,
                key=storage_key,
                provider="minio"
            )
            file_entity.storage_location = storage_location
            
            # Save file entity to database
            logger.info(f"Saving file entity {file_entity.id} to repository")
            await self.file_repository.save(file_entity)
            
            # Generate presigned URL
            expiration = timedelta(hours=request.expires_in_hours)
            upload_url = await self.storage.generate_presigned_url(
                bucket=self.default_bucket,
                key=storage_key,
                expiration=expiration,
                method="PUT"
            )
            
            # Calculate multipart parameters
            chunk_size = 5 * 1024 * 1024  # 5MB
            max_chunks = (request.file_size + chunk_size - 1) // chunk_size if request.file_size > chunk_size else 1
            
            return SignedUrlResponse(
                file_id=file_entity.id,
                upload_url=upload_url,
                upload_session_id=f"session_{file_entity.id}",
                expires_at=datetime.utcnow() + expiration,
                multipart_upload_id=f"multipart_{file_entity.id}" if request.enable_multipart else None,
                chunk_size=chunk_size,
                max_chunks=max_chunks
            )
            
        except Exception as e:
            logger.error(f"Error generating signed URL: {e}")
            raise
    
    async def initiate_upload(
        self,
        request: InitiateUploadRequest,
        user_id: str
    ) -> UploadSessionResponse:
        """Initiate a new upload session for chunked uploads."""
        try:
            logger.info(f"Initiating upload session for file: {request.filename}")
            
            # Create upload session
            upload_session = UploadSession(
                user_id=user_id,
                original_filename=request.filename,
                expected_size=request.file_size,
                content_type=request.content_type,
                chunk_size=request.chunk_size
            )
            
            # Generate file ID and storage key
            file_entity = FileEntity(
                owner_id=user_id,
                metadata=FileMetadata(
                    original_name=request.filename,
                    file_size=request.file_size,
                    content_type=request.content_type,
                    category=request.category,
                    tags=request.tags,
                    custom_metadata=request.metadata
                ),
                status=FileStatus.UPLOADING,
                access_permission=AccessPermission(level=request.access_level)
            )
            
            upload_session.file_id = file_entity.id
            storage_key = self._generate_storage_key(user_id, file_entity.id, request.filename)
            
            # Start upload session
            upload_session.start_upload(storage_key)
            
            # Save session and file entity
            await self.upload_session_repository.save(upload_session)
            await self.file_repository.save(file_entity)
            
            return UploadSessionResponse(
                session_id=upload_session.id,
                file_id=file_entity.id,
                status=upload_session.status.value,
                progress_percentage=upload_session.progress_percentage,
                uploaded_size=upload_session.uploaded_size,
                expected_size=upload_session.expected_size,
                uploaded_chunks=len(upload_session.uploaded_chunks),
                total_chunks=upload_session.max_chunks or 0,
                next_chunk_number=upload_session.next_chunk_number,
                expires_at=upload_session.expires_at,
                is_resumable=upload_session.is_resumable
            )
            
        except Exception as e:
            logger.error(f"Error initiating upload: {e}")
            raise
    
    async def get_chunk_upload_url(
        self,
        session_id: str,
        chunk_number: int,
        user_id: str
    ) -> Dict[str, Any]:
        """Get a signed URL for uploading a specific chunk."""
        try:
            # Get upload session
            upload_session = await self.upload_session_repository.get_by_id(session_id)
            if not upload_session:
                raise ValueError(f"Upload session {session_id} not found")
            
            # Verify ownership - DISABLED for development
            # if upload_session.user_id != user_id:
            #     raise PermissionError("Access denied to upload session")
            
            # Check if session is valid
            if upload_session.is_expired:
                raise ValueError("Upload session has expired")
            
            # Generate chunk storage key
            chunk_key = f"{upload_session.storage_key}/chunk_{chunk_number}"
            
            # Generate presigned URL for chunk
            chunk_url = await self.storage.generate_presigned_url(
                bucket=self.default_bucket,
                key=chunk_key,
                expiration=timedelta(hours=1),
                method="PUT"
            )
            
            return {
                "chunk_url": chunk_url,
                "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting chunk upload URL: {e}")
            raise
    
    async def complete_upload(
        self,
        request: CompleteUploadRequest,
        user_id: str
    ) -> FileResponse:
        """Complete an upload session and finalize the file."""
        try:
            # Get upload session
            session_id = request.upload_session_id.replace("session_", "")
            upload_session = await self.upload_session_repository.get_by_id(session_id)
            
            if not upload_session:
                # For direct uploads, try to get file by ID
                file_entity = await self.file_repository.get_by_id(session_id)
                if not file_entity:
                    raise ValueError(f"Upload session or file {session_id} not found")
                
                # Mark file as available
                file_entity.mark_as_available()
                await self.file_repository.save(file_entity)
                
            else:
                # Verify ownership - DISABLED for development
                # if upload_session.user_id != user_id:
                #     raise PermissionError("Access denied to upload session")
                
                # Complete upload session
                upload_session.complete_upload()
                await self.upload_session_repository.save(upload_session)
                
                # Get file entity and mark as available
                file_entity = await self.file_repository.get_by_id(upload_session.file_id)
                if file_entity:
                    file_entity.mark_as_available()
                    await self.file_repository.save(file_entity)
            
            # Return file response
            return self._entity_to_response(file_entity)
            
        except Exception as e:
            logger.error(f"Error completing upload: {e}")
            raise
    
    async def get_upload_status(
        self,
        session_id: str,
        user_id: str
    ) -> UploadSessionResponse:
        """Get the current status of an upload session."""
        try:
            upload_session = await self.upload_session_repository.get_by_id(session_id)
            if not upload_session:
                raise ValueError(f"Upload session {session_id} not found")
            
            # DISABLED for development - ownership check
            # if upload_session.user_id != user_id:
            #     raise PermissionError("Access denied to upload session")
            
            return UploadSessionResponse(
                session_id=upload_session.id,
                file_id=upload_session.file_id,
                status=upload_session.status.value,
                progress_percentage=upload_session.progress_percentage,
                uploaded_size=upload_session.uploaded_size,
                expected_size=upload_session.expected_size,
                uploaded_chunks=len(upload_session.uploaded_chunks),
                total_chunks=upload_session.max_chunks or 0,
                next_chunk_number=upload_session.next_chunk_number,
                expires_at=upload_session.expires_at,
                is_resumable=upload_session.is_resumable
            )
            
        except Exception as e:
            logger.error(f"Error getting upload status: {e}")
            raise
    
    async def cancel_upload(
        self,
        session_id: str,
        user_id: str
    ) -> Dict[str, str]:
        """Cancel an upload session."""
        try:
            upload_session = await self.upload_session_repository.get_by_id(session_id)
            if not upload_session:
                raise ValueError(f"Upload session {session_id} not found")
            
            # DISABLED for development - ownership check
            # if upload_session.user_id != user_id:
            #     raise PermissionError("Access denied to upload session")
            
            # Cancel upload session
            upload_session.cancel_upload()
            await self.upload_session_repository.save(upload_session)
            
            # Mark associated file as failed if exists
            if upload_session.file_id:
                file_entity = await self.file_repository.get_by_id(upload_session.file_id)
                if file_entity:
                    file_entity.mark_as_failed("Upload cancelled")
                    await self.file_repository.save(file_entity)
            
            return {"message": "Upload cancelled successfully"}
            
        except Exception as e:
            logger.error(f"Error cancelling upload: {e}")
            raise
    
    def _validate_upload_request(self, request: GetSignedUrlRequest) -> None:
        """Validate upload request parameters."""
        # Check file size limits
        max_file_size = 1024 * 1024 * 1024  # 1GB
        if request.file_size > max_file_size:
            raise ValueError(f"File size exceeds maximum limit of {max_file_size} bytes")
        
        # Check content type
        allowed_types = [
            'text/', 'image/', 'application/pdf', 'application/msword',
            'application/vnd.openxmlformats-officedocument',
            'application/json', 'application/csv'
        ]
        if not any(request.content_type.startswith(t) for t in allowed_types):
            raise ValueError(f"Content type {request.content_type} not allowed")
        
        # Check filename
        if len(request.filename) > 255:
            raise ValueError("Filename too long")
        
        forbidden_chars = ['<', '>', ':', '"', '|', '?', '*']
        if any(char in request.filename for char in forbidden_chars):
            raise ValueError("Filename contains forbidden characters")
    
    def _generate_storage_key(self, user_id: str, file_id: str, filename: str) -> str:
        """Generate a unique storage key for the file."""
        timestamp = datetime.utcnow().strftime("%Y/%m/%d")
        safe_filename = "".join(c for c in filename if c.isalnum() or c in '.-_')
        return f"uploads/{user_id}/{timestamp}/{file_id}/{safe_filename}"
    
    def _entity_to_response(self, entity: FileEntity) -> FileResponse:
        """Convert file entity to response DTO."""
        return FileResponse(
            id=entity.id,
            original_name=entity.metadata.original_name if entity.metadata else "",
            file_size=entity.metadata.file_size if entity.metadata else 0,
            content_type=entity.metadata.content_type if entity.metadata else "",
            status=entity.status.value,
            access_level=entity.access_permission.level.value,
            download_count=entity.download_count,
            owner_id=entity.owner_id or "",
            category=entity.metadata.category if entity.metadata else None,
            tags=entity.metadata.tags if entity.metadata else [],
            metadata=entity.metadata.custom_metadata if entity.metadata else {},
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            last_accessed_at=entity.last_accessed_at,
            is_available=entity.is_available,
            is_public=entity.is_public,
            file_size_mb=entity.file_size_mb,
            age_days=entity.age_days
        )
    
    async def confirm_upload_completion(
        self,
        request: ConfirmUploadCompletionRequest,
        user_id: str
    ) -> UploadCompletionResponse:
        """
        Confirm that a file upload has completed and trigger processing.
        
        This method:
        1. Verifies the file exists in storage
        2. Updates file status from UPLOADING to AVAILABLE
        3. Triggers RAG processing pipeline
        """
        try:
            logger.info(f"Confirming upload completion for file {request.file_id} by user {user_id}")
            
            # Get the file entity from database
            file_entity = await self.file_repository.get_by_id(request.file_id)
            if not file_entity:
                raise ValueError(f"File {request.file_id} not found")
            
            # Verify ownership - DISABLED for development
            # if file_entity.owner_id != user_id:
            #     raise PermissionError(f"User {user_id} does not own file {request.file_id}")
            
            # Check current status
            if file_entity.status != FileStatus.UPLOADING:
                return UploadCompletionResponse(
                    file_id=request.file_id,
                    status=file_entity.status.value,
                    processing_started=False,
                    message=f"File is already in {file_entity.status.value} status"
                )
            
            # Verify file exists in storage
            verification_result = await self._verify_upload_completion(file_entity, request)
            
            if not verification_result["exists"]:
                raise ValueError("File was not found in storage. Upload may have failed.")
            
            # Update file status to AVAILABLE
            file_entity.status = FileStatus.PROCESSING
            file_entity.updated_at = datetime.utcnow()
            
            # Update actual file size if provided
            if request.actual_file_size and file_entity.metadata:
                file_entity.metadata.file_size = request.actual_file_size
            
            # Save updated entity
            await self.file_repository.update_by_id(file_entity.id, file_entity)
            
            # Trigger RAG processing pipeline
            task_ids = []
            if file_entity.storage_location:
                try:
                    from infrastructure.tasks.service import process_file_complete
                    task_ids = await process_file_complete(
                        file_id=file_entity.id,
                        file_path=file_entity.storage_location.key,
                        file_name=file_entity.metadata.original_name if file_entity.metadata else "unknown",
                        file_size=file_entity.metadata.file_size if file_entity.metadata else 0,
                        mime_type=file_entity.metadata.content_type if file_entity.metadata else "application/octet-stream",
                        topic_id=file_entity.topic_id,
                        user_id=user_id
                    )
                    logger.info(f"Started processing pipeline for file {request.file_id} with task IDs: {task_ids}")
                except Exception as e:
                    logger.error(f"Failed to start processing pipeline for file {request.file_id}: {e}")
                    # Don't fail the completion - the file is uploaded successfully
            
            return UploadCompletionResponse(
                file_id=request.file_id,
                status=FileStatus.AVAILABLE.value,
                processing_started=len(task_ids) > 0,
                task_ids=task_ids,
                message="Upload completion confirmed and processing started" if task_ids else "Upload completion confirmed",
                verification_result=verification_result
            )
            
        except Exception as e:
            logger.error(f"Error confirming upload completion: {e}")
            raise
    
    async def _verify_upload_completion(
        self, 
        file_entity: FileEntity, 
        request: ConfirmUploadCompletionRequest
    ) -> dict:
        """Verify that the upload was completed successfully."""
        try:
            if not file_entity.storage_location:
                return {"exists": False, "error": "No storage location defined"}
            
            # Check if file exists in storage
            exists = await self.storage.object_exists(
                bucket=file_entity.storage_location.bucket,
                key=file_entity.storage_location.key
            )
            
            verification = {"exists": exists}
            
            if exists:
                # Get file size from storage
                try:
                    metadata = await self.storage.get_object_metadata(
                        bucket=file_entity.storage_location.bucket,
                        key=file_entity.storage_location.key
                    )
                    storage_size = metadata.get("size", 0)
                    verification["storage_size"] = storage_size
                    
                    # Compare with expected size
                    expected_size = file_entity.metadata.file_size if file_entity.metadata else 0
                    actual_size = request.actual_file_size or expected_size
                    
                    if storage_size != actual_size:
                        verification["size_mismatch"] = True
                        verification["expected_size"] = actual_size
                        logger.warning(f"Size mismatch for file {request.file_id}: expected {actual_size}, got {storage_size}")
                    else:
                        verification["size_verified"] = True
                        
                except Exception as e:
                    logger.warning(f"Could not verify file size for {request.file_id}: {e}")
                    verification["size_check_failed"] = str(e)
            
            return verification
            
        except Exception as e:
            logger.error(f"Upload verification failed for {request.file_id}: {e}")
            return {"exists": False, "error": str(e)}


class FileAccessService:
    """Service for file access operations."""
    
    def __init__(self, storage, file_repository):
        self.storage = storage
        self.file_repository = file_repository
    
    async def get_download_url(
        self,
        request: DownloadFileRequest,
        user_id: Optional[str],
        user_groups: Set[str]
    ) -> DownloadResponse:
        """Generate a download URL for a file."""
        try:
            # Get file entity
            file_entity = await self.file_repository.get_by_id(request.file_id)
            if not file_entity:
                raise ValueError(f"File {request.file_id} not found")
            
            # Check access permissions - DISABLED for development
            # if not file_entity.can_be_accessed_by(user_id, user_groups):
            #     raise PermissionError("Access denied to file")
            
            # Mark file as accessed
            file_entity.mark_accessed()
            await self.file_repository.save(file_entity)
            
            # Generate download URL
            if file_entity.storage_location:
                expiration = timedelta(hours=request.expires_in_hours)
                download_url = await self.storage.generate_presigned_url(
                    bucket=file_entity.storage_location.bucket,
                    key=file_entity.storage_location.key,
                    expiration=expiration,
                    method="GET"
                )
            else:
                raise ValueError("File storage location not found")
            
            return DownloadResponse(
                file_id=file_entity.id,
                download_url=download_url,
                expires_at=datetime.utcnow() + expiration,
                file_metadata={
                    "original_name": file_entity.metadata.original_name if file_entity.metadata else "",
                    "file_size": file_entity.metadata.file_size if file_entity.metadata else 0,
                    "content_type": file_entity.metadata.content_type if file_entity.metadata else "",
                    "uploaded_at": file_entity.created_at.isoformat()
                },
                access_type=request.access_type,
                content_disposition="attachment" if request.force_download else "inline"
            )
            
        except Exception as e:
            logger.error(f"Error generating download URL: {e}")
            raise