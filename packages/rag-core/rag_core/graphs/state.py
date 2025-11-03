"""Graph state definitions shared across LangGraph DAGs."""

from typing import List, Optional

from pydantic import BaseModel


class DocumentIngestState(BaseModel):
    """State payload flowing through the ingest graph."""

    document_id: str
    content: str
    metadata: dict
    chunks: Optional[List[str]] = None
    embeddings: Optional[List[List[float]]] = None


class QueryState(BaseModel):
    """State payload for query and QA graphs."""

    question: str
    retriever_top_k: int
    document_ids: Optional[List[str]] = None  # Filter by specific document IDs
    documents: Optional[List[dict]] = None
    answer: Optional[str] = None
