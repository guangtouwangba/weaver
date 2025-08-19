"""
Consolidated Application Layer Example

This demonstrates how to merge the Application and Services layers
into a unified structure that eliminates redundancy while maintaining
clear separation of concerns.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from infrastructure.storage.interfaces import IObjectStorage
from application.event.event_bus import EventBus
from infrastructure.messaging.interfaces import IMessageBroker

logger = logging.getLogger(__name__)


# =============================================================================
# Unified DTOs (Data Transfer Objects)
# =============================================================================

@dataclass
class CreateTopicRequest:
    """Request DTO for topic creation."""
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    tags: List[str] = None
    settings: Dict[str, Any] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.settings is None:
            self.settings = {}


@dataclass
class TopicResponse:
    """Response DTO for topic operations."""
    id: int
    name: str
    description: Optional[str]
    category: Optional[str]
    status: str
    tags: List[str]
    resource_count: int
    created_at: datetime
    updated_at: datetime
    
    @classmethod
    def from_entity(cls, entity) -> 'TopicResponse':
        """Create response from database entity."""
        return cls(
            id=entity.id,
            name=entity.name,
            description=entity.description,
            category=entity.category,
            status=entity.status,
            tags=[tag.name for tag in entity.tags] if entity.tags else [],
            resource_count=entity.total_resources or 0,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )


# =============================================================================
# Consolidated Topic Service
# =============================================================================

class TopicService:
    """
    Consolidated Topic Service combining business logic and workflow orchestration.
    
    This service replaces both the TopicApplicationService and topic-related
    workflow services, providing a single point of responsibility for all
    topic operations.
    """
    
    def __init__(self,
                 session: AsyncSession,
                 storage: IObjectStorage,
                 event_bus: EventBus,
                 message_broker: Optional[IMessageBroker] = None):
        """
        Initialize service with required dependencies.
        
        Note: Dependencies are injected rather than created internally,
        following the Dependency Inversion Principle.
        """
        self.session = session
        self.storage = storage
        self.event_bus = event_bus
        self.message_broker = message_broker
        
        # Initialize repositories (could be injected as well)
        from infrastructure.database.repositories.topic import TopicRepository
        self.topic_repo = TopicRepository(session)
    
    async def create_topic(self, request: CreateTopicRequest) -> TopicResponse:
        """
        Create a new topic with complete workflow orchestration.
        
        This method combines:
        - Input validation (from Application layer)
        - Business logic (from Application layer)  
        - Workflow orchestration (from Services layer)
        - Event publishing (from Services layer)
        """
        try:
            # 1. Validate business rules
            await self._validate_topic_creation(request)
            
            # 2. Create topic entity
            topic_data = {
                'name': request.name,
                'description': request.description,
                'category': request.category,
                'settings': request.settings,
                'status': 'active',
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            
            topic_entity = await self.topic_repo.create(topic_data)
            
            # 3. Handle tags if provided
            if request.tags:
                await self._associate_tags(topic_entity.id, request.tags)
            
            # 4. Initialize topic storage structure
            await self._initialize_topic_storage(topic_entity.id)
            
            # 5. Publish domain event
            await self._publish_topic_created_event(topic_entity)
            
            # 6. Commit transaction
            await self.session.commit()
            
            logger.info(f"Created topic {topic_entity.id}: {topic_entity.name}")
            return TopicResponse.from_entity(topic_entity)
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to create topic: {e}")
            raise
    
    async def get_topic(self, topic_id: int) -> Optional[TopicResponse]:
        """Get topic by ID with optimized loading."""
        try:
            topic_entity = await self.topic_repo.get_by_id(topic_id)
            if not topic_entity:
                return None
            
            # Update last accessed timestamp
            await self.topic_repo.update(topic_id, {
                'last_accessed_at': datetime.utcnow()
            })
            
            await self.session.commit()
            return TopicResponse.from_entity(topic_entity)
            
        except Exception as e:
            logger.error(f"Failed to get topic {topic_id}: {e}")
            raise
    
    async def update_topic(self, topic_id: int, request: CreateTopicRequest) -> Optional[TopicResponse]:
        """Update existing topic with complete workflow."""
        try:
            # 1. Check if topic exists
            existing = await self.topic_repo.get_by_id(topic_id)
            if not existing:
                return None
            
            # 2. Validate update business rules
            await self._validate_topic_update(topic_id, request)
            
            # 3. Prepare update data
            update_data = {
                'name': request.name,
                'description': request.description,
                'category': request.category,
                'settings': request.settings,
                'updated_at': datetime.utcnow()
            }
            
            # 4. Update entity
            updated_entity = await self.topic_repo.update(topic_id, update_data)
            
            # 5. Update tags
            if request.tags is not None:
                await self._update_tags(topic_id, request.tags)
            
            # 6. Publish update event
            await self._publish_topic_updated_event(updated_entity)
            
            # 7. Commit transaction
            await self.session.commit()
            
            logger.info(f"Updated topic {topic_id}")
            return TopicResponse.from_entity(updated_entity)
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to update topic {topic_id}: {e}")
            raise
    
    async def delete_topic(self, topic_id: int, hard_delete: bool = False) -> bool:
        """Delete topic with cleanup workflow."""
        try:
            # 1. Validate deletion business rules
            await self._validate_topic_deletion(topic_id)
            
            # 2. Cleanup topic resources if hard delete
            if hard_delete:
                await self._cleanup_topic_storage(topic_id)
            
            # 3. Delete from database
            success = await self.topic_repo.delete(topic_id, soft_delete=not hard_delete)
            
            if success:
                # 4. Publish deletion event
                await self._publish_topic_deleted_event(topic_id, hard_delete)
                
                # 5. Commit transaction
                await self.session.commit()
                
                logger.info(f"Deleted topic {topic_id} (hard={hard_delete})")
            
            return success
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to delete topic {topic_id}: {e}")
            raise
    
    async def list_topics(self, 
                         category: Optional[str] = None,
                         tags: Optional[List[str]] = None,
                         limit: int = 50,
                         offset: int = 0) -> List[TopicResponse]:
        """List topics with filtering."""
        try:
            filters = {}
            if category:
                filters['category'] = category
            if tags:
                filters['tags'] = tags
            
            topics = await self.topic_repo.get_all(
                filters=filters,
                limit=limit,
                offset=offset
            )
            
            return [TopicResponse.from_entity(topic) for topic in topics]
            
        except Exception as e:
            logger.error(f"Failed to list topics: {e}")
            raise
    
    # ==========================================================================
    # Private Helper Methods (Business Logic & Workflows)
    # ==========================================================================
    
    async def _validate_topic_creation(self, request: CreateTopicRequest) -> None:
        """Validate business rules for topic creation."""
        # Check for duplicate names
        existing = await self.topic_repo.get_all(filters={'name': request.name})
        if existing:
            raise ValueError(f"Topic with name '{request.name}' already exists")
        
        # Validate category
        if request.category and not await self._is_valid_category(request.category):
            raise ValueError(f"Invalid category: {request.category}")
        
        # Validate tags
        if request.tags:
            await self._validate_tags(request.tags)
    
    async def _validate_topic_update(self, topic_id: int, request: CreateTopicRequest) -> None:
        """Validate business rules for topic updates."""
        # Check for duplicate names (excluding current topic)
        existing = await self.topic_repo.get_all(filters={'name': request.name})
        if existing and any(t.id != topic_id for t in existing):
            raise ValueError(f"Topic with name '{request.name}' already exists")
    
    async def _validate_topic_deletion(self, topic_id: int) -> None:
        """Validate business rules for topic deletion."""
        # Could check for dependencies, active resources, etc.
        pass
    
    async def _is_valid_category(self, category: str) -> bool:
        """Validate if category is allowed."""
        # Implementation would check against allowed categories
        return True
    
    async def _validate_tags(self, tags: List[str]) -> None:
        """Validate tag format and constraints."""
        for tag in tags:
            if not tag.strip():
                raise ValueError("Empty tags are not allowed")
            if len(tag) > 50:
                raise ValueError(f"Tag too long: {tag}")
    
    async def _associate_tags(self, topic_id: int, tags: List[str]) -> None:
        """Associate tags with topic."""
        # Implementation would handle tag creation and association
        logger.debug(f"Associating tags {tags} with topic {topic_id}")
    
    async def _update_tags(self, topic_id: int, tags: List[str]) -> None:
        """Update topic tags."""
        # Implementation would replace existing tags
        logger.debug(f"Updating tags for topic {topic_id} to {tags}")
    
    async def _initialize_topic_storage(self, topic_id: int) -> None:
        """Initialize storage structure for topic."""
        try:
            folder_path = f"topics/{topic_id}"
            await self.storage.create_folder(folder_path)
            logger.debug(f"Created storage folder for topic {topic_id}")
        except Exception as e:
            logger.warning(f"Failed to create storage folder for topic {topic_id}: {e}")
    
    async def _cleanup_topic_storage(self, topic_id: int) -> None:
        """Cleanup topic storage on hard delete."""
        try:
            folder_path = f"topics/{topic_id}"
            await self.storage.delete_folder(folder_path)
            logger.debug(f"Cleaned up storage for topic {topic_id}")
        except Exception as e:
            logger.warning(f"Failed to cleanup storage for topic {topic_id}: {e}")
    
    async def _publish_topic_created_event(self, topic_entity) -> None:
        """Publish topic creation event."""
        event_data = {
            'topic_id': topic_entity.id,
            'topic_name': topic_entity.name,
            'category': topic_entity.category,
            'created_at': topic_entity.created_at.isoformat()
        }
        
        # Publish to event bus (local)
        await self.event_bus.publish('topic.created', event_data)
        
        # Publish to message broker (distributed) if available
        if self.message_broker:
            await self.message_broker.publish('topic.created', event_data)
    
    async def _publish_topic_updated_event(self, topic_entity) -> None:
        """Publish topic update event."""
        event_data = {
            'topic_id': topic_entity.id,
            'topic_name': topic_entity.name,
            'updated_at': topic_entity.updated_at.isoformat()
        }
        
        await self.event_bus.publish('topic.updated', event_data)
        if self.message_broker:
            await self.message_broker.publish('topic.updated', event_data)
    
    async def _publish_topic_deleted_event(self, topic_id: int, hard_delete: bool) -> None:
        """Publish topic deletion event."""
        event_data = {
            'topic_id': topic_id,
            'hard_delete': hard_delete,
            'deleted_at': datetime.utcnow().isoformat()
        }
        
        await self.event_bus.publish('topic.deleted', event_data)
        if self.message_broker:
            await self.message_broker.publish('topic.deleted', event_data)


# =============================================================================
# Usage Example in API Routes
# =============================================================================

"""
# api/topic_routes.py
from fastapi import APIRouter, Depends, HTTPException
from examples.simplified_dependencies import get_topic_service
from examples.consolidated_services import TopicService, CreateTopicRequest

