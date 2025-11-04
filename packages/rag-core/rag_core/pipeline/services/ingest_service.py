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

    print(f"💼 构建 Ingest Payload...")
    print(f"  ├─ 保存临时文件...")
    
    suffix = Path(file.filename).suffix or ".txt"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        contents = await file.read()
        temp_file.write(contents)
        temp_path = Path(temp_file.name)
    
    print(f"  ✓ 临时文件已保存: {temp_path}")
    print(f"  ├─ 加载文档内容...")

    text = load_document_content(temp_path)
    temp_path.unlink(missing_ok=True)
    
    print(f"  ✓ 临时文件已清理")
    print(f"  ├─ 内容长度: {len(text)} 字符")

    document_id = str(uuid.uuid4())
    metadata = {
        "document_id": document_id,  # 添加document_id到metadata，用于过滤
        "filename": file.filename,
        "source": file.filename,  # 添加source字段用于前端显示来源
    }
    
    print(f"  ✓ 生成 Document ID: {document_id}")
    
    return IngestPayload(document_id=document_id, content=text, metadata=metadata)
