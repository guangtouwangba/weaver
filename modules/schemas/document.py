"""
文档Schema定义

定义文档和文档块相关的所有数据模式。
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator

from modules.schemas.base import BaseSchema, TimestampMixin
from modules.schemas.enums import ContentType


class Document(BaseModel):
    """
    document schema for domain layer
    """

    id: str
    title: str
    content: str
    content_type: ContentType
    file_path: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class DocumentSchema(BaseSchema, TimestampMixin):
    """文档基础Schema"""

    id: Optional[str] = Field(default=None, description="文档ID")
    title: str = Field(min_length=1, max_length=500, description="文档标题")
    content: Optional[str] = Field(default=None, description="文档内容")
    content_type: ContentType = Field(description="内容类型")
    file_id: Optional[str] = Field(default=None, description="关联文件ID")
    file_path: Optional[str] = Field(default=None, description="文件路径")
    file_size: int = Field(ge=0, default=0, description="文件大小")
    status: str = Field(default="pending", description="文档状态")
    doc_metadata: Dict[str, Any] = Field(default_factory=dict, description="文档元数据")

    @validator("title")
    def validate_title(cls, v):
        if not v or not v.strip():
            raise ValueError("文档标题不能为空")
        return v.strip()


class DocumentCreate(BaseSchema):
    """创建文档请求Schema"""

    id: str = Field(description="文档ID")
    title: str = Field(min_length=1, max_length=500, description="文档标题")
    content: Optional[str] = Field(default=None, description="文档内容")
    content_type: ContentType = Field(description="内容类型")
    file_id: Optional[str] = Field(default=None, description="关联文件ID")
    file_path: Optional[str] = Field(default=None, description="文件路径")
    file_size: Optional[int] = Field(default=0, ge=0, description="文件大小")
    doc_metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="文档元数据"
    )


class DocumentUpdate(BaseSchema):
    """更新文档请求Schema"""

    title: Optional[str] = Field(
        default=None, min_length=1, max_length=500, description="文档标题"
    )
    content: Optional[str] = Field(default=None, description="文档内容")
    status: Optional[str] = Field(default=None, description="文档状态")
    doc_metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="文档元数据"
    )


class DocumentResponse(DocumentSchema):
    """文档响应Schema"""

    id: str = Field(description="文档ID")
    chunk_count: Optional[int] = Field(default=0, description="文档块数量")


class DocumentChunkSchema(BaseSchema, TimestampMixin):
    """文档块基础Schema"""

    id: Optional[str] = Field(default=None, description="文档块ID")
    document_id: str = Field(description="所属文档ID")
    content: str = Field(min_length=1, description="块内容")
    chunk_index: int = Field(ge=0, description="块索引")
    start_char: Optional[int] = Field(default=None, ge=0, description="开始字符位置")
    end_char: Optional[int] = Field(default=None, ge=0, description="结束字符位置")
    embedding_vector: Optional[List[float]] = Field(
        default=None, description="嵌入向量"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="块元数据")


class DocumentChunkCreate(BaseSchema):
    """创建文档块请求Schema"""

    document_id: str = Field(description="所属文档ID")
    content: str = Field(min_length=1, description="块内容")
    chunk_index: int = Field(ge=0, description="块索引")
    start_char: Optional[int] = Field(default=None, ge=0, description="开始字符位置")
    end_char: Optional[int] = Field(default=None, ge=0, description="结束字符位置")
    chunk_id: Optional[str] = Field(default=None, description="自定义块ID")
    embedding_vector: Optional[List[float]] = Field(
        default=None, description="嵌入向量"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="块元数据"
    )


class DocumentChunkResponse(DocumentChunkSchema):
    """文档块响应Schema"""

    id: str = Field(description="文档块ID")


# 为兼容性创建别名
DocumentChunk = DocumentChunkSchema


class DocumentList(BaseSchema):
    """文档列表Schema"""

    documents: List[DocumentResponse] = Field(description="文档列表")
    total: int = Field(description="总数量")
    page: int = Field(description="当前页")
    page_size: int = Field(description="每页大小")
    total_pages: int = Field(description="总页数")


def create_document_from_path(
    file_path: str, content: str, content_type: str = "text", original_filename: str = None
) -> Document:
    """从文件路径创建文档对象"""
    import os
    from uuid import uuid4

    document_id = str(uuid4())
    # 使用原始文件名作为标题，如果没有提供则使用文件路径的basename
    title = original_filename if original_filename else os.path.basename(file_path)

    # 根据文件扩展名推断内容类型
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        doc_content_type = ContentType.PDF
    elif ext == ".doc":
        doc_content_type = ContentType.DOC
    elif ext == ".docx":
        doc_content_type = ContentType.DOCX
    elif ext == ".txt":
        doc_content_type = ContentType.TXT
    elif ext == ".html":
        doc_content_type = ContentType.HTML
    elif ext == ".md":
        doc_content_type = ContentType.MD
    elif ext == ".json":
        doc_content_type = ContentType.JSON
    elif ext == ".csv":
        doc_content_type = ContentType.CSV
    else:
        doc_content_type = ContentType.TXT  # 默认为文本

    return Document(
        id=document_id,
        title=title,
        content=content,
        content_type=doc_content_type,
        file_path=file_path,
        metadata={"original_path": file_path, "file_size": len(content)},
    )
