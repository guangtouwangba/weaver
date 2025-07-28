"""
Embedding model abstraction layer with multi-provider support
"""
from .base import BaseEmbeddingModel, EmbeddingModelFactory
from .openai_embedding import OpenAIEmbedding
from .deepseek_embedding import DeepSeekEmbedding
from .anthropic_embedding import AnthropicEmbedding
from .huggingface_embedding import HuggingFaceEmbedding

__all__ = [
    'BaseEmbeddingModel',
    'EmbeddingModelFactory',
    'OpenAIEmbedding',
    'DeepSeekEmbedding', 
    'AnthropicEmbedding',
    'HuggingFaceEmbedding'
]