"""
增强RAG API

提供新的模块化RAG架构的API接口。
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession

from logging_system import get_logger, log_execution_time, log_errors
from modules.database import get_db_session
from modules.schemas import APIResponse
from modules.schemas.chat import ChatRequest, ChatResponse
from modules.services.rag_integrated_chat_service import (
    RAGIntegratedChatService, 
    create_rag_integrated_chat_service
)
from pydantic import BaseModel

router = APIRouter(prefix="/enhanced-rag", tags=["Enhanced RAG"])
logger = get_logger(__name__)


# ==================== 请求/响应模型 ====================

class RAGPipelineConfig(BaseModel):
    """RAG管道配置"""
    pipeline_type: str = "adaptive"  # simple, hybrid, adaptive, multi_hop
    config: Optional[Dict[str, Any]] = None
    enable_routing: bool = True


class RAGSwitchRequest(BaseModel):
    """RAG管道切换请求"""
    pipeline_type: str
    config: Optional[Dict[str, Any]] = None


class RAGStatsResponse(BaseModel):
    """RAG统计响应"""
    rag_stats: Dict[str, Any]
    routing_stats: Dict[str, Any]
    health_status: Dict[str, Any]


class RAGSearchRequest(BaseModel):
    """RAG搜索请求"""
    query: str
    top_k: int = 10
    score_threshold: float = 0.0
    use_hybrid: Optional[bool] = None
    use_reranking: Optional[bool] = None


class RAGSearchResponse(BaseModel):
    """RAG搜索响应"""
    query: str
    documents: List[Dict[str, Any]]
    total_found: int
    processing_time_ms: float
    search_metadata: Dict[str, Any]


# ==================== 服务依赖 ====================

_rag_service_cache: Optional[RAGIntegratedChatService] = None


async def get_rag_integrated_service(
    session: AsyncSession = Depends(get_db_session)
) -> RAGIntegratedChatService:
    """获取RAG集成聊天服务"""
    global _rag_service_cache
    
    if _rag_service_cache is None:
        try:
            _rag_service_cache = await create_rag_integrated_chat_service(
                session=session,
                pipeline_type="adaptive",
                enable_routing=True
            )
            logger.info("RAG集成聊天服务创建成功")
        except Exception as e:
            logger.error(f"创建RAG集成聊天服务失败: {e}")
            raise HTTPException(status_code=500, detail=f"服务初始化失败: {str(e)}")
    
    return _rag_service_cache


# ==================== API端点 ====================

@router.post("/chat", response_model=APIResponse)
@log_execution_time(threshold_ms=1000)
@log_errors()
async def enhanced_rag_chat(
    request: ChatRequest,
    service: RAGIntegratedChatService = Depends(get_rag_integrated_service)
):
    """
    增强RAG聊天接口
    
    使用新的模块化RAG架构处理聊天请求，支持：
    - 自适应查询处理
    - 混合检索（向量+BM25）
    - 智能重排序
    - 多跳推理
    - 流式响应
    """
    try:
        start_time = datetime.now()
        
        # 处理聊天请求
        response = await service.chat(request)
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return APIResponse(
            success=True,
            data=response.dict(),
            message="聊天处理成功",
            metadata={
                "processing_time_ms": processing_time,
                "rag_enabled": service.rag_enabled,
                "routing_enabled": service.routing_enabled
            }
        )
        
    except Exception as e:
        logger.error(f"增强RAG聊天失败: {e}")
        raise HTTPException(status_code=500, detail=f"聊天处理失败: {str(e)}")


@router.post("/search", response_model=APIResponse)
@log_execution_time(threshold_ms=500)
@log_errors()
async def enhanced_rag_search(
    request: RAGSearchRequest,
    service: RAGIntegratedChatService = Depends(get_rag_integrated_service)
):
    """
    增强RAG搜索接口
    
    直接使用RAG组件进行文档搜索，支持：
    - 混合检索
    - 重排序
    - 可配置的搜索参数
    """
    try:
        start_time = datetime.now()
        
        # 检查是否有增强RAG处理器
        if not hasattr(service, 'rag_pipeline') or not service.rag_pipeline:
            raise HTTPException(status_code=503, detail="RAG管道未初始化")
        
        # 这里需要从RAG管道中获取检索器组件进行搜索
        # 简化实现：直接调用RAG管道的process方法
        rag_response = await service.rag_pipeline.process(
            query=request.query,
            user_context={
                "top_k": request.top_k,
                "score_threshold": request.score_threshold
            }
        )
        
        # 转换文档格式
        documents = []
        for doc in rag_response.retrieved_documents:
            documents.append({
                "id": doc.id,
                "content": doc.content,
                "score": doc.score,
                "source": doc.source,
                "metadata": doc.metadata,
                "rank": doc.rank
            })
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        search_response = RAGSearchResponse(
            query=request.query,
            documents=documents,
            total_found=len(documents),
            processing_time_ms=processing_time,
            search_metadata={
                "strategy": rag_response.metadata.get("strategy", "unknown"),
                "components_used": rag_response.metadata.get("components_used", []),
                "confidence": rag_response.confidence
            }
        )
        
        return APIResponse(
            success=True,
            data=search_response.dict(),
            message="搜索完成",
            metadata={
                "processing_time_ms": processing_time
            }
        )
        
    except Exception as e:
        logger.error(f"增强RAG搜索失败: {e}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


@router.get("/stats", response_model=APIResponse)
@log_execution_time(threshold_ms=200)
@log_errors()
async def get_rag_stats(
    service: RAGIntegratedChatService = Depends(get_rag_integrated_service)
):
    """
    获取RAG统计信息
    
    返回RAG管道和路由引擎的统计信息。
    """
    try:
        # 获取RAG统计
        rag_stats = await service.get_rag_stats()
        
        # 获取路由统计
        routing_stats = await service.get_routing_stats()
        
        # 获取健康状态
        health_status = await service.health_check()
        
        stats_response = RAGStatsResponse(
            rag_stats=rag_stats,
            routing_stats=routing_stats,
            health_status=health_status
        )
        
        return APIResponse(
            success=True,
            data=stats_response.dict(),
            message="统计信息获取成功"
        )
        
    except Exception as e:
        logger.error(f"获取RAG统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")


@router.post("/switch-pipeline", response_model=APIResponse)
@log_execution_time(threshold_ms=2000)
@log_errors()
async def switch_rag_pipeline(
    request: RAGSwitchRequest,
    service: RAGIntegratedChatService = Depends(get_rag_integrated_service)
):
    """
    动态切换RAG管道
    
    支持在运行时切换不同类型的RAG管道。
    """
    try:
        start_time = datetime.now()
        
        # 切换RAG管道
        await service.switch_rag_pipeline(
            pipeline_type=request.pipeline_type,
            config=request.config
        )
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # 获取新管道的健康状态
        health_status = await service.health_check()
        
        return APIResponse(
            success=True,
            data={
                "pipeline_type": request.pipeline_type,
                "switch_time_ms": processing_time,
                "health_status": health_status
            },
            message=f"RAG管道已切换到: {request.pipeline_type}"
        )
        
    except Exception as e:
        logger.error(f"切换RAG管道失败: {e}")
        raise HTTPException(status_code=500, detail=f"管道切换失败: {str(e)}")


@router.get("/health", response_model=APIResponse)
@log_execution_time(threshold_ms=100)
@log_errors()
async def health_check(
    service: RAGIntegratedChatService = Depends(get_rag_integrated_service)
):
    """
    RAG服务健康检查
    
    检查所有RAG组件的健康状态。
    """
    try:
        health_status = await service.health_check()
        
        # 判断整体健康状态
        is_healthy = (
            health_status.get("initialized", False) and
            health_status.get("rag_initialized", False)
        )
        
        return APIResponse(
            success=is_healthy,
            data=health_status,
            message="健康检查完成" if is_healthy else "服务存在问题"
        )
        
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        raise HTTPException(status_code=500, detail=f"健康检查失败: {str(e)}")


@router.get("/pipeline-types", response_model=APIResponse)
@log_execution_time(threshold_ms=50)
@log_errors()
async def get_pipeline_types():
    """
    获取支持的RAG管道类型
    
    返回所有可用的RAG管道类型和配置选项。
    """
    try:
        from modules.rag.factory import DEFAULT_CONFIGS
        
        pipeline_types = {
            "simple": {
                "description": "简单RAG管道，适合基础查询",
                "features": ["向量检索", "基础生成"],
                "config": DEFAULT_CONFIGS.get("simple_rag", {})
            },
            "hybrid": {
                "description": "混合RAG管道，结合向量和BM25检索",
                "features": ["向量检索", "BM25检索", "结果融合", "重排序"],
                "config": DEFAULT_CONFIGS.get("hybrid_rag", {})
            },
            "adaptive": {
                "description": "自适应RAG管道，根据查询复杂度选择策略",
                "features": ["智能查询分析", "自适应策略", "多种检索方法", "高级重排序"],
                "config": DEFAULT_CONFIGS.get("adaptive_rag", {})
            },
            "multi_hop": {
                "description": "多跳RAG管道，支持复杂推理查询",
                "features": ["多跳推理", "查询重写", "历史追踪"],
                "config": {}
            }
        }
        
        return APIResponse(
            success=True,
            data=pipeline_types,
            message="管道类型信息获取成功"
        )
        
    except Exception as e:
        logger.error(f"获取管道类型失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取管道类型失败: {str(e)}")


@router.post("/test-query", response_model=APIResponse)
@log_execution_time(threshold_ms=1000)
@log_errors()
async def test_query(
    query: str = Body(..., embed=True),
    pipeline_type: Optional[str] = Body("adaptive", embed=True),
    service: RAGIntegratedChatService = Depends(get_rag_integrated_service)
):
    """
    测试查询接口
    
    用于测试不同RAG管道对查询的处理效果。
    """
    try:
        start_time = datetime.now()
        
        # 如果需要，切换到指定的管道类型
        current_pipeline = getattr(service.rag_pipeline, 'pipeline_name', 'unknown')
        if pipeline_type != current_pipeline:
            await service.switch_rag_pipeline(pipeline_type)
        
        # 构建测试请求
        test_request = ChatRequest(
            message=query,
            max_results=5,
            score_threshold=0.1,
            include_context=True
        )
        
        # 处理查询
        response = await service.chat(test_request)
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # 构建测试结果
        test_result = {
            "query": query,
            "pipeline_type": pipeline_type,
            "answer": response.content,
            "confidence": response.confidence,
            "retrieved_documents": len(response.retrieved_contexts),
            "processing_time_ms": processing_time,
            "contexts": [
                {
                    "content": ctx.content[:200] + "..." if len(ctx.content) > 200 else ctx.content,
                    "score": ctx.score,
                    "source": ctx.source
                }
                for ctx in response.retrieved_contexts[:3]  # 只返回前3个上下文
            ]
        }
        
        return APIResponse(
            success=True,
            data=test_result,
            message="查询测试完成"
        )
        
    except Exception as e:
        logger.error(f"查询测试失败: {e}")
        raise HTTPException(status_code=500, detail=f"查询测试失败: {str(e)}")


# ==================== 清理函数 ====================

async def cleanup_rag_service():
    """清理RAG服务资源"""
    global _rag_service_cache
    
    if _rag_service_cache:
        try:
            await _rag_service_cache.cleanup()
            _rag_service_cache = None
            logger.info("RAG服务资源清理完成")
        except Exception as e:
            logger.warning(f"RAG服务清理失败: {e}")


# 注册清理函数（在应用关闭时调用）
import atexit
atexit.register(lambda: asyncio.create_task(cleanup_rag_service()))
