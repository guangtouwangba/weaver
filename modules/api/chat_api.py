"""
Chat API - HTTP + SSE 混合接口设计

提供基于SSE的流式聊天体验和传统HTTP管理接口。
"""

import json
import asyncio
from datetime import datetime
from typing import AsyncGenerator, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from logging_system import get_logger, log_execution_time, log_errors
from modules.database import get_db_session
from modules.schemas import APIResponse
from modules.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ChatMessage,
    ChatSearchRequest,
    ChatSearchResponse,
    ChatStatisticsResponse,
    ConversationListRequest,
    ConversationListResponse,
    MessageHistoryRequest,
    MessageHistoryResponse,
    MessageRole,
    SSEEventType,
    SSEStartEvent,
    SSEProgressEvent,
    SSEContextEvent,
    SSEDeltaEvent,
    SSECompleteEvent,
    SSEErrorEvent
)
from modules.services.chat_service import ChatService, get_chat_service

router = APIRouter(prefix="/chat", tags=["Chat"])
logger = get_logger(__name__)


# ==================== SSE流式聊天接口 ====================

@router.post("/stream", summary="🌊 流式聊天接口 (SSE)")
@log_execution_time(threshold_ms=10000)
@log_errors()
async def chat_stream(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service),
):
    """
    # 🌊 流式聊天接口 (Server-Sent Events)
    
    提供实时的RAG聊天体验：
    - 实时显示RAG检索进度
    - 流式输出AI生成内容
    - 自动重连和错误恢复
    
    ## 事件流格式
    
    ### 开始事件
    ```
    event: start
    data: {"message_id": "msg-uuid", "conversation_id": "conv-uuid"}
    ```
    
    ### 进度事件
    ```
    event: progress
    data: {"stage": "retrieving", "message": "正在检索相关文档..."}
    ```
    
    ### 上下文事件
    ```
    event: context
    data: {"contexts": [...], "search_time_ms": 200, "total_results": 5}
    ```
    
    ### 增量内容事件
    ```
    event: delta
    data: {"content": "机器学习", "message_id": "msg-uuid"}
    ```
    
    ### 完成事件
    ```
    event: complete
    data: {"conversation_id": "conv-uuid", "total_tokens": 150, "generation_time_ms": 3000}
    ```
    
    ### 错误事件
    ```
    event: error
    data: {"error": "错误信息", "error_type": "ValueError", "stage": "retrieving"}
    ```
    
    ## 前端接入示例
    
    ```javascript
    const response = await fetch('/api/v1/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            message: "什么是机器学习？",
            topic_id: 123,
            conversation_id: "conv-uuid"  // 可选
        })
    });
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    
    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value);
        const lines = chunk.split('\\n');
        
        for (const line of lines) {
            if (line.startsWith('event:')) {
                eventType = line.substring(6).trim();
            } else if (line.startsWith('data:')) {
                const data = JSON.parse(line.substring(5));
                handleSSEEvent(eventType, data);
            }
        }
    }
    ```
    """
    
    async def generate_chat_stream() -> AsyncGenerator[str, None]:
        """生成SSE流数据"""
        try:
            await chat_service.initialize()
            
            # 生成唯一标识符
            import uuid
            message_id = str(uuid.uuid4())
            conversation_id = request.conversation_id or str(uuid.uuid4())
            
            # 1. 🚀 开始处理
            start_event = SSEStartEvent(
                message_id=message_id,
                conversation_id=conversation_id
            )
            yield f"event: {SSEEventType.START}\n"
            yield f"data: {start_event.model_dump_json()}\n\n"
            
            # 2. 🔍 RAG检索阶段
            progress_event = SSEProgressEvent(
                stage="retrieving",
                message="正在检索相关文档...",
                progress=0.2
            )
            yield f"event: {SSEEventType.PROGRESS}\n"
            yield f"data: {progress_event.model_dump_json()}\n\n"
            
            # 执行RAG检索
            retrieved_contexts, search_time_ms = await chat_service._retrieve_contexts(
                query=request.message,
                topic_id=request.topic_id,
                search_type=request.search_type,
                max_results=request.max_results,
                score_threshold=request.score_threshold
            )
            
            # 发送检索结果
            context_event = SSEContextEvent(
                contexts=retrieved_contexts,
                search_time_ms=search_time_ms,
                total_results=len(retrieved_contexts)
            )
            yield f"event: {SSEEventType.CONTEXT}\n"
            yield f"data: {context_event.model_dump_json()}\n\n"
            
            # 3. 🤖 AI生成阶段
            progress_event = SSEProgressEvent(
                stage="generating",
                message="AI正在生成回答...",
                progress=0.6
            )
            yield f"event: {SSEEventType.PROGRESS}\n"
            yield f"data: {progress_event.model_dump_json()}\n\n"
            
            # 获取对话历史
            conversation_history = []
            if request.context_window > 0:
                conversation_history = await chat_service.get_conversation_messages(
                    conversation_id, limit=request.context_window * 2
                )
            
            # 构建提示词
            prompt = chat_service._build_prompt(
                user_message=request.message,
                retrieved_contexts=retrieved_contexts if request.include_context else [],
                conversation_history=conversation_history
            )
            
            # 4. 🌊 流式生成AI回答
            full_response = ""
            tokens_used = 0
            generation_start = datetime.now()
            
            async for chunk in chat_service._generate_ai_response_stream(
                prompt=prompt,
                max_tokens=request.max_tokens,
                temperature=request.temperature
            ):
                if chunk.get("content"):
                    full_response += chunk["content"]
                    
                    # 发送增量内容
                    delta_event = SSEDeltaEvent(
                        content=chunk["content"],
                        message_id=message_id,
                        token_count=tokens_used
                    )
                    yield f"event: {SSEEventType.DELTA}\n"
                    yield f"data: {delta_event.model_dump_json()}\n\n"
                
                if chunk.get("tokens"):
                    tokens_used += chunk["tokens"]
            
            generation_time_ms = int((datetime.now() - generation_start).total_seconds() * 1000)
            
            # 5. 💾 保存对话
            progress_event = SSEProgressEvent(
                stage="saving",
                message="正在保存对话记录...",
                progress=0.9
            )
            yield f"event: {SSEEventType.PROGRESS}\n"
            yield f"data: {progress_event.model_dump_json()}\n\n"
            
            await chat_service.es_service.save_conversation(
                conversation_id=conversation_id,
                user_message=request.message,
                assistant_message=full_response,
                topic_id=request.topic_id,
                retrieved_contexts=retrieved_contexts,
                ai_metadata={
                    "model": "gpt-3.5-turbo",
                    "tokens_used": tokens_used,
                    "generation_time_ms": generation_time_ms,
                    "search_time_ms": search_time_ms,
                    "temperature": request.temperature,
                    "max_tokens": request.max_tokens
                }
            )
            
            # 6. ✅ 发送完成事件
            complete_event = SSECompleteEvent(
                conversation_id=conversation_id,
                message_id=message_id,
                total_tokens=tokens_used,
                generation_time_ms=generation_time_ms,
                search_time_ms=search_time_ms
            )
            yield f"event: {SSEEventType.COMPLETE}\n"
            yield f"data: {complete_event.model_dump_json()}\n\n"
            
        except Exception as e:
            logger.error(f"❌ 流式聊天处理失败: {e}")
            
            # 发送错误事件
            error_event = SSEErrorEvent(
                error=str(e),
                error_type=type(e).__name__,
                stage="unknown"
            )
            yield f"event: {SSEEventType.ERROR}\n"
            yield f"data: {error_event.model_dump_json()}\n\n"
        
        finally:
            # 确保资源被正确清理
            try:
                await chat_service.close()
                logger.info("ChatService资源已清理")
            except Exception as e:
                logger.error(f"清理ChatService资源时出错: {e}")
    
    return StreamingResponse(
        generate_chat_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control, Content-Type",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "X-Accel-Buffering": "no",  # 禁用nginx缓冲
        }
    )


