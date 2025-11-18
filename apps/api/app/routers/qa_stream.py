"""Streaming question answering endpoint."""

import json
import asyncio
import uuid
from typing import AsyncGenerator
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from rag_core.graphs.state import QueryState
from rag_core.pipeline.services.qa_service import QARequest
from rag_core.chains.llm import build_llm
from rag_core.chains.vectorstore import retrieve_documents, get_vector_store
from rag_core.chains.embeddings import build_embedding_function
from rag_core.services.message_service import MessageService
from rag_core.storage.database import SessionLocal
from shared_config.settings import AppSettings

router = APIRouter(prefix="/qa", tags=["qa"])


async def generate_streaming_response(request: QARequest, app_request: Request = None) -> AsyncGenerator[str, None]:
    """Generate SSE stream for QA response."""
    
    try:
        # Generate a unique query ID for this request
        query_id = str(uuid.uuid4())
        
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
        
        # 2. Load memories (short-term + long-term)
        short_term_memory = []  # Recent conversation history
        long_term_memory = []  # Similar historical messages
        
        if request.conversation_id or request.topic_id:
            yield f"data: {json.dumps({'type': 'progress', 'message': '加载对话历史...', 'stage': 'memory'})}\n\n"
            await asyncio.sleep(0.01)
            
            try:
                # Load settings
                settings = AppSettings()  # type: ignore[arg-type]
                memory_config = settings.memory
                
                # Get database session
                db = SessionLocal()
                try:
                    # 2a. Load short-term memory (recent messages in current conversation)
                    if request.conversation_id:
                        recent_messages = await asyncio.get_event_loop().run_in_executor(
                            None,
                            lambda: MessageService.get_recent_messages(
                                db,
                                conversation_id=request.conversation_id,
                                limit=5  # Last 5 messages
                            )
                        )
                        
                        # Build short-term memory
                        for msg in recent_messages:
                            short_term_memory.append({
                                "role": msg.role,
                                "content": msg.content
                            })
                        
                        if short_term_memory:
                            print(f"📝 [Short-term Memory] 加载了 {len(short_term_memory)} 条最近消息")
                    
                    # 2b. Load long-term memory (similar historical conversations)
                    # Generate embedding for similarity search
                    embedding_fn = build_embedding_function(settings)
                    query_embedding = await embedding_fn.aembed_query(request.question)
                    
                    # Search within conversation for similar messages (if enabled)
                    if request.conversation_id and memory_config.enable_conversation_memory:
                        conversation_messages = await asyncio.get_event_loop().run_in_executor(
                            None,
                            lambda: MessageService.find_similar_messages(
                                db,
                                conversation_id=request.conversation_id,
                                query_embedding=query_embedding,
                                limit=memory_config.conversation_memory_limit,
                                similarity_threshold=memory_config.conversation_similarity_threshold
                            )
                        )
                        for msg in conversation_messages:
                            # Avoid duplicating recent messages already in short-term memory
                            is_recent = any(
                                stm["content"] == msg.content 
                                for stm in short_term_memory
                            )
                            if not is_recent:
                                long_term_memory.append({
                                    "role": msg.role,
                                    "content": msg.content[:200],  # Truncate
                                    "source": "same_conversation"
                                })
                    
                    # Then search across topic (if enabled)
                    if request.topic_id and memory_config.enable_topic_memory:
                        topic_messages = await asyncio.get_event_loop().run_in_executor(
                            None,
                            lambda: MessageService.find_similar_messages_in_topic(
                                db,
                                topic_id=request.topic_id,
                                query_embedding=query_embedding,
                                limit=memory_config.topic_memory_limit,
                                similarity_threshold=memory_config.topic_similarity_threshold,
                                exclude_conversation_id=request.conversation_id
                            )
                        )
                        for msg in topic_messages:
                            long_term_memory.append({
                                "role": msg.role,
                                "content": msg.content[:200],  # Truncate
                                "source": "other_conversations"
                            })
                    
                    # Limit to configured maximum
                    if len(long_term_memory) > memory_config.max_total_memories:
                        long_term_memory = long_term_memory[:memory_config.max_total_memories]
                    
                    if long_term_memory:
                        print(f"🔍 [Long-term Memory] 检索到 {len(long_term_memory)} 条相似历史")
                finally:
                    db.close()
            except Exception as e:
                print(f"⚠️ [Streaming] 历史检索失败: {e}")
                import traceback
                traceback.print_exc()
                short_term_memory = []
                long_term_memory = []
        
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
        
        # Build context from documents
        context = "\n".join(doc.get("page_content", "") for doc in documents)
        
        # Check if we have any information to answer the question
        has_memory = bool(short_term_memory or long_term_memory)
        has_documents = bool(context)
        
        if not has_documents and not has_memory:
            # No information at all
            yield f"data: {json.dumps({'type': 'answer_chunk', 'chunk': '抱歉，没有找到相关信息来回答您的问题。'})}\n\n"
            yield f"data: {json.dumps({'type': 'done', 'conversation_id': request.conversation_id})}\n\n"
            return
        
        # Build LLM
        settings = AppSettings()  # type: ignore[arg-type]
        llm = build_llm(settings)
        
        # Prepare system prompt with intelligent information prioritization
        system_template = (
            "You are a helpful AI assistant with access to multiple information sources. "
            "Follow these rules:\n"
            "1. For questions ABOUT the conversation itself (e.g., '我的第一个问题是什么', 'what did I just ask'), "
            "   use ONLY the 【当前对话历史】 section to answer.\n"
            "2. For questions REQUIRING knowledge from documents, use 【参考文档】.\n"
            "3. Combine information from all sources when relevant.\n"
            "4. CRITICAL: Always respond in the SAME LANGUAGE as the user's question. "
            "If question is in Chinese, answer in Chinese. If English, answer in English."
        )
        
        # Build prompt with memory and context
        prompt_parts = [system_template, ""]
        
        # Add short-term memory (recent conversation) if available
        if short_term_memory:
            prompt_parts.append("【当前对话历史】")
            for memory in short_term_memory:
                role_label = "用户" if memory["role"] == "user" else "助手"
                prompt_parts.append(f"{role_label}: {memory['content']}")
            prompt_parts.append("")
        
        # Add long-term memory (similar historical conversations) if available
        if long_term_memory:
            prompt_parts.append("【相关历史参考】")
            for idx, memory in enumerate(long_term_memory, 1):
                source_label = "本对话早期" if memory.get("source") == "same_conversation" else "相关讨论"
                prompt_parts.append(f"[{source_label}]: {memory['content']}")
            prompt_parts.append("")
        
        # Add current documents if available
        if has_documents:
            prompt_parts.append("【参考文档】")
            prompt_parts.append(f"---\n{context}\n---")
            prompt_parts.append("")
        
        # Add question
        prompt_parts.append(f"User Question: {request.question}")
        prompt_parts.append("")
        prompt_parts.append("Answer:")
        
        prompt_text = "\n".join(prompt_parts)
        
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
        
        # 5. Runtime Evaluation (if enabled)
        if app_request and hasattr(app_request.app.state, 'rag'):
            runtime_evaluator = app_request.app.state.rag.runtime_evaluator
            if runtime_evaluator:
                try:
                    # Extract contexts from documents
                    contexts = [doc.get("page_content", "") for doc in documents]
                    
                    print(f"📊 [Evaluation] Recording query: {query_id[:8]}... (question_len={len(request.question)}, contexts={len(contexts)})")
                    
                    # Record query for evaluation (async, non-blocking)
                    asyncio.create_task(
                        runtime_evaluator.record_query(
                            query_id=query_id,
                            question=request.question,
                            answer=full_answer,
                            contexts=contexts,
                            metadata={
                                "conversation_id": request.conversation_id,
                                "topic_id": request.topic_id,
                                "num_documents": len(documents),
                                "has_memory": has_memory,
                            }
                        )
                    )
                    
                except Exception as eval_error:
                    # Don't fail the request if evaluation fails
                    print(f"⚠️ [Runtime Evaluation] Failed to record query: {eval_error}")
                    import traceback
                    traceback.print_exc()
        
        # 6. Save to memory (async in background, don't wait)
        # This will be handled by the complete graph later
        
        # Send completion
        yield f"data: {json.dumps({'type': 'done', 'conversation_id': request.conversation_id or 'new'})}\n\n"
        
    except Exception as e:
        error_msg = str(e)
        yield f"data: {json.dumps({'type': 'error', 'message': f'处理出错: {error_msg}'})}\n\n"


@router.post("/stream", summary="Streaming question answering")
async def answer_question_stream(request: QARequest, app_request: Request):
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
        generate_streaming_response(request, app_request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )

