"""
FastAPI routes for topic management.

This module provides REST API endpoints for topic-related operations
including CRUD operations, resource management, and search functionality.
"""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Query, Path
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

# Application layer imports
from application.topic import (
    TopicController,
    CreateTopicRequest, UpdateTopicRequest, UploadResourceRequest,
    TopicResponse, ResourceResponse,
    create_topic_controller
)

# Registry dependency injection
from infrastructure.denpendency_injection import DependsTopicController
from domain.topic import TopicStatus, ResourceType

# Exception imports
from api.exceptions import (
    TopicNotFoundError, ResourceNotFoundError, 
    InvalidTopicDataError, ResourceUploadError,
    raise_not_found, raise_validation_error
)

# Unified file service for bridge functionality
from api.unified_file_service import get_unified_files_for_topic, get_unified_file_stats_for_topic

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/topics", tags=["topics"])

# Pydantic models for API validation
class CreateTopicAPI(BaseModel):
    """API model for creating a topic."""
    model_config = ConfigDict(from_attributes=True)
    
    name: str = Field(..., min_length=1, max_length=255, description="Topic name")
    description: Optional[str] = Field(None, max_length=1000, description="Topic description")
    category: Optional[str] = Field(None, max_length=50, description="Topic category")
    user_id: Optional[int] = Field(None, description="User ID who owns this topic")
    conversation_id: Optional[str] = Field(None, max_length=255, description="Associated conversation ID")
    parent_topic_id: Optional[int] = Field(None, description="Parent topic ID for hierarchical topics")
    settings: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Topic settings")
    tags: Optional[List[str]] = Field(default_factory=list, description="Topic tags")


class UpdateTopicAPI(BaseModel):
    """API model for updating a topic."""
    model_config = ConfigDict(from_attributes=True)
    
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Topic name")
    description: Optional[str] = Field(None, max_length=1000, description="Topic description")
    category: Optional[str] = Field(None, max_length=50, description="Topic category")
    status: Optional[TopicStatus] = Field(None, description="Topic status")
    settings: Optional[Dict[str, Any]] = Field(None, description="Topic settings")
    add_tags: Optional[List[str]] = Field(default_factory=list, description="Tags to add")
    remove_tags: Optional[List[str]] = Field(default_factory=list, description="Tags to remove")


class TopicResponseAPI(BaseModel):
    """API response model for topic (optimized for performance)."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    description: Optional[str]
    category: Optional[str]
    status: str
    core_concepts_discovered: int
    concept_relationships: int
    missing_materials_count: int
    total_resources: int
    total_conversations: int
    user_id: Optional[int]
    conversation_id: Optional[str]
    parent_topic_id: Optional[int]
    settings: Dict[str, Any]
    created_at: str
    updated_at: str
    last_accessed_at: str
    tags: List[str] = Field(default_factory=list)
    
    # Deprecated fields (kept for backward compatibility)
    resources: Optional[List[Dict[str, Any]]] = Field(default=None, description="Deprecated: Use /topics/{id}/files instead")
    conversations: Optional[List[Dict[str, Any]]] = Field(default=None, description="Deprecated: Use /topics/{id}/conversations instead")


class ResourceResponseAPI(BaseModel):
    """API response model for resource."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    topic_id: int
    original_name: str
    file_name: str
    file_path: str
    file_size: Optional[int]
    mime_type: Optional[str]
    resource_type: str
    parse_status: str
    is_parsed: bool
    content_preview: Optional[str]
    content_summary: Optional[str]
    uploaded_at: str
    access_url: Optional[str] = None


class TopicSearchParams(BaseModel):
    """API model for topic search parameters."""
    query: str = Field(..., min_length=1, description="Search query")
    category: Optional[str] = Field(None, description="Filter by category")
    status: Optional[TopicStatus] = Field(None, description="Filter by status")
    user_id: Optional[int] = Field(None, description="Filter by user ID")
    limit: int = Field(50, ge=1, le=100, description="Number of results to return")
    offset: int = Field(0, ge=0, description="Number of results to skip")




