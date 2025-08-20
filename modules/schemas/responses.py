"""
响应Schema定义

定义所有API响应的数据模式。
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import Field

from .base import BaseSchema, PaginationSchema
from .enums import ProcessingStatus
from .document import DocumentChunkResponse

class ProcessingResult(BaseSchema):
    """处理结果Schema"""
    
    document_id: str = Field(description="文档ID")
    status: ProcessingStatus = Field(description="处理状态")
    chunks_created: int = Field(
        ge=0,
        description="创建的文档块数量"
    )
    processing_time: Optional[float] = Field(
        default=None,
        description="处理时间（秒）"
    )
    error_message: Optional[str] = Field(
        default=None,
        description="错误信息"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="处理元数据"
    )

class SearchResult(BaseSchema):
    """搜索结果项Schema"""
    
    document_id: str = Field(description="文档ID")
    chunk_id: Optional[str] = Field(
        default=None,
        description="文档块ID"
    )
    title: str = Field(description="文档标题")
    content: str = Field(description="匹配内容")
    score: float = Field(
        ge=0.0,
        le=1.0,
        description="相关性得分"
    )
    content_type: str = Field(description="内容类型")
    file_id: Optional[str] = Field(
        default=None,
        description="来源文件ID"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="结果元数据"
    )

class SearchResponse(BaseSchema):
    """搜索响应Schema"""
    
    query: str = Field(description="搜索查询")
    results: List[SearchResult] = Field(description="搜索结果")
    total_results: int = Field(
        ge=0,
        description="总结果数"
    )
    search_time: float = Field(
        ge=0.0,
        description="搜索耗时（秒）"
    )
    search_type: str = Field(description="搜索类型")

class OrchestrationResult(BaseSchema):
    """编排结果Schema"""
    
    file_id: str = Field(description="文件ID")
    document_id: Optional[str] = Field(
        default=None,
        description="文档ID"
    )
    status: ProcessingStatus = Field(description="编排状态")
    processing_result: Optional[ProcessingResult] = Field(
        default=None,
        description="处理结果"
    )
    indexing_result: Optional[Dict[str, Any]] = Field(
        default=None,
        description="索引结果"
    )
    total_time: Optional[float] = Field(
        default=None,
        description="总耗时（秒）"
    )
    error_message: Optional[str] = Field(
        default=None,
        description="错误信息"
    )

class UploadUrlResponse(BaseSchema):
    """上传URL响应Schema"""
    
    upload_url: str = Field(description="上传URL")
    file_id: str = Field(description="文件ID")
    expires_at: datetime = Field(description="过期时间")
    upload_fields: Optional[Dict[str, str]] = Field(
        default=None,
        description="上传字段"
    )

class ConfirmUploadResponse(BaseSchema):
    """确认上传响应Schema"""
    
    file_id: str = Field(description="文件ID")
    status: str = Field(description="文件状态")
    processing_queued: bool = Field(description="是否已排队处理")
    estimated_processing_time: Optional[int] = Field(
        default=None,
        description="预计处理时间（秒）"
    )

class HealthCheckResponse(BaseSchema):
    """健康检查响应Schema"""
    
    status: str = Field(description="服务状态")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="检查时间"
    )
    version: str = Field(description="服务版本")
    components: Dict[str, str] = Field(
        default_factory=dict,
        description="组件状态"
    )

class PaginatedResponse(BaseSchema):
    """分页响应基类Schema"""
    
    pagination: PaginationSchema = Field(description="分页信息")

class APIResponse(BaseSchema):
    """API通用响应Schema"""
    
    success: bool = Field(description="请求是否成功")
    message: Optional[str] = Field(
        default=None,
        description="响应消息"
    )
    data: Optional[Any] = Field(
        default=None,
        description="响应数据"
    )
    error: Optional[Dict[str, Any]] = Field(
        default=None,
        description="错误信息"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="响应时间"
    )
