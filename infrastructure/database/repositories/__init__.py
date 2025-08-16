"""
Database repositories implementation.

This module provides concrete implementations of repository interfaces
using SQLAlchemy. All repositories follow the same patterns:
- Base repository with common CRUD operations
- Domain-specific repositories extending the base
- Proper error handling and transaction management
"""

from .base import BaseRepository
from .topic import TopicRepository, TagRepository, TopicResourceRepository, ConversationRepository
from .document import DocumentRepository, QueryHistoryRepository

__all__ = [
    "BaseRepository",
    "TopicRepository", "TagRepository", "TopicResourceRepository", "ConversationRepository",
    "DocumentRepository", "QueryHistoryRepository",
]