# Dependency injection with proper session management
from contextlib import asynccontextmanager

@asynccontextmanager
async def get_topic_controller_session():
    """Context manager for topic controller with proper session cleanup."""
    from infrastructure.database.config import AsyncSessionLocal
    
    async with AsyncSessionLocal() as session:
        try:
            # Get configuration
            from infrastructure import get_config, MinIOStorage, MinIOFileManager
            config = get_config()
            
            # Create repositories with the session
            from infrastructure.database.repositories.topic import (
                TopicRepository, TagRepository, TopicResourceRepository, ConversationRepository
            )
            topic_repo = TopicRepository(session)
            tag_repo = TagRepository(session)
            resource_repo = TopicResourceRepository(session)
            conversation_repo = ConversationRepository(session)
            
            # Create storage components
            storage = MinIOStorage(**config.storage.minio_config)
            file_manager = MinIOFileManager(storage, config.storage.default_bucket)
            
            # Create application service
            from application.topic import TopicApplicationService, TopicController
            service = TopicApplicationService(
                topic_repo=topic_repo,
                tag_repo=tag_repo,
                resource_repo=resource_repo,
                conversation_repo=conversation_repo,
                message_broker=None,  # Temporarily disabled
                storage=storage,
                file_manager=file_manager
            )
            
            # Create and yield controller
            controller = TopicController(service)
            yield controller
            
        except Exception as e:
            logger.error(f"Failed to create topic controller: {e}")
            raise HTTPException(status_code=500, detail="Failed to initialize topic service")

# Legacy factory function has been replaced by Registry dependency injection
# All routes now use DependsTopicController for automatic dependency injection


# API Routes

@router.post("/", response_model=TopicResponseAPI, status_code=201)
async def create_topic(
    topic_data: CreateTopicAPI,
    controller: TopicController = DependsTopicController
) -> TopicResponseAPI:
    """
    Create a new topic.
    
    - **name**: Topic name (required)
    - **description**: Optional description
    - **category**: Optional category for organization
    - **user_id**: ID of the user creating the topic
    - **conversation_id**: Associated conversation ID
    - **parent_topic_id**: Parent topic for hierarchical organization
    - **settings**: Custom settings as key-value pairs
    - **tags**: List of tags for categorization
    """
    try:
        request = CreateTopicRequest(
            name=topic_data.name,
            description=topic_data.description,
            category=topic_data.category,
            user_id=topic_data.user_id,
            conversation_id=topic_data.conversation_id,
            parent_topic_id=topic_data.parent_topic_id,
            settings=topic_data.settings or {},
            tags=topic_data.tags or []
        )
        
        response = await controller.create_topic(request)
        return TopicResponseAPI(**response.__dict__)
        
    except Exception as e:
        logger.error(f"Error creating topic: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{topic_id}", response_model=TopicResponseAPI)
