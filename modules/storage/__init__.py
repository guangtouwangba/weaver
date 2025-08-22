"""
存储模块

提供文件存储和签名URL功能，支持多种存储后端。
"""

from .base import IStorage, StorageError
from .local_storage import LocalStorage
from .minio_storage import MinIOStorage
from .mock_storage import MockStorage

__all__ = ["IStorage", "StorageError", "LocalStorage", "MockStorage", "MinIOStorage"]
