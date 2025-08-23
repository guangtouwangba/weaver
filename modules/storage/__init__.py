"""
存储模块

提供文件存储和签名URL功能，支持多种存储后端。
"""

from modules.storage.base import IStorage, StorageError
from modules.storage.local_storage import LocalStorage
from modules.storage.minio_storage import MinIOStorage
from modules.storage.mock_storage import MockStorage

__all__ = ["IStorage", "StorageError", "LocalStorage", "MockStorage", "MinIOStorage"]
