"""
基础Schema定义

提供所有Schema的基础类和通用字段。
"""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class BaseSchema(BaseModel):
    """基础Schema类"""

    model_config = ConfigDict(
        # 允许从ORM对象创建
        from_attributes=True,
        # 使用枚举值而不是枚举名称
        use_enum_values=True,
        # 验证赋值
        validate_assignment=True,
        # 允许额外字段（用于扩展）
        extra="forbid",
    )


class TimestampMixin(BaseModel):
    """时间戳混入类"""

    created_at: Optional[datetime] = Field(default=None, description="创建时间")
    updated_at: Optional[datetime] = Field(default=None, description="更新时间")


class PaginationSchema(BaseModel):
    """分页Schema"""

    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页大小")
    total: Optional[int] = Field(default=None, description="总数量")
    total_pages: Optional[int] = Field(default=None, description="总页数")


class ErrorSchema(BaseModel):
    """错误信息Schema"""

    error_code: str = Field(description="错误代码")
    error_message: str = Field(description="错误消息")
    details: Optional[Dict[str, Any]] = Field(default=None, description="错误详情")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="错误时间")