async def get_topic(
    topic_id: int = Path(..., description="Topic ID"),
    include_resources: bool = Query(False, description="[Deprecated] Include topic resources - use /topics/{id}/files instead"),
    include_conversations: bool = Query(False, description="[Deprecated] Include topic conversations"),
    controller: TopicController = DependsTopicController
) -> TopicResponseAPI:
    """
    Get a topic by ID (optimized for performance).
    
    **Performance Optimized**: This endpoint now returns only core topic information by default.
    For file lists, use the dedicated `/topics/{topic_id}/files` endpoint.
    
    - **topic_id**: ID of the topic to retrieve
    - **include_resources**: [Deprecated] Use `/topics/{topic_id}/files` instead
    - **include_conversations**: [Deprecated] Use `/topics/{topic_id}/conversations` instead
    """
    try:
        # Get topic with optimized query (no resources by default)
        response = await controller.get_topic(topic_id, False, False)
        if response is None:
            raise_not_found("topic", topic_id)
        
        # Convert to API response format
        topic_data = response.__dict__.copy()
        
        # Update total_resources count efficiently using stats
        try:
            file_stats = await get_unified_file_stats_for_topic(topic_id)
            topic_data['total_resources'] = file_stats.get('total_files', 0)
        except Exception as e:
            logger.warning(f"Failed to get file stats for topic {topic_id}: {e}")
            topic_data['total_resources'] = 0
        
        # Handle backward compatibility for deprecated include_resources parameter
        if include_resources:
            logger.warning(f"include_resources parameter is deprecated. Use /topics/{topic_id}/files instead")
            try:
                unified_files = await get_unified_files_for_topic(topic_id)
                topic_data['resources'] = unified_files
                logger.info(f"[Deprecated] Retrieved {len(unified_files)} files for topic {topic_id}")
            except Exception as e:
                logger.error(f"Failed to get files for topic {topic_id}: {e}")
                topic_data['resources'] = []
        else:
            # Default: no resources for performance
            topic_data['resources'] = None
        
        # Handle conversations (also deprecated)
        if include_conversations:
            logger.warning(f"include_conversations parameter is deprecated")
            # Keep existing behavior for now
        else:
            topic_data['conversations'] = None
        
        return TopicResponseAPI(**topic_data)
        
    except Exception as e:
        logger.error(f"Error getting topic {topic_id}: {e}")
        raise


@router.put("/{topic_id}", response_model=TopicResponseAPI)
async def update_topic(
    topic_id: int = Path(..., description="Topic ID"),
    topic_data: UpdateTopicAPI = ...,
    controller: TopicController = DependsTopicController
) -> TopicResponseAPI:
    """
    Update a topic.
    
    - **topic_id**: ID of the topic to update
    - **name**: New topic name
    - **description**: New description
    - **category**: New category
    - **status**: New status (active, archived, draft, completed)
    - **settings**: Updated settings
    - **add_tags**: Tags to add to the topic
    - **remove_tags**: Tags to remove from the topic
    """
    try:
        request = UpdateTopicRequest(
            name=topic_data.name,
            description=topic_data.description,
            category=topic_data.category,
            status=topic_data.status,
            settings=topic_data.settings,
            add_tags=topic_data.add_tags or [],
            remove_tags=topic_data.remove_tags or []
        )
        
        response = await controller.update_topic(topic_id, request)
        if response is None:
            raise_not_found("topic", topic_id)
        
        return TopicResponseAPI(**response.__dict__)
        
    except Exception as e:
        logger.error(f"Error updating topic {topic_id}: {e}")
        raise


@router.delete("/{topic_id}", status_code=204)
async def delete_topic(
    topic_id: int = Path(..., description="Topic ID"),
    hard_delete: bool = Query(False, description="Permanently delete (default: soft delete)"),
    controller: TopicController = DependsTopicController
):
    """
    Delete a topic.
    
    - **topic_id**: ID of the topic to delete
    - **hard_delete**: If true, permanently delete; otherwise soft delete (default)
    """
    try:
        success = await controller.delete_topic(topic_id, hard_delete)
        if not success:
            raise_not_found("topic", topic_id)
        
        return JSONResponse(status_code=204, content=None)
        
    except Exception as e:
        logger.error(f"Error deleting topic {topic_id}: {e}")
        raise


