"""
模块化API

提供简单、统一的API接口来访问所有模块功能。
"""

from .implementation import RagAPI
from .interface import IModularAPI, APIError

__all__ = [
    'RagAPI',
    'IModularAPI',
    'APIError'
]