# ==================== 传统HTTP接口 ====================

@router.post("/", response_model=APIResponse, summary="💬 传统聊天接口")
@log_execution_time(threshold_ms=15000)
@log_errors()
async def chat_sync(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service),
):
    """
    # 💬 传统聊天接口 (HTTP)
    
    适用于不需要流式体验的场景：
    - API集成
    - 批量处理
    - 简单客户端
    
    等待完整处理后返回所有结果。
    
    ## 响应格式
    ```json
    {
        "success": true,
        "data": {
            "message_id": "msg-uuid",
            "conversation_id": "conv-uuid", 
            "content": "AI回答内容",
            "retrieved_contexts": [...],
            "ai_metadata": {...},
            "timestamp": "2024-01-01T00:00:00Z"
        }
    }
    ```
    """
    try:
        response = await chat_service.chat(request)
        return APIResponse(success=True, data=response.model_dump())
    except Exception as e:
        logger.error(f"❌ 聊天处理失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 对话管理接口 ====================

@router.get("/conversations", response_model=APIResponse, summary="📋 获取对话列表")
@log_execution_time()
@log_errors()
async def get_conversations(
    topic_id: Optional[int] = Query(None, description="主题ID过滤"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    order_by: str = Query("last_message_time", description="排序字段"),
    order_direction: str = Query("desc", description="排序方向"),
    chat_service: ChatService = Depends(get_chat_service),
):
    """
    获取对话列表，支持分页和排序。
    
    ## 查询参数
    - **topic_id**: 可选，按主题过滤
    - **limit**: 每页数量 (1-100)
    - **offset**: 偏移量
    - **order_by**: 排序字段 (created_at, updated_at, last_message_time, message_count)
    - **order_direction**: 排序方向 (asc, desc)
    """
    try:
        conversations = await chat_service.get_conversations_list(
            topic_id=topic_id,
            limit=limit,
            offset=offset
        )
        
        response_data = ConversationListResponse(
            conversations=conversations,
            total=len(conversations),  # 简化实现
            has_more=len(conversations) == limit
        )
        
        return APIResponse(success=True, data=response_data.model_dump())
    except Exception as e:
        logger.error(f"❌ 获取对话列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/{conversation_id}/messages", response_model=APIResponse, summary="📖 获取对话消息")
@log_execution_time()
@log_errors()
async def get_conversation_messages(
    conversation_id: str,
    limit: int = Query(50, ge=1, le=200, description="消息数量"),
    before: Optional[str] = Query(None, description="在此消息ID之前"),
    include_context: bool = Query(False, description="是否包含检索上下文"),
    chat_service: ChatService = Depends(get_chat_service),
):
    """
    获取对话的消息历史。
    
    ## 路径参数
    - **conversation_id**: 对话ID
    
    ## 查询参数  
    - **limit**: 消息数量 (1-200)
    - **before**: 在此消息ID之前的消息
    - **include_context**: 是否包含RAG检索上下文
    """
    try:
        messages = await chat_service.get_conversation_messages(
            conversation_id=conversation_id,
            limit=limit,
            before=before
        )
        
        response_data = MessageHistoryResponse(
            messages=messages,
            conversation_id=conversation_id,
            has_more=len(messages) == limit
        )
        
        return APIResponse(success=True, data=response_data.model_dump())
    except Exception as e:
        logger.error(f"❌ 获取对话消息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/conversations/{conversation_id}", response_model=APIResponse, summary="🗑️ 删除对话")
@log_execution_time()
@log_errors()
async def delete_conversation(
    conversation_id: str,
    chat_service: ChatService = Depends(get_chat_service),
):
    """
    删除指定对话及其所有消息。
    
    ## 路径参数
    - **conversation_id**: 对话ID
    """
    try:
        result = await chat_service.delete_conversation(conversation_id)
        return APIResponse(
            success=True,
            data={"deleted": result, "conversation_id": conversation_id}
        )
    except Exception as e:
        logger.error(f"❌ 删除对话失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 搜索接口 ====================

@router.get("/search", response_model=APIResponse, summary="🔍 搜索聊天内容")
@log_execution_time()
@log_errors()
async def search_chat_content(
    q: str = Query(description="搜索关键词", min_length=1, max_length=200),
    topic_id: Optional[int] = Query(None, description="主题ID过滤"),
    conversation_id: Optional[str] = Query(None, description="对话ID过滤"),
    role: Optional[MessageRole] = Query(None, description="消息角色过滤"),
    limit: int = Query(20, ge=1, le=100, description="结果数量"),
    highlight: bool = Query(True, description="是否高亮关键词"),
    chat_service: ChatService = Depends(get_chat_service),
):
    """
    全文搜索聊天记录，支持高亮显示。
    
    ## 查询参数
    - **q**: 搜索关键词 (必需)
    - **topic_id**: 可选，按主题过滤
    - **conversation_id**: 可选，按对话过滤  
    - **role**: 可选，按消息角色过滤 (user, assistant, system)
    - **limit**: 结果数量 (1-100)
    - **highlight**: 是否高亮匹配的关键词
    
    ## 响应格式
    ```json
    {
        "results": [
            {
                "message": {...},
                "highlights": ["高亮片段1", "高亮片段2"],
                "score": 0.95
            }
        ],
        "total": 42,
        "query_time_ms": 15
    }
    ```
    """
    try:
        import time
        start_time = time.time()
        
        search_results = await chat_service.search_chat_content(
            query=q,
            topic_id=topic_id,
            limit=limit
        )
        
        query_time_ms = int((time.time() - start_time) * 1000)
        
        response_data = ChatSearchResponse(
            results=search_results,
            total=len(search_results),
            query_time_ms=query_time_ms
        )
        
        return APIResponse(success=True, data=response_data.model_dump())
    except Exception as e:
        logger.error(f"❌ 搜索聊天内容失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 统计接口 ====================

@router.get("/statistics", response_model=APIResponse, summary="📊 获取聊天统计")
@log_execution_time()
@log_errors()
async def get_chat_statistics(
    topic_id: Optional[int] = Query(None, description="主题ID过滤"),
    chat_service: ChatService = Depends(get_chat_service),
):
    """
    获取聊天统计信息。
    
    ## 查询参数
    - **topic_id**: 可选，按主题过滤统计
    
    ## 响应内容
    - 总对话数
    - 总消息数
    - 平均每对话消息数
    - 总token使用量
    - 热门主题
    - 每日统计 (最近7天)
    """
    try:
        stats = await chat_service.get_chat_statistics(topic_id)
        
        response_data = ChatStatisticsResponse(
            total_conversations=stats.get("total_conversations", 0),
            total_messages=stats.get("total_messages", 0),
            avg_messages_per_conversation=stats.get("avg_messages_per_conversation", 0.0),
            total_tokens_used=stats.get("total_tokens_used", 0),
            top_topics=stats.get("top_topics", []),
            daily_stats=stats.get("daily_stats", [])
        )
        
        return APIResponse(success=True, data=response_data.model_dump())
    except Exception as e:
        logger.error(f"❌ 获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 健康检查接口 ====================

@router.get("/health", response_model=APIResponse, summary="🔧 聊天服务健康检查")
@log_execution_time()
@log_errors()
async def chat_health_check(
    chat_service: ChatService = Depends(get_chat_service),
):
    """
    检查聊天服务的各个组件状态。
    
    ## 检查项目
    - ChatService 初始化状态
    - Elasticsearch 连接状态
    - Weaviate 向量数据库状态
    - OpenAI API 可用性
    """
    try:
        await chat_service.initialize()
        
        health_status = {
            "chat_service": "healthy",
            "elasticsearch": "healthy" if chat_service.es_service.es_client else "unavailable",
            "vector_store": "healthy" if chat_service._vector_store else "unavailable",
            "ai_client": "healthy" if chat_service.ai_client else "mock_mode",
            "timestamp": datetime.now().isoformat()
        }
        
        return APIResponse(success=True, data=health_status)
    except Exception as e:
        logger.error(f"❌ 健康检查失败: {e}")
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")
