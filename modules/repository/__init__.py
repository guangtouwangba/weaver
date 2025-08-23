"""
Repository模块

提供数据访问层的抽象接口和具体实现。
遵循Repository模式，将数据访问逻辑与Business logic分离。
"""

from modules.repository.base_repository import BaseRepository
from modules.repository.document_repository import DocumentRepository
from modules.repository.file_repository import FileRepository
from modules.repository.interfaces import (
    IBaseRepository,
    IDocumentRepository,
    IFileRepository,
    ITopicRepository,
)
from modules.repository.topic_repository import TopicRepository

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
