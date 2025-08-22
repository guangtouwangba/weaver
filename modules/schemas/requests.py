"""
请求Schema定义

定义所有API请求的数据模式。
"""

from typing import Any, Dict, List, Optional

from pydantic import Field

from .base import BaseSchema
from .enums import ChunkingStrategy, ContentType, ProcessingStatus, SearchType


class FileLoadRequest(BaseSchema):
    """文件加载请求Schema"""

    file_path: str = Field(description="文件路径")
    content_type: ContentType = Field(description="内容类型")
    file_id: Optional[str] = Field(default=None, description="文件ID")
    user_id: Optional[int] = Field(default=None, description="用户ID")
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="元数据"
    )


class ProcessingRequest(BaseSchema):
    """处理请求Schema"""

    document_id: str = Field(description="文档ID")
    chunking_strategy: ChunkingStrategy = Field(
        default=ChunkingStrategy.FIXED_SIZE, description="分块策略"
    )
    chunk_size: int = Field(default=512, ge=1, le=8192, description="块大小")
    chunk_overlap: int = Field(default=50, ge=0, description="块重叠大小")
    enable_embedding: bool = Field(default=True, description="是否生成嵌入向量")
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="处理元数据"
    )


class SearchRequest(BaseSchema):
    """搜索请求Schema"""

    query: str = Field(
        min_length=1,
        description="搜索查询",
        example="机器学习中的决策树算法原理是什么？",
    )
    search_type: SearchType = Field(default=SearchType.SEMANTIC, description="搜索类型")
    limit: int = Field(
        default=10, ge=1, le=100, description="返回结果数量限制", example=5
    )
    content_type: Optional[ContentType] = Field(
        default=None, description="内容类型过滤"
    )
    topic_id: Optional[int] = Field(default=None, description="主题ID过滤", example=123)
    file_id: Optional[str] = Field(default=None, description="文件ID过滤")
    metadata_filters: Optional[Dict[str, Any]] = Field(
        default=None,
        description="元数据过滤器",
        example={
            "author": "Zhang San",
            "created_date_range": {"start": "2024-01-01", "end": "2024-12-31"},
            "tags": ["machine-learning", "algorithms"],
        },
    )


class OrchestrationRequest(BaseSchema):
    """编排请求Schema"""

    file_id: str = Field(description="文件ID")
    processing_config: ProcessingRequest = Field(description="处理配置")
    auto_index: bool = Field(default=True, description="是否自动索引")
    callback_url: Optional[str] = Field(default=None, description="回调URL")


class UploadUrlRequest(BaseSchema):
    """上传URL请求Schema"""

    filename: str = Field(
        min_length=1, description="文件名", example="machine_learning_algorithms.pdf"
    )
    content_type: str = Field(description="内容类型", example="application/pdf")
    file_size: Optional[int] = Field(
        default=None, ge=0, description="文件大小", example=2048576
    )
    topic_id: Optional[int] = Field(default=None, description="主题ID", example=123)
    access_level: Optional[str] = Field(default="private", description="访问级别")
    expires_in_hours: Optional[int] = Field(
        default=24, ge=1, le=168, description="过期时间（小时）"  # 最多7天
    )
    category: Optional[str] = Field(
        default=None, max_length=100, description="文件分类", example="学术论文"
    )
    tags: Optional[List[str]] = Field(default_factory=list, description="文件标签")
    user_id: Optional[int] = Field(default=None, description="用户ID")
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="文件元数据"
    )


class AddResourceRequest(BaseSchema):
    """向主题添加资源请求Schema"""

    file_id: str = Field(description="文件ID", example="file_abc123def456")
    resource_type: Optional[str] = Field(
        default="file", description="资源类型", example="file"
    )
    title: Optional[str] = Field(
        default=None, description="资源标题", example="机器学习算法详解.pdf"
    )
    description: Optional[str] = Field(
        default=None,
        description="资源描述",
        example="关于机器学习核心算法的详细技术文档",
    )
    tags: Optional[List[str]] = Field(
        default_factory=list,
        description="资源标签",
        example=["machine-learning", "algorithm", "pdf"],
    )
    priority: Optional[int] = Field(
        default=0, ge=0, le=10, description="优先级 (0-10)", example=5
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="资源元数据",
        example={"source": "upload", "auto_process": True, "notification": True},
    )


class ConfirmUploadRequest(BaseSchema):
    """确认上传请求Schema"""

    file_id: str = Field(description="文件ID")
    actual_size: int = Field(ge=0, description="实际文件大小")
    file_hash: Optional[str] = Field(default=None, description="文件哈希值")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="附加元数据")
