"""
FastAPI routes for resource management.

This module provides REST API endpoints for resource-related operations
including individual resource management, deletion, and access control.
"""

import logging
from typing import Optional, Union
from uuid import UUID
from fastapi import APIRouter, HTTPException, Path, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ConfigDict

# Application layer imports
from application.topic import TopicController, create_topic_controller
from api.topic_routes import get_topic_controller_session, ResourceResponseAPI

# Exception imports
from api.exceptions import raise_not_found

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/resources", tags=["resources"])


class DeleteResourceResponse(BaseModel):
    """Response model for resource/file deletion."""
    model_config = ConfigDict(from_attributes=True)
    
    success: bool = Field(description="Whether the deletion was successful")
    message: str = Field(description="Status message")
    file_id: Union[str, int] = Field(description="ID of the deleted resource/file")
    topic_id: Optional[int] = Field(None, description="ID of the topic the resource belonged to")


class FileResponseAPI(BaseModel):
    """API response model for file."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str = Field(description="File UUID")
    original_name: str
    file_size: Optional[int] = None
    content_type: Optional[str] = None
    topic_id: Optional[int] = None
    status: str
    created_at: str
    updated_at: str


@router.get("/{file_id}", response_model=FileResponseAPI)
async def get_file(
    file_id: str = Path(..., description="File ID (UUID format)")
) -> FileResponseAPI:
    """
    Get a specific file by ID.
    
    This endpoint allows access to individual files across all topics.
    
    - **file_id**: UUID of the file to retrieve
    """
    try:
        file_info = await _get_file_by_id(file_id)
        
        if file_info is None:
            raise_not_found("file", file_id)
            
        return FileResponseAPI(**file_info)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting file {file_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{file_id}", response_model=DeleteResourceResponse)
async def delete_file(
    file_id: str = Path(..., description="File ID (UUID format)"),
    hard_delete: bool = Query(False, description="Permanently delete (default: soft delete)")
) -> DeleteResourceResponse:
    """
    Delete a specific file by ID.
    
    This endpoint allows deletion of individual files across all topics.
    The file will be removed from storage and the database.
    
    - **file_id**: UUID of the file to delete
    - **hard_delete**: If true, permanently delete; otherwise soft delete (default)
    """
    try:
        # First, find the file to get its details
        file_info = await _get_file_by_id(file_id)
        
        if file_info is None:
            raise_not_found("file", file_id)
        
        # Delete the file
        success = await _delete_file_by_id(file_id, file_info.get('topic_id'), hard_delete)
        
        if not success:
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to delete file {file_id}"
            )
        
        message = "File permanently deleted" if hard_delete else "File soft deleted"
        
        return DeleteResourceResponse(
            success=True,
            message=message,
            file_id=file_id,
            topic_id=file_info.get('topic_id')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting file {file_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _get_file_by_id(file_id: str) -> Optional[dict]:
    """
    Helper function to find a file by UUID.
    """
    try:
        from infrastructure.database.config import AsyncSessionLocal
        from sqlalchemy import text
        
        async with AsyncSessionLocal() as session:
            # Get the file directly from the files table
            result = await session.execute(
                text("""
                    SELECT id, original_name, file_size, content_type, topic_id, 
                           status, created_at, updated_at, is_deleted
                    FROM files 
                    WHERE id = :file_id AND is_deleted = FALSE
                """),
                {"file_id": file_id}
            )
            
            file_row = result.fetchone()
            
            if not file_row:
                return None
                
            return {
                "id": str(file_row[0]),
                "original_name": file_row[1],
                "file_size": file_row[2],
                "content_type": file_row[3],
                "topic_id": file_row[4],
                "status": file_row[5],
                "created_at": file_row[6].isoformat() if file_row[6] else "",
                "updated_at": file_row[7].isoformat() if file_row[7] else ""
            }
    
    except Exception as e:
        logger.error(f"Error finding file {file_id}: {e}")
        return None


async def _delete_resource_by_id(
    controller: TopicController, 
    resource_id: int, 
    topic_id: int,
    hard_delete: bool = False
) -> bool:
    """
    Helper function to delete a resource by ID.
    
    This includes both database deletion and storage cleanup.
    """
    try:
        # Use the repository directly for deletion
        from infrastructure.database.config import AsyncSessionLocal
        from infrastructure.database.repositories.topic import TopicResourceRepository
        from infrastructure import get_config, MinIOStorage, MinIOFileManager
        
        async with AsyncSessionLocal() as session:
            resource_repo = TopicResourceRepository(session)
            
            # Get the resource details before deletion for storage cleanup
            resource_entity = await resource_repo.get_by_id(resource_id)
            if not resource_entity:
                return False
                
            # Delete from storage if it exists
            try:
                config = get_config()
                storage = MinIOStorage(**config.storage.minio_config)
                file_manager = MinIOFileManager(storage, config.storage.default_bucket)
                
                # Try to delete the file from storage
                if resource_entity.file_path:
                    # Extract file ID or use the file path
                    file_path = resource_entity.file_path
                    try:
                        # Attempt to delete from MinIO
                        await storage.delete_object(config.storage.default_bucket, file_path)
                        logger.info(f"Deleted file from storage: {file_path}")
                    except Exception as storage_error:
                        logger.warning(f"Could not delete file from storage {file_path}: {storage_error}")
                        # Continue with database deletion even if storage cleanup fails
                        
            except Exception as storage_init_error:
                logger.warning(f"Could not initialize storage for cleanup: {storage_init_error}")
                # Continue with database deletion even if storage cleanup fails
            
            # Delete from database
            success = await resource_repo.delete(resource_id, soft_delete=not hard_delete)
            
            if success:
                # Update the topic's resource count
                if topic_id:
                    try:
                        from infrastructure.database.repositories.topic import TopicRepository
                        topic_repo = TopicRepository(session)
                        topic_entity = await topic_repo.get_by_id(topic_id)
                        if topic_entity and hasattr(topic_entity, 'total_resources'):
                            new_count = max(0, (topic_entity.total_resources or 1) - 1)
                            await topic_repo.update(topic_id, {'total_resources': new_count})
                    except Exception as count_error:
                        logger.warning(f"Could not update topic resource count: {count_error}")
                
                logger.info(f"Successfully deleted resource {resource_id} (hard={hard_delete})")
            
            return success
    
    except Exception as e:
        logger.error(f"Error deleting resource {resource_id}: {e}")
        return False


# Health check endpoint
@router.get("/health", include_in_schema=False)
async def health_check():
    """Health check endpoint for resource service."""
    try:
        # Simple health check - try to access the database
        from infrastructure.database.config import AsyncSessionLocal
        from sqlalchemy import text
        
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        
        return {"status": "healthy", "service": "resource_api"}
    except Exception as e:
        logger.error(f"Resource service health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")


async def _delete_file_by_id(file_id: str, topic_id: Optional[int], hard_delete: bool = False) -> bool:
    """
    Helper function to delete a file by UUID.
    
    This includes both database deletion and storage cleanup.
    """
    try:
        from infrastructure.database.config import AsyncSessionLocal
        from sqlalchemy import text
        from infrastructure import get_config, MinIOStorage, MinIOFileManager
        
        async with AsyncSessionLocal() as session:
            # Get the file details before deletion for storage cleanup
            result = await session.execute(
                text("SELECT id, storage_bucket, storage_key FROM files WHERE id = :file_id"),
                {"file_id": file_id}
            )
            file_row = result.fetchone()
            
            if not file_row:
                return False
                
            storage_bucket = file_row[1]
            storage_key = file_row[2]
            
            # Delete from storage if it exists
            try:
                config = get_config()
                storage = MinIOStorage(**config.storage.minio_config)
                
                if storage_bucket and storage_key:
                    try:
                        await storage.delete_object(storage_bucket, storage_key)
                        logger.info(f"Deleted file from storage: {storage_bucket}/{storage_key}")
                    except Exception as storage_error:
                        logger.warning(f"Could not delete file from storage {storage_bucket}/{storage_key}: {storage_error}")
                        # Continue with database deletion even if storage cleanup fails
                        
            except Exception as storage_init_error:
                logger.warning(f"Could not initialize storage for cleanup: {storage_init_error}")
                # Continue with database deletion even if storage cleanup fails
            
            # Delete from database
            if hard_delete:
                # Permanently delete the file
                await session.execute(
                    text("DELETE FROM files WHERE id = :file_id"),
                    {"file_id": file_id}
                )
            else:
                # Soft delete the file
                from datetime import datetime
                await session.execute(
                    text("UPDATE files SET is_deleted = TRUE, deleted_at = :deleted_at WHERE id = :file_id"),
                    {"file_id": file_id, "deleted_at": datetime.utcnow()}
                )
            
            await session.commit()
            
            # Update the topic's file count if applicable
            if topic_id:
                try:
                    # Get current file count for the topic
                    count_result = await session.execute(
                        text("SELECT COUNT(*) FROM files WHERE topic_id = :topic_id AND is_deleted = FALSE"),
                        {"topic_id": topic_id}
                    )
                    new_count = count_result.scalar()
                    
                    # Update topic's total_resources count
                    await session.execute(
                        text("UPDATE topics SET total_resources = :count WHERE id = :topic_id"),
                        {"count": new_count, "topic_id": topic_id}
                    )
                    await session.commit()
                    
                except Exception as count_error:
                    logger.warning(f"Could not update topic file count: {count_error}")
            
            logger.info(f"Successfully deleted file {file_id} (hard={hard_delete})")
            return True
    
    except Exception as e:
        logger.error(f"Error deleting file {file_id}: {e}")
        return False