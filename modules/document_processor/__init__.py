"""
文档处理模块

负责对文档进行各种处理操作，如分块、清理、转换等。
提供灵活的处理策略和可配置的参数。
"""

from .interface import IDocumentProcessor, DocumentProcessorError
from .text_processor import TextProcessor
from .chunking_processor import ChunkingProcessor

__all__ = [
    "IDocumentProcessor",
    "DocumentProcessorError",
    "TextProcessor", 
    "ChunkingProcessor",
]