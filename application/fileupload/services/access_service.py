"""
File Access Service

This service handles all file access operations including download URL generation,
access control validation, and audit logging.
"""

import logging
from typing import Optional, Dict, Any, List, Set
from datetime import datetime, timedelta

from ..domain.entities import FileEntity, AccessPolicy
from ..domain.value_objects import AccessLevel, FileStatus
from ..dtos.file_dtos import (
    DownloadFileRequest, UpdateFileAccessRequest, FileSearchRequest,
    DownloadResponse, FileResponse, FileListResponse, FileStatsResponse
)

# Infrastructure imports
from infrastructure.storage.interfaces import IObjectStorage, IFileManager
from infrastructure.database.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class FileAccessService:
    """
    Application service for file access and download operations.
    
    This service manages:
    - Download URL generation with access control
    - File access validation and permissions
    - Audit logging and access tracking
    - File search and listing operations
    """
    
    def __init__(
        self,
        storage: IObjectStorage,
        file_manager: IFileManager,
        file_repository: BaseRepository,
        access_log_repository: BaseRepository,
        default_bucket: str = "files"
    ):
        self.storage = storage
        self.file_manager = file_manager
        self.file_repository = file_repository
        self.access_log_repository = access_log_repository
        self.default_bucket = default_bucket
    
    async def get_download_url(
        self, 
        request: DownloadFileRequest, 
        user_id: Optional[str] = None,
        user_groups: Set[str] = None
    ) -> DownloadResponse:
        """
        Generate a download URL for a file.
        
        This is the core implementation of the downloadFile endpoint.
        """
        try:
            logger.info(f"Generating download URL for file {request.file_id} by user: {user_id}")
            
            # Retrieve file entity
            file_data = await self.file_repository.get_by_id(request.file_id)
            if not file_data:
                raise ValueError(f"File {request.file_id} not found")
            
            file_entity = FileEntity(**file_data)
            
            # Validate access permissions
            if not await self._validate_file_access(file_entity, user_id, user_groups):
                raise PermissionError(f"Access denied to file {request.file_id}")
            
            # Check file availability
            if not file_entity.is_available:
                raise ValueError(f"File {request.file_id} is not available for download")
            
            # Generate download URL based on access type
            download_url = await self._generate_download_url(
                file_entity, 
                request.expires_in_hours, 
                request.access_type
            )
            
            # Record access event
            await self._log_file_access(file_entity, user_id, "download_requested")
            
            # Update file access tracking
            file_entity.mark_accessed()
            await self.file_repository.update(file_entity.id, file_entity.to_dict())
            
            expires_at = datetime.utcnow() + timedelta(hours=request.expires_in_hours)
            
            logger.info(f"Generated download URL for file {file_entity.id}")
            
            return DownloadResponse.from_domain(
                file_entity, 
                download_url, 
                expires_at, 
                request.access_type,
                request.force_download
            )
            
        except Exception as e:
            logger.error(f"Failed to generate download URL for file {request.file_id}: {e}")
            raise
    
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
            file_data = await self.file_repository.get_by_id(file_id)
            if not file_data:
                raise ValueError(f"File {file_id} not found")
            
            file_entity = FileEntity(**file_data)
            
            # For public files or files owned by the user, allow info access
            if not (file_entity.is_public or 
                   file_entity.owner_id == user_id or
                   await self._validate_file_access(file_entity, user_id, user_groups)):
                raise PermissionError(f"Access denied to file {file_id}")
            
            # Record access event
            await self._log_file_access(file_entity, user_id, "info_accessed")
            
            return FileResponse.from_domain(file_entity)
            
        except Exception as e:
            logger.error(f"Failed to get file info for {file_id}: {e}")
            raise
    
    async def search_files(
        self, 
        request: FileSearchRequest, 
        user_id: Optional[str] = None,
        user_groups: Set[str] = None
    ) -> FileListResponse:
        """
        Search files based on criteria with access control.
        """
        try:
            logger.info(f"Searching files for user: {user_id}")
            
            # Build search filters
            filters = self._build_search_filters(request, user_id)
            
            # Execute search
            files_data, total_count = await self.file_repository.search(
                filters=filters,
                limit=request.limit,
                offset=request.offset,
                sort_by=request.sort_by,
                sort_order=request.sort_order
            )
            
            # Convert to domain entities and filter by access
            accessible_files = []
            for file_data in files_data:
                file_entity = FileEntity(**file_data)
                
                # Check access permissions
                if (file_entity.is_public or 
                    file_entity.owner_id == user_id or
                    await self._validate_file_access(file_entity, user_id, user_groups)):
                    accessible_files.append(file_entity)
            
            return FileListResponse.from_domain(
                accessible_files, 
                len(accessible_files),  # Adjusted total for accessible files
                request.limit, 
                request.offset
            )
            
        except Exception as e:
            logger.error(f"Failed to search files: {e}")
            raise
    
    async def list_user_files(
        self, 
        user_id: str, 
        limit: int = 50, 
        offset: int = 0
    ) -> FileListResponse:
        """
        List all files owned by a user.
        """
        try:
            filters = {"owner_id": user_id, "status": FileStatus.AVAILABLE.value}
            
            files_data, total_count = await self.file_repository.search(
                filters=filters,
                limit=limit,
                offset=offset,
                sort_by="created_at",
                sort_order="desc"
            )
            
            file_entities = [FileEntity(**file_data) for file_data in files_data]
            
            return FileListResponse.from_domain(file_entities, total_count, limit, offset)
            
        except Exception as e:
            logger.error(f"Failed to list files for user {user_id}: {e}")
            raise
    
    async def update_file_access(
        self, 
        request: UpdateFileAccessRequest, 
        user_id: str
    ) -> FileResponse:
        """
        Update file access permissions (owner only).
        """
        try:
            logger.info(f"Updating access for file {request.file_id} by user: {user_id}")
            
            file_data = await self.file_repository.get_by_id(request.file_id)
            if not file_data:
                raise ValueError(f"File {request.file_id} not found")
            
            file_entity = FileEntity(**file_data)
            
            # Only file owner can update access permissions
            if file_entity.owner_id != user_id:
                raise PermissionError("Only file owner can update access permissions")
            
            # Create new access permission
            from ..domain.value_objects import AccessPermission
            
            new_permission = AccessPermission(
                level=request.access_level,
                expires_at=request.expires_at,
                allowed_users=frozenset(request.allowed_users),
                allowed_groups=frozenset(request.allowed_groups),
                max_downloads=request.max_downloads
            )
            
            file_entity.update_access_permission(new_permission)
            
            # Update in database
            await self.file_repository.update(file_entity.id, file_entity.to_dict())
            
            # Log the access change
            await self._log_file_access(file_entity, user_id, "access_updated")
            
            logger.info(f"Updated access permissions for file {file_entity.id}")
            
            return FileResponse.from_domain(file_entity)
            
        except Exception as e:
            logger.error(f"Failed to update access for file {request.file_id}: {e}")
            raise
    
    async def delete_file(self, file_id: str, user_id: str, hard_delete: bool = False) -> bool:
        """
        Delete a file (soft delete by default).
        """
        try:
            logger.info(f"Deleting file {file_id} by user: {user_id}")
            
            file_data = await self.file_repository.get_by_id(file_id)
            if not file_data:
                return False
            
            file_entity = FileEntity(**file_data)
            
            # Only file owner can delete
            if file_entity.owner_id != user_id:
                raise PermissionError("Only file owner can delete the file")
            
            if hard_delete:
                # Delete from storage
                if file_entity.storage_location:
                    await self.storage.delete_object(
                        file_entity.storage_location.bucket,
                        file_entity.storage_location.key
                    )
                
                # Hard delete from database
                await self.file_repository.delete(file_id)
            else:
                # Soft delete
                file_entity.soft_delete()
                await self.file_repository.update(file_entity.id, file_entity.to_dict())
            
            # Log the deletion
            await self._log_file_access(file_entity, user_id, "deleted")
            
            logger.info(f"Deleted file {file_id} (hard={hard_delete})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete file {file_id}: {e}")
            return False
    
    async def get_file_stats(self, user_id: Optional[str] = None) -> FileStatsResponse:
        """
        Get file statistics for a user or system-wide.
        """
        try:
            # Build filters for stats query
            filters = {}
            if user_id:
                filters["owner_id"] = user_id
            
            # This would be implemented with optimized database queries
            stats_data = await self._calculate_file_stats(filters)
            
            return FileStatsResponse.create(stats_data)
            
        except Exception as e:
            logger.error(f"Failed to get file stats: {e}")
            raise
    
    async def get_public_files(self, limit: int = 50, offset: int = 0) -> FileListResponse:
        """
        Get publicly accessible files.
        """
        try:
            filters = {
                "access_level": AccessLevel.PUBLIC_READ.value,
                "status": FileStatus.AVAILABLE.value
            }
            
            files_data, total_count = await self.file_repository.search(
                filters=filters,
                limit=limit,
                offset=offset,
                sort_by="created_at",
                sort_order="desc"
            )
            
            file_entities = [FileEntity(**file_data) for file_data in files_data]
            
            return FileListResponse.from_domain(file_entities, total_count, limit, offset)
            
        except Exception as e:
            logger.error(f"Failed to get public files: {e}")
            raise
    
    # Private helper methods
    
    async def _validate_file_access(
        self, 
        file_entity: FileEntity, 
        user_id: Optional[str],
        user_groups: Set[str] = None
    ) -> bool:
        """
        Validate if a user can access a file.
        """
        # Owner always has access
        if user_id and file_entity.owner_id == user_id:
            return True
        
        # Check file-level permissions
        if not file_entity.can_be_accessed_by(user_id, user_groups or set()):
            return False
        
        # TODO: Check policy-based access control
        # This would evaluate AccessPolicy entities that might apply to this file
        
        return True
    
    async def _generate_download_url(
        self, 
        file_entity: FileEntity, 
        expires_in_hours: int,
        access_type: str
    ) -> str:
        """
        Generate the appropriate download URL based on access type.
        """
        if not file_entity.storage_location:
            raise ValueError("File has no storage location")
        
        expiration = timedelta(hours=expires_in_hours)
        
        if access_type == "direct":
            # Generate presigned URL for direct access
            return await self.storage.generate_presigned_url(
                bucket=file_entity.storage_location.bucket,
                key=file_entity.storage_location.key,
                expiration=expiration,
                method="GET"
            )
        elif access_type == "redirect":
            # Return a redirect URL (through our API)
            return f"/api/v1/files/{file_entity.id}/stream"
        else:  # inline
            # Generate presigned URL with inline content disposition
            return await self.storage.generate_presigned_url(
                bucket=file_entity.storage_location.bucket,
                key=file_entity.storage_location.key,
                expiration=expiration,
                method="GET"
            )
    
    async def _log_file_access(
        self, 
        file_entity: FileEntity, 
        user_id: Optional[str], 
        action: str
    ) -> None:
        """
        Log file access for audit purposes.
        """
        try:
            access_log = {
                "file_id": file_entity.id,
                "user_id": user_id,
                "action": action,
                "timestamp": datetime.utcnow(),
                "file_name": file_entity.metadata.original_name if file_entity.metadata else None,
                "file_size": file_entity.metadata.file_size if file_entity.metadata else None,
                "ip_address": None,  # Would be populated from request context
                "user_agent": None   # Would be populated from request context
            }
            
            await self.access_log_repository.create(access_log)
            
        except Exception as e:
            # Don't fail the main operation if logging fails
            logger.warning(f"Failed to log file access: {e}")
    
    def _build_search_filters(self, request: FileSearchRequest, user_id: Optional[str]) -> Dict[str, Any]:
        """
        Build database filters from search request.
        """
        filters = {}
        
        if request.query:
            filters["search_query"] = request.query
        if request.category:
            filters["category"] = request.category
        if request.content_type:
            filters["content_type"] = request.content_type
        if request.status:
            filters["status"] = request.status.value
        if request.access_level:
            filters["access_level"] = request.access_level.value
        if request.owner_id:
            filters["owner_id"] = request.owner_id
        if request.created_after:
            filters["created_after"] = request.created_after
        if request.created_before:
            filters["created_before"] = request.created_before
        if request.size_min:
            filters["size_min"] = request.size_min
        if request.size_max:
            filters["size_max"] = request.size_max
        if request.tags:
            filters["tags"] = request.tags
        
        # Add user access constraints
        if user_id:
            # User can see their own files + public files + shared files
            filters["user_access"] = user_id
        else:
            # Anonymous users can only see public files
            filters["access_level"] = AccessLevel.PUBLIC_READ.value
        
        return filters
    
    async def _calculate_file_stats(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate file statistics based on filters.
        """
        # This would be implemented with optimized database aggregation queries
        # For now, we'll return a placeholder structure
        
        return {
            "total_files": 0,
            "total_size_bytes": 0,
            "files_by_status": {},
            "files_by_access_level": {},
            "files_by_content_type": {},
            "average_file_size_mb": 0,
            "total_downloads": 0,
            "most_downloaded_files": [],
            "recent_uploads": [],
            "storage_usage_by_category": {}
        }