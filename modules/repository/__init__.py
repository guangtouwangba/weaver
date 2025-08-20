"""
Repository模块

提供数据访问层的抽象接口和具体实现。
遵循Repository模式，将数据访问逻辑与业务逻辑分离。
"""

from .interfaces import (
    IBaseRepository, ITopicRepository, IFileRepository, IDocumentRepository
)
from .base_repository import BaseRepository
from .topic_repository import TopicRepository
from .file_repository import FileRepository
from .document_repository import DocumentRepository

__all__ = [
    # 接口
    'IBaseRepository',
    'ITopicRepository', 
    'IFileRepository',
    'IDocumentRepository',
    
    # 实现
    'BaseRepository',
    'TopicRepository',
    'FileRepository', 
    'DocumentRepository'
]
