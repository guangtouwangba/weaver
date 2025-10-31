"""Semantic search endpoints."""

from fastapi import APIRouter, Depends

from app.dependencies import get_vector_retriever
from rag_core.pipeline.services.qa_service import SearchRequest, SearchResponse, perform_search

router = APIRouter(prefix="/search", tags=["search"])


@router.post("/", response_model=SearchResponse, summary="Semantic search")
async def search_documents(
    request: SearchRequest,
    retriever=Depends(get_vector_retriever),
) -> SearchResponse:
    """Execute semantic search against the vector store retriever."""
    if retriever is None:
        # No documents have been indexed yet
        return SearchResponse(query=request.query, results=[], total=0)
    return await perform_search(request=request, retriever=retriever)
