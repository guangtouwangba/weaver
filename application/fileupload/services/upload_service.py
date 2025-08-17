"""
File Upload Service

This service handles all file upload operations including signed URL generation,
upload session management, and file processing workflows.
"""

import logging
import hashlib
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from pathlib import Path

from ..domain.entities import FileEntity, UploadSession
from ..domain.value_objects import (
    FileMetadata, AccessPermission, StorageLocation, FileStatus,
    AccessLevel, UploadStatus, UploadConfiguration, FileValidationResult
)
from ..dtos.file_dtos import (
    GetSignedUrlRequest, InitiateUploadRequest, CompleteUploadRequest,
    SignedUrlResponse, UploadSessionResponse, FileResponse
)

# Infrastructure imports
from infrastructure.storage.interfaces import IObjectStorage, IFileManager
from infrastructure.database.repositories.base import BaseRepository

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
        storage: IObjectStorage,
        file_manager: IFileManager,
        file_repository: BaseRepository,
        upload_session_repository: BaseRepository,
        upload_config: UploadConfiguration,
        default_bucket: str = "files"
    ):
        self.storage = storage
        self.file_manager = file_manager
        self.file_repository = file_repository
        self.upload_session_repository = upload_session_repository
        self.upload_config = upload_config
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
            validation_result = self._validate_upload_request(request)
            if not validation_result.is_valid:
                raise ValueError(f"Invalid upload request: {', '.join(validation_result.errors)}")
            
            # Create file metadata
            file_metadata = FileMetadata(
                original_name=request.filename,
                file_size=request.file_size,
                content_type=request.content_type,
                category=request.category,
                tags=frozenset(request.tags),
                custom_attributes=request.metadata
            )
            
            # Create access permission
            access_permission = AccessPermission(
                level=request.access_level,
                expires_at=datetime.utcnow() + timedelta(hours=request.expires_in_hours),
                allowed_users=frozenset([user_id]),
                allowed_operations=frozenset(['read', 'write'])
            )
            
            # Create file entity
            file_entity = FileEntity(
                owner_id=user_id,
                metadata=file_metadata,
                status=FileStatus.UPLOADING,
                access_permission=access_permission
            )
            
            # Generate storage location
            storage_key = self._generate_storage_key(file_metadata)
            storage_location = StorageLocation(
                bucket=self.default_bucket,
                key=storage_key
            )
            file_entity.storage_location = storage_location
            
            # Create upload session
            upload_session = UploadSession(
                file_id=file_entity.id,
                user_id=user_id,
                original_filename=request.filename,
                expected_size=request.file_size,
                content_type=request.content_type,
                chunk_size=self.upload_config.chunk_size,
                storage_key=storage_key
            )
            
            # Determine upload method
            use_multipart = (
                request.enable_multipart and 
                request.file_size > self.upload_config.chunk_size
            )
            
            if use_multipart:
                # Initiate multipart upload
                signed_url, upload_id = await self._initiate_multipart_upload(
                    storage_location, file_metadata
                )
                upload_session.upload_id = upload_id
                upload_session.start_upload(storage_key, upload_id)
            else:
                # Generate simple presigned URL
                signed_url = await self._generate_simple_presigned_url(
                    storage_location, file_metadata, request.expires_in_hours
                )
                upload_session.start_upload(storage_key)
            
            # Save entities to database
            await self.file_repository.create(file_entity.to_dict())
            await self.upload_session_repository.create(upload_session.to_dict())
            
            logger.info(f"Generated signed URL for file {file_entity.id}, session {upload_session.id}")
            
            return SignedUrlResponse.from_domain(file_entity, upload_session, signed_url)
            
        except Exception as e:
            logger.error(f"Failed to generate signed URL for {request.filename}: {e}")
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
            logger.info(f"Initiating upload session for: {request.filename} by user: {user_id}")
            
            # Similar to get_signed_upload_url but focused on session creation
            validation_result = self._validate_upload_request(request)
            if not validation_result.is_valid:
                raise ValueError(f"Invalid upload request: {', '.join(validation_result.errors)}")
            
            # Create entities (similar to above)
            file_metadata = FileMetadata(
                original_name=request.filename,
                file_size=request.file_size,
                content_type=request.content_type,
                category=request.category,
                tags=frozenset(request.tags),
                custom_attributes=request.metadata
            )
            
            access_permission = AccessPermission(
                level=request.access_level,
                allowed_users=frozenset([user_id])
            )
            
            file_entity = FileEntity(
                owner_id=user_id,
                metadata=file_metadata,
                status=FileStatus.UPLOADING,
                access_permission=access_permission
            )
            
            storage_key = self._generate_storage_key(file_metadata)
            storage_location = StorageLocation(
                bucket=self.default_bucket,
                key=storage_key
            )
            file_entity.storage_location = storage_location
            
            upload_session = UploadSession(
                file_id=file_entity.id,
                user_id=user_id,
                original_filename=request.filename,
                expected_size=request.file_size,
                content_type=request.content_type,
                chunk_size=request.chunk_size,
                storage_key=storage_key
            )
            
            # Always use multipart for initiated sessions
            _, upload_id = await self._initiate_multipart_upload(storage_location, file_metadata)
            upload_session.start_upload(storage_key, upload_id)
            
            # Save to database
            await self.file_repository.create(file_entity.to_dict())
            await self.upload_session_repository.create(upload_session.to_dict())
            
            logger.info(f"Initiated upload session {upload_session.id} for file {file_entity.id}")
            
            return UploadSessionResponse.from_domain(upload_session)
            
        except Exception as e:
            logger.error(f"Failed to initiate upload for {request.filename}: {e}")
            raise
    
    async def get_chunk_upload_url(
        self, 
        session_id: str, 
        chunk_number: int, 
        user_id: str
    ) -> str:
        """
        Get a signed URL for uploading a specific chunk.
        """
        try:
            # Retrieve upload session
            session_data = await self.upload_session_repository.get_by_id(session_id)
            if not session_data:
                raise ValueError(f"Upload session {session_id} not found")
            
            upload_session = UploadSession(**session_data)
            
            # Validate user access
            if upload_session.user_id != user_id:
                raise ValueError("Access denied to upload session")
            
            # Check session status
            if not upload_session.is_resumable:
                raise ValueError("Upload session is not resumable")
            
            # Validate chunk number
            if chunk_number < 0 or (upload_session.max_chunks and chunk_number >= upload_session.max_chunks):
                raise ValueError(f"Invalid chunk number: {chunk_number}")
            
            # Generate presigned URL for chunk upload
            chunk_url = await self.storage.generate_presigned_url(
                bucket=self.default_bucket,
                key=upload_session.storage_key,
                expiration=timedelta(hours=1),
                method="PUT"
            )
            
            logger.info(f"Generated chunk upload URL for session {session_id}, chunk {chunk_number}")
            
            return chunk_url
            
        except Exception as e:
            logger.error(f"Failed to generate chunk upload URL for session {session_id}: {e}")
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
            logger.info(f"Completing upload session {request.upload_session_id} by user: {user_id}")
            
            # Retrieve upload session
            session_data = await self.upload_session_repository.get_by_id(request.upload_session_id)
            if not session_data:
                raise ValueError(f"Upload session {request.upload_session_id} not found")
            
            upload_session = UploadSession(**session_data)
            
            # Validate user access
            if upload_session.user_id != user_id:
                raise ValueError("Access denied to upload session")
            
            # Check if all chunks are uploaded
            if upload_session.uploaded_size < upload_session.expected_size:
                raise ValueError("Upload is not complete")
            
            # Retrieve file entity
            file_data = await self.file_repository.get_by_id(upload_session.file_id)
            if not file_data:
                raise ValueError(f"File {upload_session.file_id} not found")
            
            file_entity = FileEntity(**file_data)
            
            # Complete multipart upload if applicable
            if upload_session.upload_id:
                await self._complete_multipart_upload(
                    file_entity.storage_location, 
                    upload_session.upload_id
                )
            
            # Update file hash if provided
            if request.file_hash and file_entity.metadata:
                file_entity.metadata = file_entity.metadata.with_hash(request.file_hash)
            
            # Mark file as available
            file_entity.mark_as_available()
            upload_session.complete_upload()
            
            # Update database
            await self.file_repository.update(file_entity.id, file_entity.to_dict())
            await self.upload_session_repository.update(upload_session.id, upload_session.to_dict())
            
            logger.info(f"Completed upload for file {file_entity.id}")
            
            return FileResponse.from_domain(file_entity)
            
        except Exception as e:
            logger.error(f"Failed to complete upload session {request.upload_session_id}: {e}")
            raise
    
    async def get_upload_status(self, session_id: str, user_id: str) -> UploadSessionResponse:
        """
        Get the current status of an upload session.
        """
        try:
            session_data = await self.upload_session_repository.get_by_id(session_id)
            if not session_data:
                raise ValueError(f"Upload session {session_id} not found")
            
            upload_session = UploadSession(**session_data)
            
            # Validate user access
            if upload_session.user_id != user_id:
                raise ValueError("Access denied to upload session")
            
            return UploadSessionResponse.from_domain(upload_session)
            
        except Exception as e:
            logger.error(f"Failed to get upload status for session {session_id}: {e}")
            raise
    
    async def cancel_upload(self, session_id: str, user_id: str) -> bool:
        """
        Cancel an upload session and clean up resources.
        """
        try:
            logger.info(f"Cancelling upload session {session_id} by user: {user_id}")
            
            session_data = await self.upload_session_repository.get_by_id(session_id)
            if not session_data:
                return False
            
            upload_session = UploadSession(**session_data)
            
            # Validate user access
            if upload_session.user_id != user_id:
                raise ValueError("Access denied to upload session")
            
            # Abort multipart upload if applicable
            if upload_session.upload_id:
                try:
                    await self._abort_multipart_upload(
                        upload_session.storage_key, 
                        upload_session.upload_id
                    )
                except Exception as e:
                    logger.warning(f"Failed to abort multipart upload: {e}")
            
            # Update session status
            upload_session.cancel_upload()
            await self.upload_session_repository.update(upload_session.id, upload_session.to_dict())
            
            # Mark file as failed
            file_data = await self.file_repository.get_by_id(upload_session.file_id)
            if file_data:
                file_entity = FileEntity(**file_data)
                file_entity.mark_as_failed("Upload cancelled by user")
                await self.file_repository.update(file_entity.id, file_entity.to_dict())
            
            logger.info(f"Cancelled upload session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel upload session {session_id}: {e}")
            return False
    
    # Private helper methods
    
    def _validate_upload_request(self, request) -> FileValidationResult:
        """Validate upload request parameters."""
        errors = set()
        warnings = set()
        
        # Check file size limits
        if not self.upload_config.is_file_size_allowed(request.file_size):
            errors.add(f"File size {request.file_size} exceeds maximum allowed size")
        
        # Check content type
        if not self.upload_config.is_content_type_allowed(request.content_type):
            errors.add(f"Content type {request.content_type} is not allowed")
        
        # Check filename
        if not request.filename or len(request.filename) > 255:
            errors.add("Invalid filename")
        
        # Validate file extension
        file_ext = Path(request.filename).suffix.lower()
        if not file_ext:
            warnings.add("File has no extension")
        
        if errors:
            return FileValidationResult.invalid(errors)
        
        result = FileValidationResult.valid()
        if warnings:
            result = result.with_warnings(warnings)
        
        return result
    
    def _generate_storage_key(self, metadata: FileMetadata) -> str:
        """Generate a unique storage key for the file."""
        timestamp = datetime.utcnow().strftime("%Y/%m/%d")
        file_id = hashlib.md5(f"{metadata.original_name}{datetime.utcnow().timestamp()}".encode()).hexdigest()
        file_extension = Path(metadata.original_name).suffix
        
        if metadata.category:
            return f"{metadata.category}/{timestamp}/{file_id}{file_extension}"
        else:
            return f"uploads/{timestamp}/{file_id}{file_extension}"
    
    async def _initiate_multipart_upload(
        self, 
        storage_location: StorageLocation, 
        metadata: FileMetadata
    ) -> tuple[str, str]:
        """Initiate a multipart upload and return the first chunk URL and upload ID."""
        # This would integrate with MinIO multipart upload API
        # For now, we'll simulate the process
        upload_id = f"multipart_{hashlib.md5(storage_location.key.encode()).hexdigest()}"
        
        first_chunk_url = await self.storage.generate_presigned_url(
            bucket=storage_location.bucket,
            key=storage_location.key,
            expiration=self.upload_config.presigned_url_expiration,
            method="PUT"
        )
        
        return first_chunk_url, upload_id
    
    async def _generate_simple_presigned_url(
        self, 
        storage_location: StorageLocation, 
        metadata: FileMetadata, 
        expires_in_hours: int
    ) -> str:
        """Generate a simple presigned URL for direct upload."""
        return await self.storage.generate_presigned_url(
            bucket=storage_location.bucket,
            key=storage_location.key,
            expiration=timedelta(hours=expires_in_hours),
            method="PUT"
        )
    
    async def _complete_multipart_upload(
        self, 
        storage_location: StorageLocation, 
        upload_id: str
    ) -> None:
        """Complete a multipart upload."""
        # This would call MinIO complete multipart upload API
        logger.info(f"Completing multipart upload {upload_id} for {storage_location.key}")
        # Implementation would depend on the specific storage backend
    
    async def _abort_multipart_upload(self, storage_key: str, upload_id: str) -> None:
        """Abort a multipart upload and clean up."""
        # This would call MinIO abort multipart upload API
        logger.info(f"Aborting multipart upload {upload_id} for {storage_key}")
        # Implementation would depend on the specific storage backend