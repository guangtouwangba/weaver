"""
Vector database abstraction layer with multi-provider support
"""
from .base import BaseVectorDB, VectorDBFactory
from .chroma_db import ChromaVectorDB
try:
    from .pinecone_db import PineconeVectorDB
except ImportError as e:
    # Pinecone dependency not available or misconfigured
    PineconeVectorDB = None
from .weaviate_db import WeaviateVectorDB
from .qdrant_db import QdrantVectorDB

__all__ = [
    'BaseVectorDB',
    'VectorDBFactory', 
    'ChromaVectorDB',
    'PineconeVectorDB',
    'WeaviateVectorDB',
    'QdrantVectorDB'
]