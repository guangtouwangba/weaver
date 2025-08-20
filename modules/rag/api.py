"""
Advanced RAG API Integration

FastAPI endpoints for the advanced RAG system with comprehensive
topic-based chat, document management, and evaluation capabilities.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field

from .chat import TopicChatSystem, ChatRequest, ChatResponse, ChatMode
from .evaluation import EvaluationReport

logger = logging.getLogger(__name__)

# Pydantic models for API

class ChatRequestModel(BaseModel):
    """Chat request model"""
    query: str = Field(..., description="用户查询", min_length=1, max_length=1000)
    topic_id: int = Field(..., description="主题ID", ge=1)
    conversation_id: Optional[str] = Field(None, description="对话ID")
    mode: ChatMode = Field(ChatMode.CONVERSATION, description="聊天模式")
    max_sources: int = Field(5, description="最大来源数量", ge=1, le=10)
    temperature: float = Field(0.1, description="生成温度", ge=0.0, le=1.0)

class ChatResponseModel(BaseModel):
    """Chat response model"""
    answer: str = Field(..., description="生成的回答")
    confidence: float = Field(..., description="置信度", ge=0.0, le=1.0)
    sources: List[Dict[str, Any]] = Field(..., description="来源列表")
    conversation_id: str = Field(..., description="对话ID")
    response_time: float = Field(..., description="响应时间(秒)")
    follow_up_questions: Optional[List[str]] = Field(None, description="后续问题建议")
    query_analysis: Optional[Dict[str, Any]] = Field(None, description="查询分析")
    retrieval_stats: Optional[Dict[str, Any]] = Field(None, description="检索统计")

class DocumentIndexRequest(BaseModel):
    """Document indexing request"""
    topic_id: int = Field(..., description="主题ID", ge=1)
    documents: List[Dict[str, Any]] = Field(..., description="文档列表", min_items=1)
    force_reindex: bool = Field(False, description="强制重新索引")

class DocumentIndexResponse(BaseModel):
    """Document indexing response"""
    success: bool = Field(..., description="索引是否成功")
    topic_id: int = Field(..., description="主题ID")
    documents_processed: int = Field(..., description="处理的文档数量")
    chunks_created: int = Field(..., description="创建的块数量")
    indexing_completed_at: str = Field(..., description="索引完成时间")
    error: Optional[str] = Field(None, description="错误信息")

class TopicStatisticsResponse(BaseModel):
    """Topic statistics response"""
    topic_id: int = Field(..., description="主题ID")
    document_count: int = Field(..., description="文档数量")
    total_chunks: int = Field(..., description="总块数")
    average_chunk_score: float = Field(..., description="平均块分数")
    content_types: Dict[str, int] = Field(..., description="内容类型分布")
    languages: Dict[str, int] = Field(..., description="语言分布")
    last_updated: str = Field(..., description="最后更新时间")

class SystemMetricsResponse(BaseModel):
    """System metrics response"""
    total_queries: int = Field(..., description="总查询数")
    successful_responses: int = Field(..., description="成功响应数")
    average_response_time: float = Field(..., description="平均响应时间")
    active_conversations: int = Field(..., description="活跃对话数")
    indexed_topics: int = Field(..., description="已索引主题数")
    component_status: Dict[str, str] = Field(..., description="组件状态")

class EvaluationRequest(BaseModel):
    """Evaluation request"""
    test_cases_file: Optional[str] = Field(None, description="测试用例文件路径")
    export_report: bool = Field(False, description="是否导出报告")
    output_file: Optional[str] = Field(None, description="输出文件路径")

class EvaluationResponse(BaseModel):
    """Evaluation response"""
    evaluation_completed: bool = Field(..., description="评估是否完成")
    overall_score: Optional[float] = Field(None, description="总体得分")
    metric_scores: Optional[Dict[str, float]] = Field(None, description="指标得分")
    recommendations: Optional[List[str]] = Field(None, description="改进建议")
    error: Optional[str] = Field(None, description="错误信息")

class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="系统状态")
    initialized: bool = Field(..., description="是否已初始化")
    components: Dict[str, str] = Field(..., description="组件状态")
    health_ratio: float = Field(..., description="健康比例")
    timestamp: str = Field(..., description="检查时间")

# Global RAG system instance
rag_system: Optional[TopicChatSystem] = None

async def get_rag_system() -> TopicChatSystem:
    """Get or create RAG system instance"""
    global rag_system
    if rag_system is None:
        # Initialize with default config - in production, load from environment/config
        config = {
            "vector_store_type": "chromadb",  # Use ChromaDB for easier setup
            "vector_store_config": {
                "persist_directory": "./data/chroma_db"
            },
            "embedding_cache_config": {
                "enabled": False  # Disable cache for simplicity
            },
            "generation_config": {
                "llm_provider": "openai",
                "model": "gpt-3.5-turbo",  # Use more accessible model
                "max_tokens": 1000,
                "temperature": 0.1
            }
        }
        rag_system = TopicChatSystem(config)
        await rag_system.initialize()
    
    return rag_system

# Create router
router = APIRouter(prefix="/api/v1/rag", tags=["Advanced RAG"])

@router.post("/chat", response_model=ChatResponseModel, 
            summary="智能对话", description="基于主题资源的智能对话接口")
async def chat(request: ChatRequestModel, 
               rag_system: TopicChatSystem = Depends(get_rag_system)) -> ChatResponseModel:
    """
    # 智能对话接口
    
    基于指定主题下的多个资源进行智能对话，支持：
    
    ## 功能特性
    - 🔍 **多策略检索**: 语义搜索、关键词搜索、混合搜索
    - 🧠 **上下文感知**: 维护对话历史和上下文理解
    - 📚 **多文档整合**: 跨多个文档进行信息综合
    - 🎯 **精准回答**: 基于检索内容生成准确答案
    - 📖 **来源引用**: 提供详细的信息来源和引用
    
    ## 使用示例
    ```json
    {
        "query": "什么是人工智能？",
        "topic_id": 1,
        "mode": "conversation",
        "max_sources": 5
    }
    ```
    
    ## 响应内容
    - **answer**: 生成的智能回答
    - **confidence**: 答案置信度 (0-1)
    - **sources**: 详细来源信息
    - **follow_up_questions**: 建议的后续问题
    """
    try:
        # Convert to internal request format
        chat_request = ChatRequest(
            query=request.query,
            topic_id=request.topic_id,
            conversation_id=request.conversation_id,
            mode=request.mode,
            max_sources=request.max_sources,
            temperature=request.temperature
        )
        
        # Process chat
        response = await rag_system.chat(chat_request)
        
        # Convert to API response format
        return ChatResponseModel(
            answer=response.answer,
            confidence=response.confidence,
            sources=response.sources,
            conversation_id=response.conversation_id,
            response_time=response.response_time,
            follow_up_questions=response.follow_up_questions,
            query_analysis=response.query_analysis,
            retrieval_stats=response.retrieval_stats
        )
        
    except Exception as e:
        logger.error(f"Chat request failed: {e}")
        raise HTTPException(status_code=500, detail=f"聊天处理失败: {str(e)}")

@router.post("/topics/{topic_id}/index", response_model=DocumentIndexResponse,
            summary="索引文档", description="为指定主题索引文档")
async def index_documents(
    topic_id: int,
    request: DocumentIndexRequest,
    background_tasks: BackgroundTasks,
    rag_system: TopicChatSystem = Depends(get_rag_system)
) -> DocumentIndexResponse:
    """
    # 文档索引接口
    
    为指定主题索引多个文档，支持：
    
    ## 处理功能
    - 📄 **多格式支持**: PDF、Word、TXT、Markdown等
    - 🔨 **智能分块**: 基于语义的文档分块策略
    - 🧮 **向量化**: 多模型嵌入生成
    - 🗂️ **元数据管理**: 丰富的文档元数据提取
    
    ## 文档格式
    ```json
    {
        "topic_id": 1,
        "documents": [
            {
                "id": "doc_001",
                "title": "人工智能概述",
                "content": "人工智能是...",
                "metadata": {
                    "author": "张三",
                    "created_at": "2024-01-01"
                }
            }
        ]
    }
    ```
    
    ## 异步处理
    - 大批量文档支持后台异步处理
    - 实时进度跟踪和状态更新
    """
    try:
        if topic_id != request.topic_id:
            raise HTTPException(
                status_code=400, 
                detail="路径中的topic_id与请求体中的topic_id不匹配"
            )
        
        # Validate documents
        if not request.documents:
            raise HTTPException(status_code=400, detail="文档列表不能为空")
        
        for doc in request.documents:
            if "id" not in doc or "content" not in doc:
                raise HTTPException(
                    status_code=400, 
                    detail="每个文档必须包含'id'和'content'字段"
                )
        
        # Index documents
        result = await rag_system.index_topic_documents(
            topic_id=topic_id,
            documents=request.documents
        )
        
        return DocumentIndexResponse(
            success=result["success"],
            topic_id=topic_id,
            documents_processed=result.get("documents_processed", 0),
            chunks_created=result.get("chunks_created", 0),
            indexing_completed_at=result.get("indexing_completed_at", datetime.now().isoformat()),
            error=result.get("error")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document indexing failed: {e}")
        raise HTTPException(status_code=500, detail=f"文档索引失败: {str(e)}")

@router.get("/topics/{topic_id}/statistics", response_model=TopicStatisticsResponse,
           summary="主题统计", description="获取主题的详细统计信息")
async def get_topic_statistics(
    topic_id: int,
    rag_system: TopicChatSystem = Depends(get_rag_system)
) -> TopicStatisticsResponse:
    """
    # 主题统计接口
    
    获取指定主题的详细统计信息：
    
    ## 统计内容
    - 📊 **文档统计**: 文档数量、块数量
    - 📈 **质量指标**: 平均分数、覆盖率
    - 🌐 **内容分析**: 语言分布、类型分布
    - ⏰ **时间信息**: 最后更新时间
    
    ## 用途
    - 监控主题内容质量
    - 分析文档分布情况
    - 优化检索策略
    """
    try:
        stats = await rag_system.get_topic_statistics(topic_id)
        
        if stats is None:
            raise HTTPException(
                status_code=404, 
                detail=f"主题 {topic_id} 不存在或尚未索引任何文档"
            )
        
        return TopicStatisticsResponse(
            topic_id=stats["topic_id"],
            document_count=stats["document_count"],
            total_chunks=stats["total_chunks"],
            average_chunk_score=stats["average_chunk_score"],
            content_types=stats["content_types"],
            languages=stats["languages"],
            last_updated=stats["last_updated"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get topic statistics: {e}")
        raise HTTPException(status_code=500, detail=f"获取主题统计失败: {str(e)}")

@router.get("/system/metrics", response_model=SystemMetricsResponse,
           summary="系统指标", description="获取系统性能指标")
async def get_system_metrics(
    rag_system: TopicChatSystem = Depends(get_rag_system)
) -> SystemMetricsResponse:
    """
    # 系统性能指标
    
    获取RAG系统的综合性能指标：
    
    ## 指标类型
    - 🔢 **使用统计**: 查询数、响应数、成功率
    - ⚡ **性能指标**: 平均响应时间、吞吐量
    - 💬 **对话状态**: 活跃对话数、对话质量
    - 🏗️ **系统状态**: 组件健康状况、资源使用
    
    ## 应用场景
    - 系统监控和告警
    - 性能优化分析
    - 容量规划参考
    """
    try:
        metrics = await rag_system.get_system_metrics()
        
        return SystemMetricsResponse(
            total_queries=metrics["total_queries"],
            successful_responses=metrics["successful_responses"],
            average_response_time=metrics["average_response_time"],
            active_conversations=metrics["active_conversations"],
            indexed_topics=metrics["indexed_topics"],
            component_status=metrics["component_status"]
        )
        
    except Exception as e:
        logger.error(f"Failed to get system metrics: {e}")
        raise HTTPException(status_code=500, detail=f"获取系统指标失败: {str(e)}")

@router.post("/evaluation/run", response_model=EvaluationResponse,
            summary="运行评估", description="运行RAG系统综合评估")
async def run_evaluation(
    request: EvaluationRequest,
    background_tasks: BackgroundTasks,
    rag_system: TopicChatSystem = Depends(get_rag_system)
) -> EvaluationResponse:
    """
    # RAG系统评估
    
    对RAG系统进行全面的性能评估：
    
    ## 评估维度
    - 🎯 **检索质量**: Precision@K, Recall@K, NDCG, MRR
    - ✍️ **生成质量**: BLEU, ROUGE, 语义相似度
    - 🔄 **端到端**: 整体答案质量、响应时间
    - 👤 **用户体验**: 可读性、有用性、满意度
    
    ## 评估流程
    1. 加载测试用例
    2. 执行检索和生成
    3. 计算多维度指标
    4. 生成改进建议
    
    ## 输出内容
    - 综合得分和分项得分
    - 详细的评估报告
    - 个性化改进建议
    """
    try:
        # Run evaluation
        result = await rag_system.evaluate_system_performance(
            test_cases_file=request.test_cases_file
        )
        
        return EvaluationResponse(
            evaluation_completed=result["evaluation_completed"],
            overall_score=result.get("overall_score"),
            metric_scores=result.get("metric_scores"),
            recommendations=result.get("recommendations"),
            error=result.get("error")
        )
        
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        raise HTTPException(status_code=500, detail=f"系统评估失败: {str(e)}")

@router.get("/conversations/{conversation_id}/summary",
           summary="对话摘要", description="获取对话摘要和统计信息")
async def get_conversation_summary(
    conversation_id: str,
    rag_system: TopicChatSystem = Depends(get_rag_system)
) -> Dict[str, Any]:
    """
    # 对话摘要接口
    
    获取指定对话的详细摘要信息：
    
    ## 摘要内容
    - 📊 **基础统计**: 轮次、响应时间、话题分布
    - 🎯 **质量指标**: 用户满意度、问题解决率
    - 🔍 **内容分析**: 常见话题、未解决问题
    - ⏰ **时间信息**: 创建时间、最后活动时间
    
    ## 应用价值
    - 对话质量分析
    - 用户行为洞察
    - 系统优化方向
    """
    try:
        summary = await rag_system.get_conversation_summary(conversation_id)
        
        if summary is None:
            raise HTTPException(
                status_code=404,
                detail=f"对话 {conversation_id} 不存在"
            )
        
        return summary
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get conversation summary: {e}")
        raise HTTPException(status_code=500, detail=f"获取对话摘要失败: {str(e)}")

@router.get("/health", response_model=HealthCheckResponse,
           summary="健康检查", description="系统健康状态检查")
async def health_check(
    rag_system: TopicChatSystem = Depends(get_rag_system)
) -> HealthCheckResponse:
    """
    # 系统健康检查
    
    全面检查RAG系统各组件的健康状态：
    
    ## 检查组件
    - 🗄️ **向量存储**: 连接状态、索引完整性
    - 🧮 **嵌入服务**: 模型加载、推理性能
    - 🔍 **检索系统**: 搜索功能、排序算法
    - 🤖 **生成服务**: LLM连接、推理能力
    - 📊 **评估框架**: 指标计算、报告生成
    
    ## 健康状态
    - **healthy**: 所有组件正常
    - **degraded**: 部分组件异常但可用
    - **unhealthy**: 关键组件故障
    
    ## 监控建议
    - 集成到监控系统
    - 设置自动告警
    - 定期健康检查
    """
    try:
        health_result = await rag_system.health_check()
        
        return HealthCheckResponse(
            status=health_result["status"],
            initialized=health_result["initialized"],
            components=health_result["components"],
            health_ratio=health_result["health_ratio"],
            timestamp=health_result["timestamp"]
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthCheckResponse(
            status="unhealthy",
            initialized=False,
            components={},
            health_ratio=0.0,
            timestamp=datetime.now().isoformat()
        )

@router.delete("/conversations/{conversation_id}",
              summary="删除对话", description="删除指定对话及其历史")
async def delete_conversation(
    conversation_id: str,
    rag_system: TopicChatSystem = Depends(get_rag_system)
) -> Dict[str, str]:
    """删除对话历史"""
    try:
        # In a real implementation, this would delete from persistent storage
        if conversation_id in rag_system.active_conversations:
            del rag_system.active_conversations[conversation_id]
            return {"message": f"对话 {conversation_id} 已删除"}
        else:
            raise HTTPException(status_code=404, detail="对话不存在")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete conversation: {e}")
        raise HTTPException(status_code=500, detail=f"删除对话失败: {str(e)}")

@router.post("/system/cleanup",
            summary="清理资源", description="清理非活跃对话和临时资源")
async def cleanup_resources(
    max_age_hours: int = 24,
    rag_system: TopicChatSystem = Depends(get_rag_system)
) -> Dict[str, Any]:
    """清理系统资源"""
    try:
        cleaned_conversations = await rag_system.cleanup_inactive_conversations(max_age_hours)
        
        return {
            "cleaned_conversations": cleaned_conversations,
            "cleanup_completed_at": datetime.now().isoformat(),
            "max_age_hours": max_age_hours
        }
        
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        raise HTTPException(status_code=500, detail=f"资源清理失败: {str(e)}")

# Add router to main app
def include_rag_routes(app):
    """Include RAG routes in FastAPI app"""
    app.include_router(router)
    
    @app.on_event("shutdown")
    async def shutdown_rag_system():
        """Shutdown RAG system on app shutdown"""
        global rag_system
        if rag_system:
            await rag_system.shutdown()
            rag_system = None