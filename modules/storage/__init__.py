"""
存储模块

提供文件存储和签名URL功能，支持多种存储后端。
"""

from .interface import IStorage, StorageError
from .local_storage import LocalStorage
from .mock_storage import MockStorage

__all__ = [
    'IStorage',
    'StorageError',
    'LocalStorage', 
    'MockStorage'
]
