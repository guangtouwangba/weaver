"""Document ingest endpoints."""

from typing import List

from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile
from pydantic import BaseModel

from rag_core.chains.vectorstore import get_vector_store
from rag_core.graphs.ingest_graph import run_ingest_graph
from rag_core.pipeline.services.ingest_service import IngestResult, build_ingest_payload

router = APIRouter(prefix="/documents", tags=["ingest"])


class DocumentInfo(BaseModel):
    """Information about an ingested document."""
    document_id: str
    filename: str
    chunk_count: int


class ListDocumentsResponse(BaseModel):
    """Response for listing documents."""
    total: int
    documents: List[DocumentInfo]


@router.post("/", summary="Ingest a document")
async def ingest_document(
    file: UploadFile,
    background_tasks: BackgroundTasks,
) -> IngestResult:
    """Schedule ingestion of an uploaded file via LangGraph."""
    print("=" * 80)
    print(f"📥 收到文档上传请求")
    print(f"  ├─ 文件名: {file.filename}")
    print(f"  ├─ Content-Type: {file.content_type}")
    print(f"  └─ 开始构建 Payload...")
    
    try:
        payload = await build_ingest_payload(file)
        print(f"✅ Payload 构建成功")
        print(f"  ├─ Document ID: {payload.document_id}")
        print(f"  └─ 内容长度: {len(payload.content)} 字符")
    except ValueError as exc:
        print(f"❌ Payload 构建失败: {str(exc)}")
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    print(f"⏰ 文档已加入后台处理队列")
    print("=" * 80)
    background_tasks.add_task(run_ingest_graph, payload)
    return IngestResult(status="scheduled", document_id=payload.document_id)


@router.get("/", response_model=ListDocumentsResponse, summary="List all documents")
async def list_documents() -> ListDocumentsResponse:
    """List all ingested documents with their metadata."""
    vector_store = get_vector_store()
    
    if vector_store is None:
        return ListDocumentsResponse(total=0, documents=[])
    
    # Get all documents from the vector store
    # FAISS doesn't have a direct "list all" API, so we need to access the docstore
    try:
        docstore = vector_store.docstore
        all_docs = list(docstore._dict.values()) if hasattr(docstore, '_dict') else []
        
        # Group by document_id
        doc_groups = {}
        for doc in all_docs:
            if hasattr(doc, 'metadata') and doc.metadata:
                doc_id = doc.metadata.get('document_id')
                filename = doc.metadata.get('filename', 'Unknown')
                
                if doc_id:
                    if doc_id not in doc_groups:
                        doc_groups[doc_id] = {
                            'document_id': doc_id,
                            'filename': filename,
                            'chunk_count': 0
                        }
                    doc_groups[doc_id]['chunk_count'] += 1
        
        documents = [
            DocumentInfo(**info) for info in doc_groups.values()
        ]
        
        print(f"📋 列出文档: 共 {len(documents)} 个文档, {len(all_docs)} 个chunks")
        
        return ListDocumentsResponse(
            total=len(documents),
            documents=sorted(documents, key=lambda x: x.filename)
        )
        
    except Exception as e:
        print(f"❌ 列出文档失败: {e}")
        return ListDocumentsResponse(total=0, documents=[])