router = APIRouter(prefix="/api/v1/topics", tags=["topics"])

@router.post("/", response_model=TopicResponse)
async def create_topic(
    request: CreateTopicRequest,
    service: TopicService = Depends(get_topic_service)
):
    try:
        return await service.create_topic(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{topic_id}", response_model=TopicResponse)
async def get_topic(
    topic_id: int,
    service: TopicService = Depends(get_topic_service)
):
    result = await service.get_topic(topic_id)
    if not result:
        raise HTTPException(status_code=404, detail="Topic not found")
    return result

@router.put("/{topic_id}", response_model=TopicResponse)
async def update_topic(
    topic_id: int,
    request: CreateTopicRequest,
    service: TopicService = Depends(get_topic_service)
):
    try:
        result = await service.update_topic(topic_id, request)
        if not result:
            raise HTTPException(status_code=404, detail="Topic not found")
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{topic_id}")
async def delete_topic(
    topic_id: int,
    hard_delete: bool = False,
    service: TopicService = Depends(get_topic_service)
):
    try:
        success = await service.delete_topic(topic_id, hard_delete)
        if not success:
            raise HTTPException(status_code=404, detail="Topic not found")
        return {"message": "Topic deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[TopicResponse])
async def list_topics(
    category: Optional[str] = None,
    tags: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    service: TopicService = Depends(get_topic_service)
):
    tag_list = tags.split(",") if tags else None
    return await service.list_topics(category, tag_list, limit, offset)
"""


# =============================================================================
# Benefits of This Consolidated Approach
# =============================================================================

"""
1. **Single Responsibility**: Each service handles one domain aggregate
2. **Clear Boundaries**: Business logic and workflows are co-located
3. **Easier Testing**: One class to test instead of multiple layers
4. **Reduced Complexity**: No confusion about where to put logic
5. **Better Performance**: Fewer abstractions and method calls
6. **Clearer Dependencies**: All dependencies explicit and injected
7. **Event-Driven**: Built-in support for domain events
8. **Transaction Management**: Proper transaction boundaries
9. **Error Handling**: Consistent error handling patterns
10. **Maintainability**: Less code to maintain and understand

This approach eliminates the confusion between Application and Services layers
while maintaining all the benefits of clean architecture.
"""