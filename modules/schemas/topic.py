"""
主题Schema定义

定义主题相关的所有数据模式。
"""

from typing import Any, Dict, List, Optional

from pydantic import Field, validator

from .base import BaseSchema, TimestampMixin
from .enums import TopicStatus


class TopicSchema(BaseSchema, TimestampMixin):
    """主题基础Schema"""

    id: Optional[int] = Field(default=None, description="主题ID")
    name: str = Field(min_length=1, max_length=200, description="主题名称")
    description: Optional[str] = Field(default="", max_length=1000, description="主题描述")
    status: TopicStatus = Field(default=TopicStatus.ACTIVE, description="主题状态")
    category: Optional[str] = Field(default=None, max_length=100, description="主题分类")
    user_id: Optional[int] = Field(default=None, description="用户ID")
    conversation_id: Optional[str] = Field(default=None, description="对话ID")
    parent_topic_id: Optional[int] = Field(default=None, description="父主题ID")
    settings: Dict[str, Any] = Field(default_factory=dict, description="主题设置")

    @validator("name")
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError("主题名称不能为空")
        return v.strip()


class TopicCreate(BaseSchema):
    """创建主题请求Schema"""

    name: str = Field(min_length=1, max_length=200, description="主题名称")
    description: Optional[str] = Field(default="", max_length=1000, description="主题描述")
    category: Optional[str] = Field(default=None, max_length=100, description="主题分类")
    status: Optional[TopicStatus] = Field(default=TopicStatus.ACTIVE, description="主题状态")
    topic_status: Optional[TopicStatus] = Field(
        default=None, description="主题状态(兼容字段)", exclude=True
    )
    user_id: Optional[int] = Field(default=None, description="用户ID", example=12345)

    @validator("status", pre=True, always=True)
    def set_status_from_topic_status(cls, v, values):
        """兼容topic_status字段"""
        # 如果topic_status有值但status没有值，使用topic_status的值
        if "topic_status" in values and values["topic_status"] and not v:
            return values["topic_status"]
        return v or TopicStatus.ACTIVE

    conversation_id: Optional[str] = Field(default=None, description="对话ID")
    parent_topic_id: Optional[int] = Field(default=None, description="父主题ID")
    settings: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="主题设置",
        example={
            "auto_process": True,
            "notification_enabled": True,
            "privacy_level": "public",
            "tags": ["machine-learning", "algorithms", "research"],
        },
    )


class TopicUpdate(BaseSchema):
    """更新主题请求Schema"""

    name: Optional[str] = Field(default=None, min_length=1, max_length=200, description="主题名称")
    description: Optional[str] = Field(default=None, max_length=1000, description="主题描述")
    status: Optional[TopicStatus] = Field(default=None, description="主题状态")
    category: Optional[str] = Field(default=None, max_length=100, description="主题分类")
    settings: Optional[Dict[str, Any]] = Field(default=None, description="主题设置")


class TopicResponse(TopicSchema):
    """主题响应Schema"""

    id: int = Field(description="主题ID")
    file_count: Optional[int] = Field(default=0, description="文件数量")
    document_count: Optional[int] = Field(default=0, description="文档数量")


class TopicList(BaseSchema):
    """主题列表Schema"""

    topics: List[TopicResponse] = Field(description="主题列表")
    total: int = Field(description="总数量")
    page: int = Field(description="当前页")
    page_size: int = Field(description="每页大小")
    total_pages: int = Field(description="总页数")
