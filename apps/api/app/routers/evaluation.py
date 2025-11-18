"""运行时评估 API 路由"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Optional, List, Dict
from pydantic import BaseModel

from apps.api.app.dependencies import get_app_state


router = APIRouter(prefix="/evaluation", tags=["evaluation"])


# ========================================
# 请求/响应模型
# ========================================

class EvaluationStatsResponse(BaseModel):
    """评估统计信息响应"""
    total_queries: int
    evaluated_queries: int
    skipped_queries: int
    evaluation_errors: int
    evaluation_rate: float
    recent_avg_scores: Optional[Dict[str, float]] = None


class RecentResultsResponse(BaseModel):
    """最近评估结果响应"""
    results: List[Dict]
    total_count: int


class EvaluationConfigResponse(BaseModel):
    """评估配置响应"""
    enabled: bool
    mode: str
    sampling_rate: float
    metrics: List[str]


# ========================================
# API 端点
# ========================================

@router.get("/stats", response_model=EvaluationStatsResponse)
async def get_evaluation_stats(state=Depends(get_app_state)):
    """
    获取评估统计信息。
    
    返回运行时评估系统的统计数据，包括：
    - 总查询数
    - 已评估数
    - 评估率
    - 最近的平均分数
    """
    if not state.runtime_evaluator:
        raise HTTPException(
            status_code=503,
            detail="Runtime evaluator is not enabled or initialized"
        )
    
    stats = state.runtime_evaluator.get_stats()
    
    return EvaluationStatsResponse(
        total_queries=stats.get("total_queries", 0),
        evaluated_queries=stats.get("evaluated_queries", 0),
        skipped_queries=stats.get("skipped_queries", 0),
        evaluation_errors=stats.get("evaluation_errors", 0),
        evaluation_rate=stats.get("evaluation_rate", 0.0),
        recent_avg_scores=stats.get("recent_avg_scores")
    )


@router.get("/results/recent", response_model=RecentResultsResponse)
async def get_recent_results(
    limit: int = 10,
    state=Depends(get_app_state)
):
    """
    获取最近的评估结果。
    
    Args:
        limit: 返回结果数量限制（默认 10）
    
    Returns:
        最近的评估结果列表
    """
    if not state.runtime_evaluator:
        raise HTTPException(
            status_code=503,
            detail="Runtime evaluator is not enabled or initialized"
        )
    
    results = state.runtime_evaluator.get_recent_results(limit=limit)
    
    return RecentResultsResponse(
        results=results,
        total_count=len(results)
    )


@router.get("/config", response_model=EvaluationConfigResponse)
async def get_evaluation_config(state=Depends(get_app_state)):
    """
    获取当前评估配置。
    
    Returns:
        评估系统的配置信息
    """
    if not state.runtime_evaluator:
        return EvaluationConfigResponse(
            enabled=False,
            mode="disabled",
            sampling_rate=0.0,
            metrics=[]
        )
    
    config = state.runtime_evaluator.config
    
    return EvaluationConfigResponse(
        enabled=True,
        mode=config.mode.value,
        sampling_rate=config.sampling_rate,
        metrics=[m.value for m in config.metrics]
    )


@router.post("/reset-stats")
async def reset_evaluation_stats(state=Depends(get_app_state)):
    """
    重置评估统计信息。
    
    将所有统计计数器重置为 0。
    """
    if not state.runtime_evaluator:
        raise HTTPException(
            status_code=503,
            detail="Runtime evaluator is not enabled or initialized"
        )
    
    # 重置统计
    state.runtime_evaluator.stats = {
        "total_queries": 0,
        "evaluated_queries": 0,
        "skipped_queries": 0,
        "evaluation_errors": 0,
    }
    
    return {"message": "Statistics reset successfully"}


@router.get("/health")
async def evaluation_health(state=Depends(get_app_state)):
    """
    检查评估系统健康状态。
    
    Returns:
        评估系统的健康状态信息
    """
    if not state.runtime_evaluator:
        return {
            "status": "disabled",
            "message": "Runtime evaluator is not enabled"
        }
    
    stats = state.runtime_evaluator.get_stats()
    
    # 判断健康状态
    if stats.get("evaluation_errors", 0) > stats.get("evaluated_queries", 0) * 0.1:
        status = "unhealthy"
        message = "Error rate is too high (>10%)"
    else:
        status = "healthy"
        message = "Evaluation system is working properly"
    
    return {
        "status": status,
        "message": message,
        "stats": stats
    }

