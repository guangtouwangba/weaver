"""Search and QA service helpers."""

from typing import List

from fastapi import HTTPException
from langchain.vectorstores.base import VectorStoreRetriever
from pydantic import BaseModel, Field

from rag_core.graphs.state import QueryState


class SearchRequest(BaseModel):
    """Payload for semantic search."""

    query: str = Field(..., description="User question or keywords")
    top_k: int = Field(4, description="Number of relevant chunks to return")


class SearchHit(BaseModel):
    """Representation of a retrieved document chunk."""

    content: str
    score: float | None = None
    metadata: dict | None = None


class SearchResponse(BaseModel):
    """Search API response."""

    query: str
    hits: List[SearchHit]


class QARequest(BaseModel):
    """Input to QA endpoint."""

    question: str
    top_k: int = 4


class QAResponse(BaseModel):
    """QA endpoint response."""

    question: str
    answer: str
    sources: List[SearchHit]


async def perform_search(
    request: SearchRequest,
    retriever: VectorStoreRetriever,
) -> SearchResponse:
    """Execute retrieval and shape the JSON response."""
    docs = retriever.get_relevant_documents(request.query)
    hits = [
        SearchHit(
            content=doc.page_content,
            score=doc.metadata.get("score") if doc.metadata else None,
            metadata=doc.metadata,
        )
        for doc in docs
    ]
    return SearchResponse(query=request.query, hits=hits)


async def run_qa_graph(request: QARequest) -> QAResponse:
    """Placeholder to ensure router import works before LangGraph hookup."""
    raise HTTPException(status_code=501, detail="QA graph execution not wired yet")


async def perform_search_for_qa(request: QARequest, retriever: VectorStoreRetriever) -> QueryState:
    """Prepare QueryState for downstream LangGraph invocation."""
    docs = retriever.get_relevant_documents(request.question)
    formatted = [doc.dict() for doc in docs]
    return QueryState(question=request.question, retriever_top_k=request.top_k, documents=formatted)
