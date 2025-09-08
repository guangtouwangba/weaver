"""
Memory topic repository implementation.

Implements the TopicRepository interface using in-memory storage.
"""

from typing import List, Optional, Dict
import asyncio
from datetime import datetime

from ...core.entities.topic import Topic, TopicStatus
from ...core.repositories.topic_repository import TopicRepository


class MemoryTopicRepository(TopicRepository):
    """In-memory implementation of TopicRepository."""
    
    def __init__(self):
        self._topics: Dict[int, Topic] = {}
        self._next_id = 1
        self._lock = asyncio.Lock()
    
    async def save(self, topic: Topic) -> None:
        """Save a topic."""
        async with self._lock:
            if topic.id == 0:
                # Assign new ID for new topics
                topic.id = self._next_id
                self._next_id += 1
            
            # Create a copy to avoid external modifications
            topic_copy = Topic(
                id=topic.id,
                name=topic.name,
                description=topic.description,
                category=topic.category,
                status=topic.status,
                total_resources=topic.total_resources,
                total_conversations=topic.total_conversations,
                core_concepts_discovered=topic.core_concepts_discovered,
                concept_relationships=topic.concept_relationships,
                missing_materials_count=topic.missing_materials_count,
                user_id=topic.user_id,
                conversation_id=topic.conversation_id,
                parent_topic_id=topic.parent_topic_id,
                settings=topic.settings.copy() if topic.settings else {},
                created_at=topic.created_at,
                updated_at=datetime.utcnow()
            )
            self._topics[topic.id] = topic_copy
    
    async def get_by_id(self, topic_id: int) -> Optional[Topic]:
        """Get topic by ID."""
        async with self._lock:
            topic = self._topics.get(topic_id)
            if topic:
                return self._copy_topic(topic)
            return None
    
    async def get_by_name(self, name: str) -> Optional[Topic]:
        """Get topic by name."""
        async with self._lock:
            for topic in self._topics.values():
                if topic.name == name:
                    return self._copy_topic(topic)
            return None
    
    async def list_by_status(self, status: TopicStatus, limit: int = 100) -> List[Topic]:
        """List topics by status."""
        async with self._lock:
            results = []
            for topic in self._topics.values():
                if topic.status == status:
                    results.append(self._copy_topic(topic))
                    if len(results) >= limit:
                        break
            return results
    
    async def list_by_user_id(self, user_id: int, limit: int = 100) -> List[Topic]:
        """List topics by user ID."""
        async with self._lock:
            results = []
            for topic in self._topics.values():
                if topic.user_id == user_id:
                    results.append(self._copy_topic(topic))
                    if len(results) >= limit:
                        break
            return results
    
    async def list_by_parent_topic_id(self, parent_topic_id: int) -> List[Topic]:
        """List child topics by parent topic ID."""
        async with self._lock:
            results = []
            for topic in self._topics.values():
                if topic.parent_topic_id == parent_topic_id:
                    results.append(self._copy_topic(topic))
            return results
    
    async def search_by_name(self, name_pattern: str, limit: int = 10) -> List[Topic]:
        """Search topics by name pattern."""
        async with self._lock:
            results = []
            pattern_lower = name_pattern.lower()
            
            for topic in self._topics.values():
                if pattern_lower in topic.name.lower():
                    results.append(self._copy_topic(topic))
                    if len(results) >= limit:
                        break
            return results
    
    async def search_by_category(self, category: str, limit: int = 10) -> List[Topic]:
        """Search topics by category."""
        async with self._lock:
            results = []
            for topic in self._topics.values():
                if topic.category and topic.category.lower() == category.lower():
                    results.append(self._copy_topic(topic))
                    if len(results) >= limit:
                        break
            return results
    
    async def update_status(self, topic_id: int, status: TopicStatus) -> bool:
        """Update topic status."""
        async with self._lock:
            topic = self._topics.get(topic_id)
            if topic:
                topic.status = status
                topic.updated_at = datetime.utcnow()
                return True
            return False
    
    async def update_statistics(
        self, 
        topic_id: int, 
        total_resources: Optional[int] = None,
        total_conversations: Optional[int] = None,
        core_concepts_discovered: Optional[int] = None,
        concept_relationships: Optional[int] = None,
        missing_materials_count: Optional[int] = None
    ) -> bool:
        """Update topic statistics."""
        async with self._lock:
            topic = self._topics.get(topic_id)
            if topic:
                if total_resources is not None:
                    topic.total_resources = total_resources
                if total_conversations is not None:
                    topic.total_conversations = total_conversations
                if core_concepts_discovered is not None:
                    topic.core_concepts_discovered = core_concepts_discovered
                if concept_relationships is not None:
                    topic.concept_relationships = concept_relationships
                if missing_materials_count is not None:
                    topic.missing_materials_count = missing_materials_count
                
                topic.updated_at = datetime.utcnow()
                return True
            return False
    
    async def delete(self, topic_id: int) -> bool:
        """Delete a topic."""
        async with self._lock:
            if topic_id in self._topics:
                del self._topics[topic_id]
                return True
            return False
    
    async def count_by_status(self, status: TopicStatus) -> int:
        """Count topics by status."""
        async with self._lock:
            count = 0
            for topic in self._topics.values():
                if topic.status == status:
                    count += 1
            return count
    
    async def get_active_topics(self, limit: int = 100) -> List[Topic]:
        """Get all active topics."""
        return await self.list_by_status(TopicStatus.ACTIVE, limit)
    
    def _copy_topic(self, topic: Topic) -> Topic:
        """Create a copy of a topic."""
        return Topic(
            id=topic.id,
            name=topic.name,
            description=topic.description,
            category=topic.category,
            status=topic.status,
            total_resources=topic.total_resources,
            total_conversations=topic.total_conversations,
            core_concepts_discovered=topic.core_concepts_discovered,
            concept_relationships=topic.concept_relationships,
            missing_materials_count=topic.missing_materials_count,
            user_id=topic.user_id,
            conversation_id=topic.conversation_id,
            parent_topic_id=topic.parent_topic_id,
            settings=topic.settings.copy() if topic.settings else {},
            created_at=topic.created_at,
            updated_at=topic.updated_at
        )
    
    # Utility methods for testing/debugging
    async def clear_all(self) -> None:
        """Clear all topics (for testing)."""
        async with self._lock:
            self._topics.clear()
            self._next_id = 1
    
    async def get_all_topics(self) -> List[Topic]:
        """Get all topics (for testing/debugging)."""
        async with self._lock:
            return [self._copy_topic(topic) for topic in self._topics.values()]