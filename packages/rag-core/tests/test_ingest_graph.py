"""Basic smoke tests for ingest graph components."""

import pytest

from rag_core.graphs.ingest_graph import run_ingest_graph
from rag_core.pipeline.services.ingest_service import IngestPayload


@pytest.mark.asyncio
async def test_run_ingest_graph_noop(monkeypatch):
    """Test ingest graph with fake embeddings to avoid API calls."""
    # Use fake provider to avoid real API calls
    monkeypatch.setenv("EMBEDDING_PROVIDER", "fake")
    
    state = IngestPayload(document_id="doc-1", content="hello", metadata={})
    await run_ingest_graph(state)
