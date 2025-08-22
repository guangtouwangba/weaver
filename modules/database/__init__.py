"""
数据库模块

提供简单、直接的数据库交互功能，支持RAG系统的数据持久化需求。
"""

from .connection import (
    DatabaseConnection,
    get_database_connection,
    get_db_session,
    get_session,
)
from .models import Document, DocumentChunk, File, Topic

# DatabaseService removed to avoid circular imports

# Repository classes removed to avoid circular imports
# Use: from modules.repository import TopicRepository

__all__ = [
    "DatabaseConnection",
    "get_session",
    "get_db_session",
    "get_database_connection",
    "Topic",
    "File",
    "Document",
    "DocumentChunk",
]
