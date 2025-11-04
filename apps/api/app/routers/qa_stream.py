"""Streaming question answering endpoint."""

import json
import asyncio
from typing import AsyncGenerator
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from rag_core.graphs.state import QueryState
from rag_core.pipeline.services.qa_service import QARequest
from rag_core.chains.llm import build_llm
from rag_core.chains.vectorstore import retrieve_documents, get_vector_store
from shared_config.settings import AppSettings

router = APIRouter(prefix="/qa", tags=["qa"])


async def generate_streaming_response(request: QARequest) -> AsyncGenerator[str, None]:
    """Generate SSE stream for QA response."""
    
    try:
        # 1. Build initial state
        state = QueryState(
            question=request.question,
            retriever_top_k=request.top_k,
            document_ids=request.document_ids,
            conversation_id=request.conversation_id,
            topic_id=request.topic_id,
            documents=[],
            answer=""
        )
        
        # Send progress: starting
        yield f"data: {json.dumps({'type': 'progress', 'message': '开始处理...', 'stage': 'init'})}\n\n"
        await asyncio.sleep(0.01)  # Allow client to receive
        
        # 2. Load memories (if needed)
        if request.conversation_id:
            yield f"data: {json.dumps({'type': 'progress', 'message': '加载对话历史...', 'stage': 'memory'})}\n\n"
            # Note: These are sync functions, run in executor if needed
            # For now, skip to keep streaming smooth
        
        # 3. Retrieve documents
        yield f"data: {json.dumps({'type': 'progress', 'message': '检索相关文档...', 'stage': 'retrieval'})}\n\n"
        await asyncio.sleep(0.01)
        
        # Ensure vector store is loaded
        vector_store = get_vector_store()
        
        # Retrieve documents using async method
        documents = []
        if vector_store is not None:
            from rag_core.retrievers.vector_retriever import VectorRetriever
            retriever = VectorRetriever(vector_store=vector_store, top_k=state.retriever_top_k)
            
            # Use async retrieve
            rag_documents = await retriever.retrieve(state.question, top_k=state.retriever_top_k)
            
            # Filter by document_ids if provided
            if state.document_ids:
                rag_documents = [
                    doc for doc in rag_documents
                    if doc.metadata.get("document_id") in state.document_ids
                ]
            
            # Convert to dict format
            documents = [doc.model_dump() for doc in rag_documents]
        
        # Prepare sources for streaming
        sources = [
            {
                "content": doc.get("page_content", ""),
                "score": doc.get("score"),
                "metadata": doc.get("metadata", {})
            }
            for doc in documents
        ]
        
        # Send sources
        yield f"data: {json.dumps({'type': 'sources', 'sources': sources, 'count': len(sources)})}\n\n"
        await asyncio.sleep(0.01)
        
        # 4. Generate answer with streaming
        yield f"data: {json.dumps({'type': 'progress', 'message': '生成回答...', 'stage': 'generation'})}\n\n"
        await asyncio.sleep(0.01)
        
        # Build context
        context = "\n".join(doc.get("page_content", "") for doc in documents)
        
        if not context:
            yield f"data: {json.dumps({'type': 'answer_chunk', 'chunk': '抱歉，没有找到相关文档来回答您的问题。'})}\n\n"
            yield f"data: {json.dumps({'type': 'done', 'conversation_id': request.conversation_id})}\n\n"
            return
        
        # Build LLM with streaming
        settings = AppSettings()  # type: ignore[arg-type]
        llm = build_llm(settings)
        
        # Prepare prompt
        system_template = (
            "You are a helpful RAG assistant. "
            "Answer based ONLY on the provided context. "
            "CRITICAL: Always respond in the SAME LANGUAGE as the user's question. "
            "If question is in Chinese, answer in Chinese. If English, answer in English."
        )
        
        prompt_text = (
            f"{system_template}\n\n"
            f"Context:\n---\n{context}\n---\n\n"
            f"User Question: {request.question}\n\n"
            f"Answer:"
        )
        
        # Generate answer (non-streaming, then simulate streaming)
        # Run LLM call in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        full_answer = await loop.run_in_executor(None, llm.invoke, prompt_text)
        
        # Ensure we have a string
        if not isinstance(full_answer, str):
            full_answer = str(full_answer)
        
        # Simulate streaming by sending in chunks for better UX
        chunk_size = 15  # Characters per chunk
        for i in range(0, len(full_answer), chunk_size):
            chunk = full_answer[i:i+chunk_size]
            yield f"data: {json.dumps({'type': 'answer_chunk', 'chunk': chunk})}\n\n"
            await asyncio.sleep(0.03)  # Simulate typing effect (30ms per chunk)
        
        # 5. Save to memory (async in background, don't wait)
        # This will be handled by the complete graph later
        
        # Send completion
        yield f"data: {json.dumps({'type': 'done', 'conversation_id': request.conversation_id or 'new'})}\n\n"
        
    except Exception as e:
        error_msg = str(e)
        yield f"data: {json.dumps({'type': 'error', 'message': f'处理出错: {error_msg}'})}\n\n"


@router.post("/stream", summary="Streaming question answering")
async def answer_question_stream(request: QARequest):
    """
    Stream the QA response using Server-Sent Events (SSE).
    
    The stream will send events in the following format:
    - type: 'progress' - Processing stage updates
    - type: 'sources' - Retrieved source documents
    - type: 'answer_chunk' - Streaming answer chunks
    - type: 'done' - Processing complete
    - type: 'error' - Error occurred
    """
    return StreamingResponse(
        generate_streaming_response(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )

