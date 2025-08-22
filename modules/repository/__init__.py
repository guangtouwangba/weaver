"""
Repository模块

提供数据访问层的抽象接口和具体实现。
遵循Repository模式，将数据访问逻辑与Business logic分离。
"""

from .base_repository import BaseRepository
from .document_repository import DocumentRepository
from .file_repository import FileRepository
from .interfaces import IBaseRepository, IDocumentRepository, IFileRepository, ITopicRepository
from .topic_repository import TopicRepository

__all__ = [
    # 接口
    "IBaseRepository",
    "ITopicRepository",
    "IFileRepository",
    "IDocumentRepository",
    # 实现
    "BaseRepository",
    "TopicRepository",
    "FileRepository",
    "DocumentRepository",
]
