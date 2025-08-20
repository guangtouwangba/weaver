"""
文件加载模块

负责从各种来源加载文档内容。
提供统一的接口和多种加载策略。
"""

from .interface import IFileLoader, FileLoaderError
from .text_loader import TextFileLoader
from .multi_format_loader import MultiFormatFileLoader

__all__ = [
    "IFileLoader",
    "FileLoaderError", 
    "TextFileLoader",
    "MultiFormatFileLoader",
]