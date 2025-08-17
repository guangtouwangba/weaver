"""
FastAPI routes for topic file management.

This module provides REST API endpoints for topic file operations
with optimized performance, pagination, and filtering capabilities.
"""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query, Path
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from enum import Enum

# File service imports
from api.unified_file_service import (
    get_unified_files_for_topic, 
    get_unified_file_stats_for_topic,
    get_unified_files_paginated
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/topics", tags=["topic-files"])

# Helper functions
def _parse_metadata(metadata_value) -> Dict[str, Any]:
    """Parse metadata from database value (string or dict)."""
    if metadata_value is None:
        return {}
    if isinstance(metadata_value, dict):
        return metadata_value
    if isinstance(metadata_value, str):
        if not metadata_value or metadata_value.strip() in ['{}', '']:
            return {}
        try:
            import json
            return json.loads(metadata_value)
        except (json.JSONDecodeError, TypeError):
            return {}
    return {}

# Enums for API
class FileSortBy(str, Enum):
    """File sorting options."""
    NAME = "name"
    SIZE = "size"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    FILE_TYPE = "file_type"

class SortOrder(str, Enum):
    """Sort order options."""
    ASC = "asc"
    DESC = "desc"

# Pydantic models
class FileInfo(BaseModel):
    """File information model."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str = Field(..., description="File ID")
    name: str = Field(..., description="File name")
    original_name: str = Field(..., description="Original file name")
    size: Optional[int] = Field(None, description="File size in bytes")
    mime_type: Optional[str] = Field(None, description="MIME type")
    file_type: Optional[str] = Field(None, description="File type category")
    source: str = Field(..., description="File source (legacy/new)")
    upload_url: Optional[str] = Field(None, description="Upload URL if available")
    download_url: Optional[str] = Field(None, description="Download URL if available")
    preview_url: Optional[str] = Field(None, description="Preview URL if available")
    is_processed: bool = Field(False, description="Whether file is processed")
    process_status: Optional[str] = Field(None, description="Processing status")
    content_preview: Optional[str] = Field(None, description="Content preview")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="File metadata")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

class PaginationInfo(BaseModel):
    """Pagination information."""
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    total_items: int = Field(..., description="Total number of items")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_previous: bool = Field(..., description="Whether there is a previous page")

class FileListResponse(BaseModel):
    """Response model for file list."""
    files: List[FileInfo] = Field(..., description="List of files")
    pagination: PaginationInfo = Field(..., description="Pagination information")
    total_size: Optional[int] = Field(None, description="Total size of all files in bytes")

class FileStatsResponse(BaseModel):
    """Response model for file statistics."""
    total_files: int = Field(..., description="Total number of files")
    total_size: Optional[int] = Field(None, description="Total size in bytes")
    file_types: Dict[str, int] = Field(default_factory=dict, description="File type distribution")
    source_breakdown: Dict[str, int] = Field(default_factory=dict, description="Files by source")
    recent_uploads: int = Field(..., description="Files uploaded in last 24 hours")
    processing_status: Dict[str, int] = Field(default_factory=dict, description="Processing status breakdown")
    last_upload: Optional[datetime] = Field(None, description="Last upload timestamp")

# API Routes

@router.get("/{topic_id}/files", response_model=FileListResponse)
async def get_topic_files(
    topic_id: int = Path(..., description="Topic ID"),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(20, ge=1, le=100, description="Number of files per page"),
    sort_by: FileSortBy = Query(FileSortBy.CREATED_AT, description="Sort field"),
    sort_order: SortOrder = Query(SortOrder.DESC, description="Sort order"),
    file_type: Optional[str] = Query(None, description="Filter by file type"),
    search: Optional[str] = Query(None, description="Search in file names"),
    source: Optional[str] = Query(None, description="Filter by source (legacy/new)")
) -> FileListResponse:
    """
    Get paginated files for a topic with filtering and sorting.
    
    Features:
    - **Pagination**: Efficient page-based pagination
    - **Sorting**: Sort by name, size, date, or type
    - **Filtering**: Filter by file type, source, or search term
    - **Performance**: Optimized queries with proper indexing
    
    Parameters:
    - **topic_id**: ID of the topic
    - **page**: Page number (starting from 1)
    - **page_size**: Files per page (1-100)
    - **sort_by**: Field to sort by
    - **sort_order**: Ascending or descending order
    - **file_type**: Filter by MIME type or file extension
    - **search**: Search term for file names
    - **source**: Filter by file source (legacy/new)
    """
    try:
        logger.info(f"Getting files for topic {topic_id}, page {page}, size {page_size}")
        
        # Calculate offset
        offset = (page - 1) * page_size
        
        # Get paginated files with filters
        result = await get_unified_files_paginated(
            topic_id=topic_id,
            limit=page_size,
            offset=offset,
            sort_by=sort_by.value,
            sort_order=sort_order.value,
            file_type=file_type,
            search=search,
            source=source
        )
        
        # Calculate pagination info
        total_items = result.get('total_count', 0)
        total_pages = (total_items + page_size - 1) // page_size
        has_next = page < total_pages
        has_previous = page > 1
        
        # Convert files to response format
        files = []
        for file_data in result.get('files', []):
            file_info = FileInfo(
                id=str(file_data.get('id', '')),
                name=file_data.get('file_name', file_data.get('name', '')),
                original_name=file_data.get('original_name', ''),
                size=file_data.get('file_size'),
                mime_type=file_data.get('mime_type'),
                file_type=file_data.get('file_type', file_data.get('resource_type')),
                source=file_data.get('source', 'unknown'),
                upload_url=file_data.get('upload_url'),
                download_url=file_data.get('download_url'),
                preview_url=file_data.get('preview_url'),
                is_processed=file_data.get('is_parsed', False),
                process_status=file_data.get('parse_status'),
                content_preview=file_data.get('content_preview'),
                metadata=_parse_metadata(file_data.get('metadata', {})),
                created_at=file_data.get('created_at', file_data.get('uploaded_at', datetime.now())),
                updated_at=file_data.get('updated_at')
            )
            files.append(file_info)
        
        pagination = PaginationInfo(
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
            has_next=has_next,
            has_previous=has_previous
        )
        
        return FileListResponse(
            files=files,
            pagination=pagination,
            total_size=result.get('total_size')
        )
        
    except Exception as e:
        logger.error(f"Error getting files for topic {topic_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get topic files: {str(e)}")


@router.get("/{topic_id}/files/stats", response_model=FileStatsResponse)
async def get_topic_file_stats(
    topic_id: int = Path(..., description="Topic ID")
) -> FileStatsResponse:
    """
    Get comprehensive statistics for topic files.
    
    Returns detailed statistics including:
    - **Total file count and size**
    - **File type distribution**
    - **Source breakdown** (legacy vs new system)
    - **Processing status** distribution
    - **Recent activity** metrics
    
    This endpoint is optimized for dashboard displays and overview widgets.
    """
    try:
        logger.info(f"Getting file statistics for topic {topic_id}")
        
        # Get basic stats
        stats = await get_unified_file_stats_for_topic(topic_id)
        
        # Get detailed files for analysis
        files = await get_unified_files_for_topic(topic_id)
        
        # Analyze file types
        file_types = {}
        source_breakdown = {}
        processing_status = {}
        total_size = 0
        recent_uploads = 0
        last_upload = None
        
        now = datetime.now()
        twenty_four_hours_ago = now.timestamp() - (24 * 60 * 60)
        
        for file_data in files:
            # File type analysis
            file_type = file_data.get('file_type', file_data.get('resource_type', 'unknown'))
            file_types[file_type] = file_types.get(file_type, 0) + 1
            
            # Source breakdown
            source = file_data.get('source', 'unknown')
            source_breakdown[source] = source_breakdown.get(source, 0) + 1
            
            # Processing status
            status = file_data.get('parse_status', 'unknown')
            processing_status[status] = processing_status.get(status, 0) + 1
            
            # Size calculation
            size = file_data.get('file_size', 0)
            if size:
                total_size += size
            
            # Recent uploads (last 24 hours)
            created_at = file_data.get('created_at', file_data.get('uploaded_at'))
            if created_at:
                if isinstance(created_at, str):
                    created_timestamp = datetime.fromisoformat(created_at.replace('Z', '+00:00')).timestamp()
                else:
                    created_timestamp = created_at.timestamp()
                
                if created_timestamp > twenty_four_hours_ago:
                    recent_uploads += 1
                
                # Track last upload
                if last_upload is None or created_timestamp > last_upload.timestamp():
                    last_upload = created_at if isinstance(created_at, datetime) else datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        
        return FileStatsResponse(
            total_files=stats.get('total_files', 0),
            total_size=total_size if total_size > 0 else None,
            file_types=file_types,
            source_breakdown=source_breakdown,
            recent_uploads=recent_uploads,
            processing_status=processing_status,
            last_upload=last_upload
        )
        
    except Exception as e:
        logger.error(f"Error getting file statistics for topic {topic_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get file statistics: {str(e)}")


@router.get("/{topic_id}/files/{file_id}", response_model=FileInfo)
async def get_topic_file(
    topic_id: int = Path(..., description="Topic ID"),
    file_id: str = Path(..., description="File ID")
) -> FileInfo:
    """
    Get detailed information about a specific file.
    
    - **topic_id**: ID of the topic
    - **file_id**: ID of the file
    """
    try:
        logger.info(f"Getting file {file_id} for topic {topic_id}")
        
        # Get all files for the topic (could be optimized with direct file lookup)
        files = await get_unified_files_for_topic(topic_id)
        
        # Find the specific file
        file_data = None
        for f in files:
            if str(f.get('id', '')) == file_id:
                file_data = f
                break
        
        if not file_data:
            raise HTTPException(
                status_code=404, 
                detail=f"File {file_id} not found in topic {topic_id}"
            )
        
        return FileInfo(
            id=str(file_data.get('id', '')),
            name=file_data.get('file_name', file_data.get('name', '')),
            original_name=file_data.get('original_name', ''),
            size=file_data.get('file_size'),
            mime_type=file_data.get('mime_type'),
            file_type=file_data.get('file_type', file_data.get('resource_type')),
            source=file_data.get('source', 'unknown'),
            upload_url=file_data.get('upload_url'),
            download_url=file_data.get('download_url'),
            preview_url=file_data.get('preview_url'),
            is_processed=file_data.get('is_parsed', False),
            process_status=file_data.get('parse_status'),
            content_preview=file_data.get('content_preview'),
            metadata=_parse_metadata(file_data.get('metadata', {})),
            created_at=file_data.get('created_at', file_data.get('uploaded_at', datetime.now())),
            updated_at=file_data.get('updated_at')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting file {file_id} for topic {topic_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get file: {str(e)}")


# Health check for file service
@router.get("/{topic_id}/files/health", include_in_schema=False)
async def topic_files_health_check(topic_id: int):
    """Health check endpoint for topic files service."""
    try:
        # Quick test of the unified file service
        stats = await get_unified_file_stats_for_topic(topic_id)
        return {
            "status": "healthy", 
            "service": "topic_files_api", 
            "timestamp": datetime.now().isoformat(),
            "test_topic_id": topic_id,
            "file_count": stats.get('total_files', 0)
        }
    except Exception as e:
        logger.error(f"Topic files health check failed: {e}")
        raise HTTPException(status_code=503, detail="Topic files service unavailable")