"""
Create topic use case.

Handles creating new topics in the knowledge management system.
"""

from typing import Optional, Dict, Any

from ...core.entities.topic import Topic, TopicStatus
from ...core.repositories.topic_repository import TopicRepository
from ..common.base_use_case import BaseUseCase
from ..common.exceptions import ValidationError, ConflictError


class CreateTopicRequest:
    """Request model for creating a topic."""
    
    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        category: Optional[str] = None,
        user_id: Optional[int] = None,
        parent_topic_id: Optional[int] = None,
        settings: Optional[Dict[str, Any]] = None
    ):
        self.name = name
        self.description = description
        self.category = category
        self.user_id = user_id
        self.parent_topic_id = parent_topic_id
        self.settings = settings or {}


class CreateTopicUseCase(BaseUseCase):
    """Use case for creating a new topic."""
    
    def __init__(self, topic_repository: TopicRepository):
        super().__init__()
        self._topic_repository = topic_repository
    
    async def execute(self, request: CreateTopicRequest) -> Topic:
        """Execute the create topic use case."""
        self.log_execution_start("create_topic", name=request.name)
        
        try:
            # Validate input
            await self._validate_request(request)
            
            # Create topic entity
            topic = Topic(
                name=request.name,
                description=request.description,
                category=request.category,
                status=TopicStatus.ACTIVE,
                user_id=request.user_id,
                parent_topic_id=request.parent_topic_id,
                settings=request.settings
            )
            
            # Save topic
            await self._topic_repository.save(topic)
            
            self.log_execution_end("create_topic", topic_id=topic.id, name=request.name)
            return topic
            
        except Exception as e:
            self.log_error("create_topic", e, name=request.name)
            raise
    
    async def _validate_request(self, request: CreateTopicRequest) -> None:
        """Validate the create topic request."""
        if not request.name or not request.name.strip():
            raise ValidationError("Topic name is required", "name")
        
        if len(request.name) > 255:
            raise ValidationError("Topic name too long (max 255 characters)", "name")
        
        # Check if topic with same name already exists
        existing_topic = await self._topic_repository.get_by_name(request.name)
        if existing_topic:
            raise ConflictError(f"Topic with name '{request.name}' already exists")
        
        # Validate parent topic exists if specified
        if request.parent_topic_id:
            parent_topic = await self._topic_repository.get_by_id(request.parent_topic_id)
            if not parent_topic:
                raise ValidationError("Parent topic does not exist", "parent_topic_id")
            
            if not parent_topic.is_active():
                raise ValidationError("Cannot create child topic under inactive parent", "parent_topic_id")
        
        # Validate description length
        if request.description and len(request.description) > 2000:
            raise ValidationError("Topic description too long (max 2000 characters)", "description")
        
        # Validate category length
        if request.category and len(request.category) > 50:
            raise ValidationError("Topic category too long (max 50 characters)", "category")