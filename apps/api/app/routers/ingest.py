"""Document ingest endpoints."""

from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile

from rag_core.graphs.ingest_graph import run_ingest_graph
from rag_core.pipeline.services.ingest_service import IngestResult, build_ingest_payload

router = APIRouter(prefix="/documents", tags=["ingest"])


@router.post("/", summary="Ingest a document")
async def ingest_document(
    file: UploadFile,
    background_tasks: BackgroundTasks,
) -> IngestResult:
    """Schedule ingestion of an uploaded file via LangGraph."""
    try:
        payload = await build_ingest_payload(file)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    background_tasks.add_task(run_ingest_graph, payload)
    return IngestResult(status="scheduled", document_id=payload.document_id)
