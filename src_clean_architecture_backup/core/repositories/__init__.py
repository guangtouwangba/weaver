"""
Core repository interfaces module.

This module contains abstract repository interfaces that define
the contracts for data access operations.
"""

from .document_repository import DocumentRepository
from .topic_repository import TopicRepository
from .chat_repository import ChatRepository
from .file_repository import FileRepository

__all__ = [
    "DocumentRepository",
    "TopicRepository", 
    "ChatRepository",
    "FileRepository"
]