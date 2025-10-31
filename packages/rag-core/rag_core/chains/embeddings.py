"""Embedding helpers."""

from typing import Callable, List

from langchain.embeddings.base import Embeddings
from langchain_community.embeddings import FakeEmbeddings

from rag_core.graphs.state import DocumentIngestState


def build_embedding_function(settings=None) -> Embeddings:
    """Return an embeddings implementation (fake by default for local dev)."""
    return FakeEmbeddings(size=768)


async def embed_chunks(state: DocumentIngestState) -> DocumentIngestState:
    """Generate embeddings for text chunks."""
    if not state.chunks:
        raise ValueError("split step must run before embedding")
    embeddings_model = build_embedding_function()
    embeddings: List[List[float]] = embeddings_model.embed_documents(state.chunks)
    return state.copy(update={"embeddings": embeddings})
