"""Topic content management endpoints."""

from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from domain_models.topic_content import ContentStatus, ContentSource, ProcessingStatus
from domain_models.topic_content_schemas import (
    TopicContentCreate,
    TopicContentUpdate,
    TopicContentResponse,
    TopicContentListResponse,
    TopicContentStats,
)
from rag_core.services.topic_content_service import TopicContentService
from rag_core.storage.database import get_db
from app.background_tasks import process_uploaded_document, get_upload_dir
import os
import uuid as uuid_lib

router = APIRouter(prefix="/topics/{topic_id}/contents", tags=["topic-contents"])


@router.post("/upload", response_model=TopicContentResponse, status_code=status.HTTP_201_CREATED, summary="Upload file to topic")
async def upload_file_to_topic(
    topic_id: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    description: Optional[str] = Form(default=None),
    tags: Optional[str] = Form(default=None),  # Comma-separated tags
    db: Session = Depends(get_db),
) -> TopicContentResponse:
    """
    Upload a file and associate it with a topic.
    
    This endpoint now uses background processing:
    1. Quickly saves the file to disk
    2. Creates a TopicContent record (processing_status=PROCESSING)
    3. Returns immediately
    4. Processes document in background (ingest into RAG)
    5. Updates content record when done
    
    Args:
        topic_id: Topic UUID
        file: Uploaded file
        description: Optional description
        tags: Optional comma-separated tags
        background_tasks: FastAPI background tasks
        db: Database session
    
    Returns:
        Created content with processing_status=PROCESSING
    """
    import logging
    import time
    logger = logging.getLogger(__name__)
    
    start_time = time.time()
    
    try:
        logger.info(f"📤 [Upload] START - topic: {topic_id}, file: {file.filename}")
        
        # Step 1: Save file to disk using streaming (faster for large files)
        upload_dir = get_upload_dir()
        file_id = uuid_lib.uuid4().hex[:12]
        file_ext = os.path.splitext(file.filename)[1] if file.filename else '.pdf'
        saved_filename = f"{file_id}{file_ext}"
        file_path = upload_dir / saved_filename
        
        logger.info(f"💾 [Upload] Streaming file to: {file_path}")
        
        # Stream file to disk in chunks (faster, lower memory usage)
        total_size = 0
        with open(file_path, 'wb') as f:
            while chunk := await file.read(8192):  # 8KB chunks
                f.write(chunk)
                total_size += len(chunk)
        
        file_size_mb = total_size / (1024 * 1024)
        logger.info(f"✅ [Upload] File saved ({file_size_mb:.2f} MB) in {time.time()-start_time:.2f}s")
        
        # Step 2: Parse tags
        tag_list = []
        if tags and tags.strip():
            tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
        
        # Step 3: Create content record with processing_status=PROCESSING
        logger.info(f"📝 [Upload] Creating content record (status=PROCESSING)...")
        content_data = TopicContentCreate(
            title=file.filename or "Untitled",
            description=description,
            source_type=ContentSource.FILE_UPLOAD,
            source_url=str(file_path),  # Save the file path
            document_id=None,  # Will be set by background task
            tags=tag_list,
        )
        
        content = TopicContentService.create_content(db, topic_id, content_data)
        
        # Update processing_status to PROCESSING (direct DB update)
        content.processing_status = ProcessingStatus.PROCESSING.value
        db.commit()
        db.refresh(content)
        
        logger.info(f"✅ [Upload] Content record created: {content.id}")
        
        # Step 4: Schedule background processing
        logger.info(f"⏰ [Upload] Scheduling background processing...")
        background_tasks.add_task(
            process_uploaded_document,
            content_id=str(content.id),
            file_path=str(file_path),
            filename=file.filename,
            db_session=db,
        )
        
        logger.info(f"✅ [Upload] Complete in {time.time()-start_time:.2f}s")
        logger.info(f"  ├─ Content ID: {content.id}")
        logger.info(f"  ├─ File: {file_path}")
        logger.info(f"  └─ Status: PROCESSING (background task started)")
        
        # Refresh to get updated processing_status
        db.refresh(content)
        response = TopicContentResponse.model_validate(content)
        
        return response
        
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Upload failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )


