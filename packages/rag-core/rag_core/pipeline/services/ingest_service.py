"""Helpers for preparing ingest payloads."""

import tempfile
import uuid
from pathlib import Path

from fastapi import UploadFile
from pydantic import BaseModel

from rag_core.chains.loaders import load_document_content
from rag_core.graphs.state import DocumentIngestState


class IngestPayload(DocumentIngestState):
    """Concrete payload passed into the ingest graph."""


class IngestResult(BaseModel):
    """Return message for ingest endpoint."""

    status: str
    document_id: str


async def build_ingest_payload(file: UploadFile) -> IngestPayload:
    """Persist upload to temp storage and build ingest payload."""
    if not file.filename:
        raise ValueError("file must include a filename")

    suffix = Path(file.filename).suffix or ".txt"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        contents = await file.read()
        temp_file.write(contents)
        temp_path = Path(temp_file.name)

    text = load_document_content(temp_path)
    temp_path.unlink(missing_ok=True)

    document_id = str(uuid.uuid4())
    metadata = {"filename": file.filename}
    return IngestPayload(document_id=document_id, content=text, metadata=metadata)
