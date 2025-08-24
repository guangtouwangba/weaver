"""
转换器

提供SQLAlchemy模型与Pydantic Schema之间的转换功能。
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from modules.database.models import Document as DocumentModel
from modules.database.models import File as FileModel
from modules.database.models import Topic as TopicModel
from modules.schemas.document import DocumentResponse, DocumentSchema
from modules.schemas.file import FileResponse, FileSchema
from modules.schemas.topic import TopicResponse, TopicSchema


# Topic转换器
def topic_to_schema(
    topic_model: TopicModel, include_stats: bool = False
) -> TopicSchema:
    """将SQLAlchemy Topic模型转换为Pydantic Schema"""
    schema_data = {
        "id": topic_model.id,
        "name": topic_model.name,
        "description": topic_model.description or "",
        "status": topic_model.status,
        "category": topic_model.category,
        "user_id": topic_model.user_id,
        "conversation_id": topic_model.conversation_id,
        "parent_topic_id": topic_model.parent_topic_id,
        "settings": topic_model.settings or {},
        "created_at": topic_model.created_at,
        "updated_at": topic_model.updated_at,
    }

    if include_stats:
        # 如果需要统计信息，转换为TopicResponse
        schema_data.update(
            {
                "file_count": (
                    len(topic_model.files)
                    if hasattr(topic_model, "files") and topic_model.files
                    else 0
                ),
                "document_count": 0,  # 需要额外查询或计算
            }
        )
        return TopicResponse(**schema_data)

    return TopicSchema(**schema_data)


def topic_to_response(
    topic_model: TopicModel, file_count: int = 0, document_count: int = 0
) -> TopicResponse:
    """将SQLAlchemy Topic模型转换为响应Schema"""
    return TopicResponse(
        id=topic_model.id,
        name=topic_model.name,
        description=topic_model.description or "",
        status=topic_model.status,
        category=topic_model.category,
        user_id=topic_model.user_id,
        conversation_id=topic_model.conversation_id,
        parent_topic_id=topic_model.parent_topic_id,
        settings=topic_model.settings or {},
        created_at=topic_model.created_at,
        updated_at=topic_model.updated_at,
        file_count=file_count,
        document_count=document_count,
    )


def schema_to_topic_dict(schema: TopicSchema) -> Dict[str, Any]:
    """将Pydantic Topic Schema转换为字典（用于SQLAlchemy创建）"""
    data = schema.model_dump(
        exclude={"id", "created_at", "updated_at"}, exclude_none=True
    )
    return data


# File转换器
def file_to_schema(
    file_model: FileModel, include_topic_name: bool = False
) -> FileSchema:
    """将SQLAlchemy File模型转换为Pydantic Schema"""
    schema_data = {
        "id": file_model.id,
        "original_name": file_model.original_name,
        "content_type": file_model.content_type,
        "file_size": file_model.file_size,
        "file_hash": file_model.file_hash,
        "storage_bucket": file_model.storage_bucket,
        "storage_key": file_model.storage_key,
        "storage_url": file_model.storage_url,
        "status": file_model.status,
        "processing_status": getattr(file_model, "processing_status", None),
        "error_message": getattr(file_model, "error_message", None),
        "topic_id": file_model.topic_id,
        "user_id": getattr(file_model, "user_id", None),
        "is_deleted": file_model.is_deleted,
        "file_metadata": getattr(file_model, "file_metadata", {}),
        "created_at": file_model.created_at,
        "updated_at": file_model.updated_at,
    }

    if include_topic_name:
        # 如果需要主题名称，转换为FileResponse
        topic_name = (
            file_model.topic.name
            if hasattr(file_model, "topic") and file_model.topic
            else None
        )
        schema_data["topic_name"] = topic_name
        return FileResponse(**schema_data)

    return FileSchema(**schema_data)


def file_to_response(
    file_model: FileModel, topic_name: Optional[str] = None
) -> FileResponse:
    """将SQLAlchemy File模型转换为响应Schema"""
    if topic_name is None and hasattr(file_model, "topic") and file_model.topic:
        topic_name = file_model.topic.name

    return FileResponse(
        id=file_model.id,
        original_name=file_model.original_name,
        content_type=file_model.content_type,
        file_size=file_model.file_size,
        file_hash=file_model.file_hash,
        storage_bucket=file_model.storage_bucket,
        storage_key=file_model.storage_key,
        storage_url=file_model.storage_url,
        status=file_model.status,
        processing_status=getattr(file_model, "processing_status", None),
        error_message=getattr(file_model, "error_message", None),
        topic_id=file_model.topic_id,
        user_id=getattr(file_model, "user_id", None),
        is_deleted=file_model.is_deleted,
        file_metadata=getattr(file_model, "file_metadata", {}),
        created_at=file_model.created_at,
        updated_at=file_model.updated_at,
        topic_name=topic_name,
    )


def schema_to_file_dict(schema: FileSchema) -> Dict[str, Any]:
    """将Pydantic File Schema转换为字典（用于SQLAlchemy创建）"""
    data = schema.model_dump(exclude={"created_at", "updated_at"}, exclude_none=True)
    # Field names are now standardized, no renaming needed for file metadata
    return data


# Document转换器
def document_to_schema(
    document_model: DocumentModel, include_chunk_count: bool = False
) -> DocumentSchema:
    """将SQLAlchemy Document模型转换为Pydantic Schema"""
    schema_data = {
        "id": document_model.id,
        "title": document_model.title,
        "content": document_model.content,
        "content_type": document_model.content_type,
        "file_id": document_model.file_id,
        "file_path": document_model.file_path,
        "file_size": document_model.file_size,
        "status": document_model.status,
        "doc_metadata": document_model.doc_metadata or {},
        "created_at": document_model.created_at,
        "updated_at": document_model.updated_at,
    }

    if include_chunk_count:
        # 如果需要块数量，转换为DocumentResponse
        chunk_count = (
            len(document_model.chunks)
            if hasattr(document_model, "chunks") and document_model.chunks
            else 0
        )
        schema_data["chunk_count"] = chunk_count
        return DocumentResponse(**schema_data)

    return DocumentSchema(**schema_data)


def document_to_response(
    document_model: DocumentModel, chunk_count: int = 0
) -> DocumentResponse:
    """将SQLAlchemy Document模型转换为响应Schema"""
    if chunk_count == 0 and hasattr(document_model, "chunks") and document_model.chunks:
        chunk_count = len(document_model.chunks)

    return DocumentResponse(
        id=document_model.id,
        title=document_model.title,
        content=document_model.content,
        content_type=document_model.content_type,
        file_id=document_model.file_id,
        file_path=document_model.file_path,
        file_size=document_model.file_size,
        status=document_model.status,
        doc_metadata=document_model.doc_metadata or {},
        created_at=document_model.created_at,
        updated_at=document_model.updated_at,
        chunk_count=chunk_count,
    )


def schema_to_document_dict(schema: DocumentSchema) -> Dict[str, Any]:
    """将Pydantic Document Schema转换为字典（用于SQLAlchemy创建）"""
    data = schema.model_dump(
        exclude={"id", "created_at", "updated_at"}, exclude_none=True
    )
    # Field names are now standardized, no renaming needed for most fields
    # Note: doc_metadata still needs mapping until database model is updated
    if "doc_metadata" in data:
        data["doc_metadata"] = data["doc_metadata"]  # Keep as-is for now
    return data


# 批量转换器
def topics_to_responses(topic_models: List[TopicModel]) -> List[TopicResponse]:
    """批量转换主题模型为响应Schema"""
    return [topic_to_response(topic) for topic in topic_models]


def files_to_responses(file_models: List[FileModel]) -> List[FileResponse]:
    """批量转换文件模型为响应Schema"""
    return [file_to_response(file) for file in file_models]


def documents_to_responses(
    document_models: List[DocumentModel],
) -> List[DocumentResponse]:
    """批量转换文档模型为响应Schema"""
    return [document_to_response(doc) for doc in document_models]


# DocumentChunk转换器
def schema_to_document_chunk_dict(
    schema: Dict[str, Any]
) -> Dict[str, Any]:
    """将DocumentChunk Schema转换为字典（用于SQLAlchemy创建）"""
    data = schema.copy()
    # Map metadata field to chunk_metadata for database model
    if "metadata" in data:
        data["chunk_metadata"] = data.pop("metadata")
    return data


def document_chunk_to_schema_dict(chunk_model) -> Dict[str, Any]:
    """将SQLAlchemy DocumentChunk模型转换为Schema字典"""
    data = {
        "id": chunk_model.id,
        "document_id": chunk_model.document_id,
        "content": chunk_model.content,
        "chunk_index": chunk_model.chunk_index,
        "start_char": chunk_model.start_char,
        "end_char": chunk_model.end_char,
        "embedding_vector": getattr(chunk_model, "embedding_vector", None),
        # Map chunk_metadata back to metadata for schema
        "metadata": chunk_model.chunk_metadata or {},
        "created_at": getattr(chunk_model, "created_at", None),
    }
    return data
