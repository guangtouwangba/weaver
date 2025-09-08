"""
文档处理模块

负责对文档进行各种处理操作，如分块、清理、转换等。
提供灵活的处理策略和可配置的参数。
"""

from modules.processors.base import DocumentProcessorError, IDocumentProcessor
from modules.processors.enhanced_chunking_processor import EnhancedChunkingProcessor
from modules.processors.text_processor import TextProcessor

__all__ = [
    "IDocumentProcessor",
    "DocumentProcessorError",
    "TextProcessor",
    "EnhancedChunkingProcessor",  # 统一的分块处理器
]
