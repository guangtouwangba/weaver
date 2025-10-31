"""Smoke test for QA graph."""

import pytest

from rag_core.graphs.qa_graph import run_qa_graph
from rag_core.graphs.state import QueryState


@pytest.mark.asyncio
async def test_run_qa_graph_placeholder():
    state = QueryState(question="What is RAG?", retriever_top_k=2)
    result = await run_qa_graph(state)
    assert result.answer is not None