@router.post("/", response_model=TopicContentResponse, status_code=status.HTTP_201_CREATED, summary="Add content to topic")
def add_content_to_topic(
    topic_id: str,
    content: TopicContentCreate,
    db: Session = Depends(get_db),
) -> TopicContentResponse:
    """
    Add content to a topic (for URL or existing document).
    
    Args:
        topic_id: Topic UUID
        content: Content creation data
        db: Database session
    
    Returns:
        Created content
    """
    created_content = TopicContentService.create_content(db, topic_id, content)
    return TopicContentResponse.model_validate(created_content)


@router.get("/", response_model=TopicContentListResponse, summary="List topic contents")
def list_topic_contents(
    topic_id: str,
    status_filter: Optional[ContentStatus] = Query(None, alias="status", description="Filter by status"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
) -> TopicContentListResponse:
    """
    List all contents for a topic with optional filtering.
    
    Args:
        topic_id: Topic UUID
        status_filter: Optional status filter
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session
    
    Returns:
        List of contents with total count
    """
    contents = TopicContentService.list_contents(
        db, topic_id, status=status_filter, skip=skip, limit=limit
    )
    content_responses = [TopicContentResponse.model_validate(c) for c in contents]
    return TopicContentListResponse(total=len(content_responses), contents=content_responses)


@router.get("/stats", response_model=TopicContentStats, summary="Get content statistics")
def get_content_stats(
    topic_id: str,
    db: Session = Depends(get_db),
) -> TopicContentStats:
    """
    Get content statistics for a topic.
    
    Args:
        topic_id: Topic UUID
        db: Database session
    
    Returns:
        Statistics with counts by status
    """
    return TopicContentService.get_content_stats(db, topic_id)


@router.get("/{content_id}", response_model=TopicContentResponse, summary="Get content by ID")
def get_content(
    topic_id: str,
    content_id: str,
    db: Session = Depends(get_db),
) -> TopicContentResponse:
    """
    Get a specific content by ID.
    
    Args:
        topic_id: Topic UUID (for validation)
        content_id: Content UUID
        db: Database session
    
    Returns:
        Content details
    
    Raises:
        HTTPException: 404 if content not found
    """
    content = TopicContentService.get_content(db, content_id)
    if not content or str(content.topic_id) != topic_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Content with id {content_id} not found in topic {topic_id}"
        )
    return TopicContentResponse.model_validate(content)


@router.put("/{content_id}", response_model=TopicContentResponse, summary="Update content")
def update_content(
    topic_id: str,
    content_id: str,
    content_data: TopicContentUpdate,
    db: Session = Depends(get_db),
) -> TopicContentResponse:
    """
    Update a content (status, understanding level, notes, etc.).
    
    Args:
        topic_id: Topic UUID (for validation)
        content_id: Content UUID
        content_data: Fields to update
        db: Database session
    
    Returns:
        Updated content
    
    Raises:
        HTTPException: 404 if content not found
    """
    content = TopicContentService.update_content(db, content_id, content_data)
    if not content or str(content.topic_id) != topic_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Content with id {content_id} not found in topic {topic_id}"
        )
    return TopicContentResponse.model_validate(content)


@router.delete("/{content_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete content")
def delete_content(
    topic_id: str,
    content_id: str,
    db: Session = Depends(get_db),
) -> None:
    """
    Delete a content from a topic.
    
    Args:
        topic_id: Topic UUID (for validation)
        content_id: Content UUID
        db: Database session
    
    Raises:
        HTTPException: 404 if content not found
    """
    # Verify content belongs to topic
    content = TopicContentService.get_content(db, content_id)
    if not content or str(content.topic_id) != topic_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Content with id {content_id} not found in topic {topic_id}"
        )
    
    if not TopicContentService.delete_content(db, content_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Content with id {content_id} not found"
        )

