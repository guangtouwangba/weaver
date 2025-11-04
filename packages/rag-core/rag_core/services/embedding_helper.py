"""Helper functions for generating embeddings."""

from typing import List

from rag_core.chains.embeddings import build_embedding_function
from shared_config.settings import AppSettings


async def generate_text_embedding(text: str) -> List[float]:
    """
    Generate embedding vector for a text string.
    
    Args:
        text: Input text to embed
        
    Returns:
        Embedding vector as list of floats
    """
    settings = AppSettings()  # type: ignore[arg-type]
    embedding_fn = build_embedding_function(settings)
    
    # Use embed_query for single text
    embedding = await embedding_fn.aembed_query(text)
    
    return embedding


def embedding_to_pgvector_string(embedding: List[float]) -> str:
    """
    Convert embedding list to PostgreSQL vector string format.
    
    Args:
        embedding: List of float numbers
        
    Returns:
        String in format '[0.1, 0.2, 0.3, ...]'
    """
    return '[' + ','.join(map(str, embedding)) + ']'

