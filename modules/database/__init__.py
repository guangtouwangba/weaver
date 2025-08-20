"""
数据库模块

提供简单、直接的数据库交互功能，支持RAG系统的数据持久化需求。
"""

from .connection import DatabaseConnection, get_session
from .models import Topic, File, Document, DocumentChunk
from .repositories import TopicRepository, FileRepository, DocumentRepository
from .service import DatabaseService

__all__ = [
    'DatabaseConnection',
    'get_session',
    'Topic',
    'File', 
    'Document',
    'DocumentChunk',
    'TopicRepository',
    'FileRepository',
    'DocumentRepository',
    'DatabaseService'
]
