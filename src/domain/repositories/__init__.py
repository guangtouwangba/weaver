"""Domain repository interfaces."""

from .document_repository import DocumentRepository
from .topic_repository import TopicRepository
from .knowledge_repository import KnowledgeRepository

__all__ = [
    "DocumentRepository",
    "TopicRepository",
    "KnowledgeRepository"
]
