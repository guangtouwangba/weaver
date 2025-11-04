"""Question answering endpoints."""

from fastapi import APIRouter

from rag_core.graphs.qa_graph import run_qa_graph
from rag_core.graphs.state import QueryState
from rag_core.pipeline.services.qa_service import QARequest, QAResponse, SearchHit

router = APIRouter(prefix="/qa", tags=["qa"])


@router.post("/", response_model=QAResponse, summary="Question answering")
async def answer_question(request: QARequest) -> QAResponse:
    """Invoke the LangGraph QA pipeline and return the synthesized answer."""
    print("=" * 80)
    print(f"💬 收到问答请求")
    print(f"  ├─ 问题: {request.question}")
    print(f"  ├─ Top-K: {request.top_k}")
    if request.document_ids:
        print(f"  └─ 文档过滤: {len(request.document_ids)} 个文档")
        for doc_id in request.document_ids:
            print(f"      - {doc_id}")
    else:
        print(f"  └─ 范围: 所有文档")
    
    # Convert QARequest to QueryState
    state = QueryState(
        question=request.question,
        retriever_top_k=request.top_k,
        document_ids=request.document_ids,
        conversation_id=request.conversation_id,
        topic_id=request.topic_id,
        documents=[],
        answer=""
    )
    
    # Run the QA graph (returns dict, not QueryState)
    result_state = await run_qa_graph(state)
    
    # Convert documents to SearchHit format
    documents = result_state.get("documents", [])
    sources = [
        SearchHit(
            content=doc.get("page_content", ""),
            score=doc.get("score"),
            metadata=doc.get("metadata")
        )
        for doc in documents
    ]
    
    answer = result_state.get("answer", "")
    conversation_id = result_state.get("conversation_id")
    
    print(f"✅ 问答完成")
    print(f"  ├─ 检索到 {len(sources)} 个相关文档")
    print(f"  ├─ 答案长度: {len(answer)} 字符")
    if conversation_id:
        print(f"  └─ 对话ID: {conversation_id}")
    print("=" * 80)
    
    return QAResponse(
        question=request.question,
        answer=answer,
        sources=sources,
        conversation_id=conversation_id
    )
