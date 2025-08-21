"""
主题API层

使用TopicService进行业务逻辑编排的API接口。
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile, Form
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from ..services import DocumentService
from ..database import get_db_session
from ..services import TopicService, FileService
from ..schemas import (
    TopicCreate, TopicUpdate, TopicResponse, TopicList,
    FileList, APIResponse, AddResourceRequest, FileResponse, FileStatus
)

router = APIRouter(prefix="/topics", tags=["topics"])
logger = logging.getLogger(__name__)

# 依赖注入
async def get_topic_service(session: AsyncSession = Depends(get_db_session)) -> TopicService:
    """获取主题服务实例"""
    return TopicService(session)

async def get_document_service(session: AsyncSession = Depends(get_db_session)) -> DocumentService:
    """获取文档服务实例"""
    return DocumentService(session)

async def get_file_service_for_topic(session: AsyncSession = Depends(get_db_session)) -> FileService:
    """获取文件服务实例（用于主题相关操作）"""
    from ..storage import MinIOStorage  # 使用MinIOStorage作为默认存储
    from config import get_config
    
    config = get_config()
    storage = MinIOStorage(
        endpoint=config.storage.minio_endpoint or "localhost:9000",
        access_key=config.storage.minio_access_key or "minioadmin",
        secret_key=config.storage.minio_secret_key or "minioadmin123",
        secure=config.storage.minio_secure,
        bucket_name=config.storage.bucket_name or "rag-uploads"
    )
    return FileService(session, storage)

@router.post("", response_model=APIResponse, summary="创建知识主题")
async def create_topic(
    topic_data: TopicCreate,
    service: TopicService = Depends(get_topic_service)
):
    """
    # 创建新的知识主题
    
    创建一个新的知识主题，用于组织和管理相关的文档和内容。
    
    ## 请求参数
    - **name**: 主题名称（必填，1-100个字符）
    - **description**: 主题描述（可选，最多500个字符）
    - **category**: 主题分类（可选）
    - **tags**: 标签列表（可选）
    - **user_id**: 创建者ID（可选）
    
    ## 返回结果
    成功创建后返回包含主题ID、创建时间等信息的完整主题数据。
    
    ## 使用场景
    - 建立新的研究主题或项目
    - 组织特定领域的知识内容
    - 为文档上传做准备
    
    ## 注意事项
    - 主题名称在用户范围内必须唯一
    - 创建后可以通过PUT接口更新主题信息
    """
    try:
        topic = await service.create_topic(topic_data)
        return APIResponse(
            success=True,
            message="主题创建成功",
            data=topic
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建主题失败: {str(e)}")

@router.get("/{topic_id}", response_model=APIResponse, summary="获取主题详情")
async def get_topic(
    topic_id: int,
    service: TopicService = Depends(get_topic_service)
):
    """
    # 获取指定主题的详细信息
    
    根据主题ID获取完整的主题信息，包括基本属性、创建时间、最后更新时间等。
    
    ## 路径参数
    - **topic_id**: 主题ID（整数，必填）
    
    ## 返回结果
    返回主题的完整信息，包括:
    - 主题基本信息（名称、描述、分类等）
    - 创建和更新时间戳
    - 主题状态和标签
    - 创建者信息
    
    ## 错误状态
    - **404**: 主题不存在或已被删除
    - **500**: 服务器内部错误
    """
    try:
        topic = await service.get_topic(topic_id)
        if not topic:
            raise HTTPException(status_code=404, detail="主题不存在")
        
        return APIResponse(
            success=True,
            data=topic
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取主题失败: {str(e)}")

@router.put("/{topic_id}", response_model=APIResponse, summary="更新主题信息")
async def update_topic(
    topic_id: int,
    topic_data: TopicUpdate,
    service: TopicService = Depends(get_topic_service)
):
    """
    # 更新指定主题的信息
    
    修改存在的主题信息，支持部分更新（只修改提供的字段）。
    
    ## 路径参数
    - **topic_id**: 主题ID（整数，必填）
    
    ## 请求参数
    所有字段都是可选的，只更新提供的字段:
    - **name**: 新的主题名称
    - **description**: 新的主题描述
    - **category**: 新的主题分类
    - **tags**: 新的标签列表
    - **status**: 新的主题状态
    
    ## 返回结果
    返回更新后的完整主题信息。
    
    ## 错误状态
    - **400**: 请求参数不合法（如名称重复）
    - **404**: 主题不存在
    - **500**: 服务器内部错误
    """
    try:
        topic = await service.update_topic(topic_id, topic_data)
        if not topic:
            raise HTTPException(status_code=404, detail="主题不存在")
        
        return APIResponse(
            success=True,
            message="主题更新成功",
            data=topic
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新主题失败: {str(e)}")

@router.delete("/{topic_id}", response_model=APIResponse, summary="删除主题")
async def delete_topic(
    topic_id: int,
    service: TopicService = Depends(get_topic_service)
):
    """
    # 删除指定的主题
    
    完全删除一个主题及其相关的所有数据。
    
    ## 路径参数
    - **topic_id**: 要删除的主题ID（整数，必填）
    
    ## 删除范围
    删除操作将移除:
    - 主题的基本信息
    - 与主题关联的文件引用（不删除实际文件）
    - 主题相关的文档处理结果
    
    ## 警告
    ⚠️ **此操作不可逆！**一旦删除，主题及其相关数据将无法恢复。
    
    ## 建议
    在执行删除操作之前:
    1. 检查主题下是否有重要文档
    2. 考虑使用更新接口将状态改为“已归档”
    3. 备份相关数据
    
    ## 错误状态
    - **404**: 主题不存在或已被删除
    - **400**: 主题正在被使用，无法删除
    - **500**: 服务器内部错误
    """
    try:
        success = await service.delete_topic(topic_id)
        if not success:
            raise HTTPException(status_code=404, detail="主题不存在")
        
        return APIResponse(
            success=True,
            message="主题删除成功"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除主题失败: {str(e)}")

@router.get("", response_model=APIResponse, summary="获取主题列表")
async def list_topics(
    page: int = Query(1, ge=1, description="页码，从1开始"),
    page_size: int = Query(20, ge=1, le=100, description="每页返回的主题数量，1-100之间"),
    status: Optional[str] = Query(None, description="按状态过滤（active/archived/draft）"),
    user_id: Optional[int] = Query(None, description="按创建者ID过滤"),
    category: Optional[str] = Query(None, description="按分类过滤"),
    service: TopicService = Depends(get_topic_service)
):
    """
    # 获取主题列表（支持分页和过滤）
    
    获取系统中所有主题的列表，支持多种过滤条件和分页显示。
    
    ## 查询参数
    - **page**: 页码（默认为1）
    - **page_size**: 每页数量（默认为20，最多100）
    - **status**: 状态过滤，可选值:
      - `active`: 活跃主题
      - `archived`: 已归档主题
      - `draft`: 草稿状态
    - **user_id**: 按创建者过滤
    - **category**: 按分类过滤
    
    ## 返回结果
    返回分页后的主题列表，包含:
    - **items**: 主题数据列表
    - **pagination**: 分页信息（总数、当前页、总页数等）
    - **total**: 符合条件的主题总数
    
    ## 使用示例
    ```
    GET /api/v1/topics?page=1&page_size=10&status=active
    GET /api/v1/topics?category=研究&user_id=123
    ```
    
    ## 排序规则
    默认按创建时间倒序排列（最新的在前）。
    """
    try:
        topic_list = await service.list_topics(
            page=page,
            page_size=page_size,
            status=status,
            user_id=user_id,
            category=category
        )
        
        return APIResponse(
            success=True,
            data=topic_list
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取主题列表失败: {str(e)}")

@router.get("/{topic_id}/files", response_model=APIResponse, summary="获取主题的文件列表")
async def get_topic_files(
    topic_id: int,
    page: int = Query(1, ge=1, description="页码，从1开始"),
    page_size: int = Query(20, ge=1, le=100, description="每页返回的文件数量"),
    sort_by: str = Query("created_at", description="排序字段（created_at/updated_at/name/size）"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="排序方向（asc:升序，desc:降序）"),
    service: FileService = Depends(get_file_service_for_topic)
):
    """
    # 获取指定主题下的所有文件
    
    查询与特定主题关联的所有文件，支持分页和自定义排序。
    
    ## 路径参数
    - **topic_id**: 主题ID（整数，必填）
    
    ## 查询参数
    - **page**: 页码（默认为1）
    - **page_size**: 每页数量（默认为20）
    - **sort_by**: 排序字段，支持:
      - `created_at`: 创建时间（默认）
      - `updated_at`: 更新时间
      - `name`: 文件名
      - `size`: 文件大小
    - **sort_order**: 排序方向（asc/desc，默认desc）
    
    ## 返回结果
    返回文件列表，包含:
    - 文件基本信息（ID、名称、大小、类型）
    - 上传和处理状态
    - 存储位置和访问链接
    - 分页信息
    
    ## 使用场景
    - 浏览主题下的所有文档
    - 管理和组织主题内容
    - 批量操作相关文件
    
    ## 错误状态
    - **400**: 请求参数不合法
    - **404**: 主题不存在
    - **500**: 服务器内部错误
    """
    try:
        file_list = await service.get_topic_files(
            topic_id=topic_id, 
            page=page, 
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        return APIResponse(
            success=True,
            data=file_list,
            message=f"获取主题{topic_id}的文件列表成功"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取主题文件失败: {str(e)}")

@router.get("/search", response_model=APIResponse, summary="搜索主题")
async def search_topics(
    q: str = Query(..., min_length=1, description="搜索关键词，在主题名称和描述中查找"),
    limit: int = Query(10, ge=1, le=100, description="返回结果的数量上限"),
    service: TopicService = Depends(get_topic_service)
):
    """
    # 全文搜索主题
    
    根据关键词在主题名称和描述中进行模糊搜索，并按照相关度排序返回结果。
    
    ## 查询参数
    - **q**: 搜索关键词（必填，至少1个字符）
    - **limit**: 结果数量限制（默认为10，最多100）
    
    ## 搜索范围
    系统将在以下字段中搜索:
    - 主题名称（权重最高）
    - 主题描述
    - 主题标签
    - 主题分类
    
    ## 返回结果
    返回按相关度排序的主题列表，每个结果包含:
    - 主题基本信息
    - 匹配的关键字片段（高亮显示）
    - 相关度得分
    
    ## 搜索特性
    - 支持中文分词和英文全文搜索
    - 自动匹配同义词和相关词
    - 支持部分匹配和模糊查询
    
    ## 使用示例
    ```
    GET /api/v1/topics/search?q=机器学习&limit=5
    GET /api/v1/topics/search?q=python数据分析
    ```
    """
    try:
        topics = await service.search_topics(q, limit)
        
        return APIResponse(
            success=True,
            data=topics
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索主题失败: {str(e)}")

@router.get("/users/{user_id}/topics", response_model=APIResponse, summary="获取用户的主题列表")
async def get_user_topics(
    user_id: int,
    service: TopicService = Depends(get_topic_service)
):
    """
    # 获取指定用户创建的所有主题
    
    查询特定用户创建的所有主题，按创建时间倒序排列。
    
    ## 路径参数
    - **user_id**: 用户ID（整数，必填）
    
    ## 返回结果
    返回该用户创建的所有主题列表，包括:
    - 主题基本信息
    - 创建和更新时间
    - 主题状态和分类
    - 与主题关联的文件数量
    
    ## 使用场景
    - 用户个人主题管理页面
    - 管理员统计用户活跃度
    - 用户作品展示页面
    
    ## 注意事项
    - 只返回该用户创建的主题
    - 不包含用户参与但非创建者的主题
    - 返回结果按创建时间倒序排列
    
    ## 错误状态
    - **404**: 用户不存在
    - **500**: 服务器内部错误
    """
    try:
        topics = await service.get_user_topics(user_id)
        
        return APIResponse(
            success=True,
            data=topics
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户主题失败: {str(e)}")

@router.post("/{topic_id}/resources", response_model=APIResponse, summary="向主题添加资源")
async def add_resource_to_topic(
    topic_id: int,
    resource_data: AddResourceRequest,
    service: TopicService = Depends(get_topic_service)
):
    """
    # 向指定主题添加资源（文件）
    
    将已上传的文件关联到特定主题，建立主题与文件之间的关联关系。这是文件上传后的重要步骤。
    
    ## 路径参数
    - **topic_id**: 目标主题ID（整数，必填）
    
    ## 请求参数
    - **file_id**: 文件ID（必填，来自文件上传接口）
    - **resource_type**: 资源类型（可选，默认为"file"）
    - **title**: 资源标题（可选，如果提供会更新文件显示名称）
    - **description**: 资源描述（可选）
    - **tags**: 资源标签列表（可选）
    - **priority**: 优先级0-10（可选，默认为0）
    - **metadata**: 扩展元数据（可选）
    
    ## 业务逻辑
    1. **验证主题存在**: 检查目标主题是否存在且可访问
    2. **验证文件存在**: 确认文件已成功上传且可用
    3. **关联更新**: 更新文件的topic_id字段建立关联
    4. **可选更新**: 如果提供了title，会更新文件的显示名称
    5. **冲突处理**: 如果文件已关联到其他主题，会进行覆盖更新
    
    ## 使用场景
    - 文件上传完成后建立主题关联
    - 将现有文件重新分配到不同主题
    - 批量整理和组织文档资源
    
    ## 返回结果
    返回更新后的文件信息，包含新的主题关联关系。
    
    ## 错误处理
    - **400**: 请求参数错误或业务规则违反
    - **404**: 主题或文件不存在
    - **500**: 服务器处理错误
    
    ## 注意事项
    - 一个文件只能关联到一个主题
    - 如果文件已有主题关联，新关联会覆盖旧的
    - 资源添加成功后，可以在主题的文件列表中查看
    """
    try:
        file_response = await service.add_resource_to_topic(topic_id, resource_data)
        
        return APIResponse(
            success=True,
            message=f"成功将资源添加到主题 {topic_id}",
            data=file_response
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"添加资源失败: {str(e)}")

@router.post("/{topic_id}/upload", response_model=APIResponse, summary="上传文件到主题")
async def upload_file_to_topic(
    topic_id: int,
    file: UploadFile = File(..., description="要上传的文件"),
    title: Optional[str] = Form(None, description="文件标题"),
    description: Optional[str] = Form(None, description="文件描述"),
    resource_type: Optional[str] = Form("file", description="资源类型"),
    tags: Optional[str] = Form(None, description="标签，用逗号分隔"),
    is_public: Optional[bool] = Form(False, description="是否公开"),
    priority: Optional[int] = Form(0, description="优先级(0-10)"),
    topic_service: TopicService = Depends(get_topic_service),
    document_service: DocumentService = Depends(get_document_service)
):
    """
    # 上传文件并直接关联到主题
    
    支持multipart/form-data格式的文件上传，直接将文件关联到指定主题。
    这是一个组合操作，包含文件上传和资源关联两个步骤。
    
    ## 路径参数
    - **topic_id**: 目标主题ID（整数）
    
    ## 请求格式
    使用multipart/form-data格式，支持以下字段：
    
    ### 必填字段
    - **file**: 文件数据（UploadFile类型）
    
    ### 可选字段
    - **title**: 文件标题（字符串）
    - **description**: 文件描述（字符串）
    - **resource_type**: 资源类型（字符串，默认"file"）
    - **tags**: 标签列表（字符串，用逗号分隔）
    - **is_public**: 是否公开（布尔值，默认false）
    - **priority**: 优先级（整数0-10，默认0）
    
    ## 业务流程
    1. **主题验证**: 检查主题是否存在
    2. **文件上传**: 将文件存储到系统中
    3. **建立关联**: 自动关联文件到指定主题
    4. **异步处理**: 触发文件内容处理
    
    ## 使用示例
    ```bash
    curl -X POST "http://localhost:8000/api/v1/topics/7/upload" \
      -F "file=@document.pdf" \
      -F "title=重要文档" \
      -F "description=项目相关的重要PDF文档"
    ```
    
    ## 返回结果
    返回上传成功的文件信息，包括文件ID、主题关联等。
    
    ## 错误处理
    - **400**: 文件或主题参数错误
    - **404**: 指定主题不存在
    - **413**: 文件大小超出限制
    - **500**: 存储或处理失败
    """
    try:
        # 验证文件
        if not file:
            raise ValueError("未提供文件")
        
        if not file.filename:
            raise ValueError("文件名不能为空")
        
        # 检查文件大小 (100MB限制)
        max_size = 100 * 1024 * 1024  # 100MB
        file_content = await file.read()
        if len(file_content) > max_size:
            raise ValueError(f"文件大小不能超过{max_size // (1024*1024)}MB")
        
        # 重置文件指针
        await file.seek(0)
        
        # 生成文件ID
        import uuid
        file_id = str(uuid.uuid4())
        
        # 解析标签
        tag_list = []
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
        
        # 验证主题存在
        topic = await topic_service.get_topic(topic_id)
        if not topic:
            raise ValueError(f"主题 {topic_id} 不存在")
        
        # 通过FileService创建文件记录
        from ..services import FileService
        from ..storage import MinIOStorage
        from config import get_config
        
        config = get_config()
        storage = MinIOStorage(
            endpoint=config.storage.minio_endpoint or "localhost:9000",
            access_key=config.storage.minio_access_key or "minioadmin",
            secret_key=config.storage.minio_secret_key or "minioadmin123",
            secure=config.storage.minio_secure,
            bucket_name=config.storage.bucket_name or "rag-uploads"
        )
        
        file_service = FileService(topic_service.topic_repo.session, storage)
        
        # 创建文件记录
        await file_service.file_repo.create_file(
            file_id=file_id,
            original_name=file.filename,
            content_type=file.content_type or "application/octet-stream",
            file_size=len(file_content),
            filename=title or file.filename,
            status=FileStatus.AVAILABLE,
            topic_id=topic_id,
            storage_key=f"uploads/{file_id}/{file.filename}"
        )

        # 存储文件（简化实现，记录日志）
        logger.info(f"文件已上传到主题 {topic_id}: {file.filename} (ID: {file_id})")
        
        return APIResponse(
            success=True,
            message=f"文件已成功上传到主题 {topic_id}",
            data={
                "file_id": file_id,
                "filename": title or file.filename,
                "original_name": file.filename,
                "size": len(file_content),
                "content_type": file.content_type or "application/octet-stream",
                "topic_id": topic_id,
                "status": FileStatus.AVAILABLE,
                "processing_status": "pending",
                "tags": tag_list,
                "priority": priority or 0
            }
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"上传文件到主题失败: {e}")
        raise HTTPException(status_code=500, detail=f"上传文件失败: {str(e)}")

@router.delete("/{topic_id}/resources/{file_id}", response_model=APIResponse, summary="从主题移除资源")
async def remove_resource_from_topic(
    topic_id: int,
    file_id: str,
    service: TopicService = Depends(get_topic_service)
):
    """
    # 从主题中移除指定资源
    
    解除文件与主题之间的关联关系，但不删除文件本身。
    
    ## 路径参数
    - **topic_id**: 主题ID（整数，必填）
    - **file_id**: 要移除的文件ID（字符串，必填）
    
    ## 业务逻辑
    1. **验证关联**: 确认文件确实属于指定主题
    2. **解除关联**: 将文件的topic_id设置为null
    3. **保留文件**: 文件本身不会被删除，仍存在于存储中
    
    ## 使用场景
    - 重新整理主题内容
    - 临时移除不相关的文件
    - 清理主题资源
    
    ## 注意事项
    - 只是解除关联关系，不删除实际文件
    - 移除后文件可以重新关联到其他主题
    """
    try:
        success = await service.remove_resource_from_topic(topic_id, file_id)
        
        if success:
            return APIResponse(
                success=True,
                message=f"成功从主题 {topic_id} 移除资源 {file_id}"
            )
        else:
            raise HTTPException(status_code=500, detail="移除资源失败")
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"移除资源失败: {str(e)}")

@router.get("/{topic_id}/resources", response_model=APIResponse, summary="获取主题的所有资源")
async def get_topic_resources(
    topic_id: int,
    page: int = Query(1, ge=1, description="页码，从1开始"),
    page_size: int = Query(20, ge=1, le=100, description="每页返回的资源数量"),
    service: TopicService = Depends(get_topic_service)
):
    """
    # 获取主题下的所有资源列表
    
    分页获取与指定主题关联的所有文件资源，支持灵活的分页控制。
    
    ## 路径参数
    - **topic_id**: 主题ID（整数，必填）
    
    ## 查询参数
    - **page**: 页码（默认为1）
    - **page_size**: 每页数量（默认为20，最多100）
    
    ## 返回结果
    返回分页后的资源列表，包含：
    - **resources**: 资源详细信息数组
    - **total**: 总资源数量
    - **page**: 当前页码
    - **page_size**: 每页大小
    - **total_pages**: 总页数
    
    ## 资源信息
    每个资源包含：
    - 文件基本信息（ID、名称、大小、类型）
    - 上传和处理状态
    - 存储位置和访问链接
    - 创建和更新时间
    
    ## 使用场景
    - 浏览主题下的所有文档
    - 管理和组织主题资源
    - 构建文档列表界面
    
    ## 排序规则
    资源按创建时间倒序排列（最新的在前）。
    """
    try:
        resources_data = await service.get_topic_resources(topic_id, page, page_size)
        
        return APIResponse(
            success=True,
            data=resources_data,
            message=f"获取主题 {topic_id} 的资源列表成功"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取主题资源失败: {str(e)}")