@router.post("/search", response_model=List[TopicResponseAPI])
async def search_topics(
    search_params: TopicSearchParams,
    controller: TopicController = DependsTopicController
) -> List[TopicResponseAPI]:
    """
    Search topics.
    
    - **query**: Search query to match against topic names and descriptions
    - **category**: Filter by category
    - **status**: Filter by status
    - **user_id**: Filter by user ID
    - **limit**: Maximum number of results (1-100)
    - **offset**: Number of results to skip for pagination
    """
    try:
        responses = await controller.search_topics(
            query=search_params.query,
            category=search_params.category,
            status=search_params.status.value if search_params.status else None,
            user_id=search_params.user_id,
            limit=search_params.limit,
            offset=search_params.offset
        )
        
        return [TopicResponseAPI(**response.__dict__) for response in responses]
        
    except Exception as e:
        logger.error(f"Error searching topics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[TopicResponseAPI])
async def list_topics(
    category: Optional[str] = Query(None, description="Filter by category"),
    status: Optional[TopicStatus] = Query(None, description="Filter by status"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    limit: int = Query(50, ge=1, le=100, description="Number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip")
) -> List[TopicResponseAPI]:
    """
    List topics with optional filtering.
    
    - **category**: Filter by category
    - **status**: Filter by status
    - **user_id**: Filter by user ID
    - **limit**: Maximum number of results (1-100)
    - **offset**: Number of results to skip for pagination
    """
    try:
        async with get_topic_controller_session() as controller:
            # Use search with empty query to list all topics
            responses = await controller.search_topics(
                query="",  # Empty query matches all
                category=category,
                status=status.value if status else None,
                user_id=user_id,
                limit=limit,
                offset=offset
            )
            
            return [TopicResponseAPI(**response.__dict__) for response in responses]
        
    except Exception as e:
        logger.error(f"Error listing topics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Resource management endpoints

@router.post("/{topic_id}/resources", response_model=ResourceResponseAPI, status_code=201)
async def upload_resource(
    topic_id: int = Path(..., description="Topic ID"),
    file: UploadFile = File(..., description="File to upload"),
    resource_type: Optional[ResourceType] = Form(None, description="Resource type"),
    source_url: Optional[str] = Form(None, description="Source URL if imported from web"),
    is_public: bool = Form(False, description="Whether resource is publicly accessible"),
    metadata: Optional[str] = Form(None, description="Additional metadata as JSON string"),
    controller: TopicController = DependsTopicController
) -> ResourceResponseAPI:
    """
    Upload a resource to a topic.
    
    - **topic_id**: ID of the topic to upload to
    - **file**: File to upload
    - **resource_type**: Type of resource (pdf, doc, image, etc.)
    - **source_url**: Original URL if imported from web
    - **is_public**: Whether the resource should be publicly accessible
    - **metadata**: Additional metadata as JSON string
    """
    try:
        # Read file content
        file_content = await file.read()
        
        # Parse metadata if provided
        parsed_metadata = {}
        if metadata:
            import json
            try:
                parsed_metadata = json.loads(metadata)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid metadata JSON")
        
        request = UploadResourceRequest(
            topic_id=topic_id,
            file_data=file_content,
            original_name=file.filename,
            resource_type=resource_type,
            source_url=source_url,
            is_public=is_public,
            metadata=parsed_metadata
        )
        
        response = await controller.upload_resource(request)
        return ResourceResponseAPI(**response.__dict__)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading resource to topic {topic_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{topic_id}/resources", response_model=List[ResourceResponseAPI])
async def get_topic_resources(
    topic_id: int = Path(..., description="Topic ID"),
    controller: TopicController = DependsTopicController
) -> List[ResourceResponseAPI]:
    """
    Get all resources for a topic.
    
    - **topic_id**: ID of the topic
    """
    try:
        responses = await controller.get_topic_resources(topic_id)
        return [ResourceResponseAPI(**response.__dict__) for response in responses]
        
    except Exception as e:
        logger.error(f"Error getting resources for topic {topic_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Health check endpoint
@router.get("/health", include_in_schema=False)
async def health_check():
    """Health check endpoint for topic service."""
    try:
        controller = await get_topic_controller()
        return {"status": "healthy", "service": "topic_api", "timestamp": datetime.now().isoformat()}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")


# Note: Error handlers are registered globally in main.py