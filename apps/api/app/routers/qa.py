"""Question answering endpoints."""

from fastapi import APIRouter

from rag_core.graphs.qa_graph import run_qa_graph
from rag_core.pipeline.services.qa_service import QARequest, QAResponse

router = APIRouter(prefix="/qa", tags=["qa"])


@router.post("/", response_model=QAResponse, summary="Question answering")
async def answer_question(request: QARequest) -> QAResponse:
    """Invoke the LangGraph QA pipeline and return the synthesized answer."""
    return await run_qa_graph(request)
