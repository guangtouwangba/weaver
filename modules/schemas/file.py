"""
文件Schema定义

定义文件相关的所有数据模式。
"""

from typing import Any, Dict, List, Optional

from pydantic import Field, validator

from modules.schemas.base import BaseSchema, TimestampMixin
from modules.schemas.enums import FileStatus


class FileSchema(BaseSchema, TimestampMixin):
    """文件基础Schema"""

    id: Optional[str] = Field(default=None, description="文件ID")
    original_name: str = Field(min_length=1, max_length=255, description="原始文件名")
    content_type: str = Field(description="文件内容类型")
    file_size: int = Field(ge=0, description="文件大小（字节）")
    file_hash: Optional[str] = Field(default=None, description="文件哈希值")
    storage_bucket: Optional[str] = Field(default=None, description="存储桶名称")
    storage_key: Optional[str] = Field(default=None, description="存储键名")
    storage_url: Optional[str] = Field(default=None, description="存储URL")
    status: FileStatus = Field(default=FileStatus.UPLOADING, description="文件状态")
    processing_status: Optional[str] = Field(default=None, description="处理状态")
    error_message: Optional[str] = Field(default=None, description="错误信息")
    topic_id: Optional[int] = Field(default=None, description="所属主题ID")
    user_id: Optional[int] = Field(default=None, description="上传用户ID")
    is_deleted: bool = Field(default=False, description="是否已删除")
    file_metadata: Dict[str, Any] = Field(
        default_factory=dict, description="文件元数据"
    )

    @validator("original_name")
    def validate_original_name(cls, v):
        if not v or not v.strip():
            raise ValueError("文件名不能为空")
        return v.strip()


class FileCreate(BaseSchema):
    """创建文件请求Schema"""

    id: str = Field(description="文件ID")
    original_name: str = Field(min_length=1, max_length=255, description="原始文件名")
    content_type: str = Field(description="文件内容类型")
    file_size: int = Field(ge=0, description="文件大小（字节）")
    file_hash: Optional[str] = Field(default=None, description="文件哈希值")
    storage_bucket: Optional[str] = Field(default=None, description="存储桶名称")
    storage_key: Optional[str] = Field(default=None, description="存储键名")
    storage_url: Optional[str] = Field(default=None, description="存储URL")
    topic_id: Optional[int] = Field(default=None, description="所属主题ID")
    user_id: Optional[int] = Field(default=None, description="上传用户ID")
    file_metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="文件元数据"
    )


class FileUpdate(BaseSchema):
    """更新文件请求Schema"""

    original_name: Optional[str] = Field(
        default=None, min_length=1, max_length=255, description="原始文件名"
    )
    status: Optional[FileStatus] = Field(default=None, description="文件状态")
    processing_status: Optional[str] = Field(default=None, description="处理状态")
    error_message: Optional[str] = Field(default=None, description="错误信息")
    file_metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="文件元数据"
    )


class FileResponse(FileSchema):
    """文件响应Schema"""

    id: str = Field(description="文件ID")
    topic_name: Optional[str] = Field(default=None, description="所属主题名称")


class FileList(BaseSchema):
    """文件列表Schema"""

    files: List[FileResponse] = Field(description="文件列表")
    total: int = Field(description="总数量")
    page: int = Field(description="当前页")
    page_size: int = Field(description="每页大小")
    total_pages: int = Field(description="总页数")
