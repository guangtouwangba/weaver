"""
工作流管理API

提供RESTful接口来管理和监控工作流执行
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..services.workflow_service import WorkflowService, create_workflow_service


# 定义基础响应模型
class BaseResponse(BaseModel):
    success: bool = Field(..., description="操作是否成功")
    message: str = Field(..., description="响应消息")
    data: Any = Field(None, description="响应数据")


logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/workflow", tags=["工作流管理"])


# 请求模型
class DocumentProcessingRequest(BaseModel):
    """文档处理请求"""

    file_id: str = Field(..., description="文件ID")
    document_data: Dict[str, Any] = Field(..., description="文档数据")
    enable_rag: bool = Field(True, description="是否启用RAG处理")
    topic_id: Optional[int] = Field(None, description="主题ID")
    embedding_provider: str = Field("openai", description="嵌入服务提供商")
    vector_store_provider: str = Field("weaviate", description="向量存储提供商")
    priority: int = Field(5, description="优先级", ge=1, le=10)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="其他元数据")


class DocumentCreateRequest(BaseModel):
    """文档创建请求"""

    file_id: str = Field(..., description="文件ID")
    document_data: Dict[str, Any] = Field(..., description="文档数据")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="其他元数据")


class RAGProcessingRequest(BaseModel):
    """RAG处理请求"""

    document_id: str = Field(..., description="文档ID")
    file_path: str = Field(..., description="文件路径")
    content_type: str = Field("txt", description="内容类型")
    topic_id: Optional[int] = Field(None, description="主题ID")
    embedding_provider: str = Field("openai", description="嵌入服务提供商")
    vector_store_provider: str = Field("weaviate", description="向量存储提供商")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="其他元数据")


class WorkflowCancelRequest(BaseModel):
    """工作流取消请求"""

    reason: Optional[str] = Field(None, description="取消原因")


# 响应模型
class WorkflowStartResponse(BaseResponse):
    """工作流启动响应"""

    execution_id: str = Field(..., description="工作流执行ID")
    workflow_id: str = Field(..., description="工作流ID")
    started_at: str = Field(..., description="启动时间")


class TaskSubmitResponse(BaseResponse):
    """任务提交响应"""

    task_id: str = Field(..., description="任务ID")
    task_type: str = Field(..., description="任务类型")
    submitted_at: str = Field(..., description="提交时间")


class WorkflowStatusResponse(BaseResponse):
    """工作流状态响应"""

    execution_id: str = Field(..., description="工作流执行ID")
    status: Dict[str, Any] = Field(..., description="执行状态详情")


class WorkflowListResponse(BaseResponse):
    """工作流列表响应"""

    workflows: List[Dict[str, Any]] = Field(..., description="可用工作流列表")


# API端点
@router.post("/document-processing", response_model=WorkflowStartResponse)
async def start_document_processing(
    request: DocumentProcessingRequest, session: AsyncSession = Depends(get_session)
):
    """启动文档处理工作流"""
    try:
        service = WorkflowService(session)

        execution_id = await service.start_document_processing(
            file_id=request.file_id,
            document_data=request.document_data,
            enable_rag=request.enable_rag,
            topic_id=request.topic_id,
            embedding_provider=request.embedding_provider,
            vector_store_provider=request.vector_store_provider,
            priority=request.priority,
            **request.metadata,
        )

        return WorkflowStartResponse(
            success=True,
            message="文档处理工作流已启动",
            execution_id=execution_id,
            workflow_id="document_processing",
            started_at=datetime.utcnow().isoformat(),
        )

    except Exception as e:
        logger.error(f"启动文档处理工作流失败: {e}")
        raise HTTPException(status_code=500, detail=f"启动工作流失败: {str(e)}")


@router.post("/document-create", response_model=TaskSubmitResponse)
async def create_document_only(
    request: DocumentCreateRequest, session: AsyncSession = Depends(get_session)
):
    """仅创建文档，不进行RAG处理"""
    try:
        service = WorkflowService(session)

        result = await service.create_document_only(
            file_id=request.file_id, document_data=request.document_data, **request.metadata
        )

        return TaskSubmitResponse(
            success=True,
            message="文档创建任务已提交",
            task_id=result["task_id"],
            task_type=result["task_type"],
            submitted_at=result["submitted_at"],
        )

    except Exception as e:
        logger.error(f"提交文档创建任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"任务提交失败: {str(e)}")


@router.post("/rag-processing", response_model=TaskSubmitResponse)
async def process_rag_only(
    request: RAGProcessingRequest, session: AsyncSession = Depends(get_session)
):
    """仅进行RAG处理，假设文档已存在"""
    try:
        service = WorkflowService(session)

        result = await service.process_rag_only(
            document_id=request.document_id,
            file_path=request.file_path,
            content_type=request.content_type,
            topic_id=request.topic_id,
            embedding_provider=request.embedding_provider,
            vector_store_provider=request.vector_store_provider,
            **request.metadata,
        )

        return TaskSubmitResponse(
            success=True,
            message="RAG处理任务已提交",
            task_id=result["task_id"],
            task_type=result["task_type"],
            submitted_at=result["submitted_at"],
        )

    except Exception as e:
        logger.error(f"提交RAG处理任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"任务提交失败: {str(e)}")


@router.get("/status/{execution_id}", response_model=WorkflowStatusResponse)
async def get_workflow_status(execution_id: str, session: AsyncSession = Depends(get_session)):
    """获取工作流执行状态"""
    try:
        service = WorkflowService(session)

        status = await service.get_workflow_status(execution_id)

        if status is None:
            raise HTTPException(status_code=404, detail="工作流执行不存在")

        return WorkflowStatusResponse(
            success=True, message="状态获取成功", execution_id=execution_id, status=status
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取工作流状态失败: {execution_id}, {e}")
        raise HTTPException(status_code=500, detail=f"状态获取失败: {str(e)}")


@router.post("/cancel/{execution_id}")
async def cancel_workflow(
    execution_id: str,
    request: WorkflowCancelRequest = Body(...),
    session: AsyncSession = Depends(get_session),
):
    """取消工作流执行"""
    try:
        service = WorkflowService(session)

        success = await service.cancel_workflow(execution_id, request.reason)

        if not success:
            raise HTTPException(status_code=404, detail="工作流执行不存在或取消失败")

        return BaseResponse(success=True, message=f"工作流已取消: {request.reason or '用户取消'}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"取消工作流失败: {execution_id}, {e}")
        raise HTTPException(status_code=500, detail=f"取消失败: {str(e)}")


@router.get("/list", response_model=WorkflowListResponse)
async def list_workflows(session: AsyncSession = Depends(get_session)):
    """获取可用的工作流列表"""
    try:
        service = WorkflowService(session)

        workflows = await service.get_available_workflows()

        return WorkflowListResponse(success=True, message="工作流列表获取成功", workflows=workflows)

    except Exception as e:
        logger.error(f"获取工作流列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取列表失败: {str(e)}")


@router.get("/definition/{workflow_id}")
async def get_workflow_definition(workflow_id: str, session: AsyncSession = Depends(get_session)):
    """获取工作流定义详情"""
    try:
        service = WorkflowService(session)

        definition = await service.get_workflow_definition(workflow_id)

        if definition is None:
            raise HTTPException(status_code=404, detail="工作流定义不存在")

        return BaseResponse(success=True, message="工作流定义获取成功", data=definition)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取工作流定义失败: {workflow_id}, {e}")
        raise HTTPException(status_code=500, detail=f"获取定义失败: {str(e)}")


# 统计和监控端点
@router.get("/stats")
async def get_workflow_stats(session: AsyncSession = Depends(get_session)):
    """获取工作流统计信息"""
    try:
        from ..tasks.orchestrator import orchestrator

        total_workflows = len(orchestrator.workflows)
        active_executions = len(
            [
                execution
                for execution in orchestrator.executions.values()
                if execution.status.value in ["initialized", "running"]
            ]
        )
        completed_executions = len(
            [
                execution
                for execution in orchestrator.executions.values()
                if execution.status.value == "completed"
            ]
        )
        failed_executions = len(
            [
                execution
                for execution in orchestrator.executions.values()
                if execution.status.value == "failed"
            ]
        )

        stats = {
            "total_workflows": total_workflows,
            "total_executions": len(orchestrator.executions),
            "active_executions": active_executions,
            "completed_executions": completed_executions,
            "failed_executions": failed_executions,
            "success_rate": (
                completed_executions / len(orchestrator.executions) * 100
                if len(orchestrator.executions) > 0
                else 0
            ),
        }

        return BaseResponse(success=True, message="统计信息获取成功", data=stats)

    except Exception as e:
        logger.error(f"获取工作流统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"统计获取失败: {str(e)}")


logger.info("工作流API模块已加载")
