"""
Get topic use case.

Handles retrieving topic information.
"""

from ...core.entities.topic import Topic
from ...core.repositories.topic_repository import TopicRepository
from ..common.base_use_case import BaseUseCase
from ..common.exceptions import NotFoundError, ValidationError


class GetTopicUseCase(BaseUseCase):
    """Use case for retrieving a topic."""
    
    def __init__(self, topic_repository: TopicRepository):
        super().__init__()
        self._topic_repository = topic_repository
    
    async def execute(self, topic_id: int) -> Topic:
        """Execute the get topic use case."""
        self.log_execution_start("get_topic", topic_id=topic_id)
        
        try:
            # Validate input
            if not isinstance(topic_id, int) or topic_id <= 0:
                raise ValidationError("Valid topic ID is required", "topic_id")
            
            # Get topic
            topic = await self._topic_repository.get_by_id(topic_id)
            
            if not topic:
                raise NotFoundError("Topic", str(topic_id))
            
            self.log_execution_end("get_topic", topic_id=topic_id)
            return topic
            
        except Exception as e:
            self.log_error("get_topic", e, topic_id=topic_id)
            raise