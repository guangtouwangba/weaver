"""
模块化API

提供简单、统一的API接口来访问所有模块功能。
"""

from .simple_api import SimpleAPI
from .interface import IModularAPI, APIError

__all__ = [
    'SimpleAPI',
    'IModularAPI',
    'APIError'
]
