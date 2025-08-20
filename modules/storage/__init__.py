"""
存储模块

提供文件存储和签名URL功能，支持多种存储后端。
"""

from .interface import IStorage, StorageError
from .local_storage import LocalStorage
from .mock_storage import MockStorage
from .minio_storage import MinIOStorage

__all__ = [
    'IStorage',
    'StorageError',
    'LocalStorage', 
    'MockStorage',
    'MinIOStorage'
]
