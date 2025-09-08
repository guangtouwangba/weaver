"""
Core value objects module.

This module contains value objects that represent immutable data structures
used throughout the system.
"""

from .chat_message import ChatMessage, MessageRole
from .document_chunk import DocumentChunk

__all__ = [
    "ChatMessage",
    "MessageRole",
    "DocumentChunk"
]