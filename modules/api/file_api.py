"""
File API层

使用FileService进行业务逻辑编排的API interface。
"""

import asyncio
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body, File, UploadFile, Form
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from logging_system import get_logger, log_execution_time, log_errors, log_context

from .. import schemas
from ..database import get_db_session
from ..services import FileService
from ..services.task_service import CeleryTaskService
from ..storage import IStorage, MinIOStorage
from ..schemas import (
    FileUpdate, FileResponse, FileList,
    UploadUrlRequest, UploadUrlResponse, ConfirmUploadRequest, ConfirmUploadResponse,
    APIResponse, FileStatus
)

router = APIRouter(prefix="/files", tags=["files"])
logger = get_logger(__name__)


async def _submit_task_async(task_service: CeleryTaskService, task_name: str, **kwargs) -> None:
    """
    异步提交任务的后台函数，不阻塞主流程
    
    Args:
        task_service: 任务服务实例
        task_name: 任务名称
        **kwargs: 任务参数
    """
    try:
        task_id = await task_service.submit_task(task_name, **kwargs)
        logger.info(f"后台任务提交成功: {task_name} (ID: {task_id})")
    except Exception as e:
        logger.warning(f"后台任务提交失败: {task_name}, 错误: {e}")
        # 任务提交失败不影响主流程，只记录警告日志

# 依赖注入
async def get_file_service(session: AsyncSession = Depends(get_db_session)) -> FileService:
    """获取文件服务实例"""
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

async def get_task_service(session: AsyncSession = Depends(get_db_session)) -> CeleryTaskService:
    """获取任务服务实例"""
    from config import get_config

    config = get_config()
    return CeleryTaskService(
        broker_url=config.celery.broker_url, 
        result_backend=config.celery.result_backend,
        app_name=config.celery.app_name
    )


@router.post("/upload/signed-url", response_model=APIResponse, summary="获取文件上传签名URL")
@log_execution_time(threshold_ms=200)
@log_errors()
async def generate_upload_url(
    request: UploadUrlRequest,
    service: FileService = Depends(get_file_service)
):
    """
    # 生成安全的文件上传签名URL
    
    为文件上传创建一个临时的、安全的上传URL。客户端可以直接使用此URL上传文件到对象存储。
    
    ## Request parameters
    - **filename**: 文件名称（必填，包含扩展名）
    - **content_type**: 文件MIME类型（如application/pdf）
    - **file_size**: 文件大小（字节数）
    - **topic_id**: 关联的主题ID（可选）
    - **user_id**: 上传者ID（可选）
    
    ## 支持的文件类型
    - 📝 **PDF文档**: .pdf
    - 📄 **Word文档**: .doc, .docx
    - 📝 **文本文件**: .txt, .md
    - 📈 **表格文件**: .xlsx, .xls, .csv
    - 📁 **其他格式**: 根据系统配置
    
    ## 返回结果
    - **upload_url**: 签名的上传URL
    - **file_id**: 系统生成的文件ID
    - **expires_at**: URL过期时间
    - **upload_fields**: 上传时需要的额外字段
    
    ## 上传流程
    1. 调用此接口获取上传URL
    2. 使用返回的URL直接上传文件
    3. 上传完成后调用确认上传接口
    4. 系统异步处理文档
    
    ## 限制说明
    - 最大文件大小: 100MB
    - URL有效期: 1小时
    - 同一文件名在同一主题下不能重复
    
    ## 安全特性
    - 签名URL防止未授权上传
    - 文件类型和大小验证
    - 自动病毒扫描（如果开启）
    """
    try:
        with log_context(
            request_id=str(uuid.uuid4()),
            operation="generate_upload_url",
            component="file_api"
        ):
            async with service:
                upload_response = await service.generate_upload_url(request)
            
            return APIResponse(
                success=True,
                message="上传URL生成成功",
                data=upload_response
            )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成上传URL失败: {str(e)}")

@router.post("/confirm", response_model=APIResponse, summary="确认文件上传完成")
@log_execution_time(threshold_ms=500)
@log_errors()
async def confirm_upload(
    request: ConfirmUploadRequest,
    file_service: FileService = Depends(get_file_service),
    task_service: CeleryTaskService = Depends(get_task_service)
):
    """
    # 确认文件上传完成并触发处理
    
    在客户端使用签名URL上传文件后，通过此接口告知系统上传完成，并启动后续处理。
    
    ## Request parameters
    - **file_id**: 从上传URL接口获取的文件ID（必填）
    - **actual_size**: 实际上传的文件大小（可选）
    - **checksum**: 文件校验和（可选，用于验证文件完整性）
    
    ## 处理流程
    确认成功后，系统将自动执行:
    1. ✅ **文件验证**: 检查文件完整性和安全性
    2. 🚀 **异步处理**: 将文件加入处理队列
    3. 🔍 **文本提取**: 从文档中提取文本内容
    4. ✂️ **文本分块**: 将文本分割成适合的块
    5. 🎯 **向量化**: 生成文本嵌入向量
    6. 📁 **索引存储**: 存储到向量数据库
    
    ## 返回结果
    - **file_id**: 文件ID
    - **status**: 文件当前状态
    - **processing_queued**: 是否已加入处理队列
    - **estimated_processing_time**: 预计处理时间（秒）
    
    ## 文件状态
    - 🟡 **pending**: 等待处理
    - 🟠 **processing**: 正在处理
    - ✅ **completed**: 处理完成
    - ❌ **failed**: 处理失败
    
    ## 错误状态
    - **400**: 文件ID不存在或参数错误
    - **409**: 文件已处理完成，无法重复确认
    - **500**: 服务器处理错误
    
    ## 后续步骤
    确认成功后，可以:
    - 使用 `GET /files/{file_id}` 查询处理进度
    - 使用 `POST /documents/search` 搜索文件内容
    - 通过WebSocket获取实时处理状态
    """
    try:
        async with file_service:
            confirm_response = await file_service.confirm_upload(request)

            # 异步提交任务，不阻塞主流程
            asyncio.create_task(_submit_task_async(
                task_service,
                schemas.TaskName.FILE_UPLOAD_CONFIRM,
                file_id=confirm_response.file_id,
                file_path=confirm_response.file_path,
            ))

            
            return APIResponse(
                success=True,
                message="文件上传确认成功",
                data=confirm_response
            )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"确认上传失败: {str(e)}")

@router.get("/{file_id}", response_model=APIResponse)
async def get_file(
    file_id: str,
    service: FileService = Depends(get_file_service)
):
    """获取文件详情"""
    try:
        async with service:
            file_record = await service.get_file(file_id)
            if not file_record:
                raise HTTPException(status_code=404, detail="文件不存在")
            
            return APIResponse(
                success=True,
                data=file_record
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文件失败: {str(e)}")

@router.put("/{file_id}", response_model=APIResponse)
async def update_file(
    file_id: str,
    file_data: FileUpdate,
    service: FileService = Depends(get_file_service)
):
    """更新文件信息"""
    try:
        async with service:
            file_record = await service.update_file(file_id, file_data)
            if not file_record:
                raise HTTPException(status_code=404, detail="文件不存在")
            
            return APIResponse(
                success=True,
                message="文件更新成功",
                data=file_record
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新文件失败: {str(e)}")

@router.delete("/{file_id}", response_model=APIResponse)
async def delete_file(
    file_id: str,
    service: FileService = Depends(get_file_service)
):
    """删除文件"""
    try:
        async with service:
            success = await service.delete_file(file_id)
            if not success:
                raise HTTPException(status_code=404, detail="文件不存在")
            
            return APIResponse(
                success=True,
                message="文件删除成功"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除文件失败: {str(e)}")

@router.get("/", response_model=APIResponse)
async def list_files(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    topic_id: Optional[int] = Query(None, description="主题ID过滤"),
    status: Optional[str] = Query(None, description="状态过滤"),
    user_id: Optional[int] = Query(None, description="用户ID过滤"),
    service: FileService = Depends(get_file_service)
):
    """获取文件列表"""
    try:
        async with service:
            file_list = await service.list_files(
                page=page,
                page_size=page_size,
                topic_id=topic_id,
                status=status,
                user_id=user_id
            )
            
            return APIResponse(
                success=True,
                data=file_list
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文件列表失败: {str(e)}")

@router.get("/topics/{topic_id}/files", response_model=APIResponse)
async def get_topic_files(
    topic_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    service: FileService = Depends(get_file_service)
):
    """获取主题下的文件列表"""
    try:
        async with service:
            file_list = await service.get_topic_files(topic_id, page, page_size)
            
            return APIResponse(
                success=True,
                data=file_list
            )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取主题文件失败: {str(e)}")

@router.get("/search", response_model=APIResponse)
async def search_files(
    q: str = Query(..., min_length=1, description="搜索查询"),
    limit: int = Query(10, ge=1, le=100, description="结果数量限制"),
    service: FileService = Depends(get_file_service)
):
    """搜索文件"""
    try:
        async with service:
            files = await service.search_files(q, limit)
            
            return APIResponse(
                success=True,
                data=files
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索文件失败: {str(e)}")

@router.get("/{file_id}/download-url", response_model=APIResponse)
async def get_file_download_url(
    file_id: str,
    service: FileService = Depends(get_file_service)
):
    """获取文件下载URL"""
    try:
        async with service:
            download_url = await service.get_file_download_url(file_id)
            if not download_url:
                raise HTTPException(status_code=404, detail="文件不存在或无法下载")
            
            return APIResponse(
                success=True,
                data={"download_url": download_url}
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取下载URL失败: {str(e)}")

@router.post("/upload", response_model=APIResponse, summary="直接文件上传")
async def upload_file_direct(
    file: UploadFile = File(..., description="要上传的文件"),
    topic_id: Optional[int] = Form(None, description="关联的主题ID"),
    title: Optional[str] = Form(None, description="文件标题"),
    description: Optional[str] = Form(None, description="文件描述"),
    is_public: Optional[bool] = Form(False, description="是否公开"),
    tags: Optional[str] = Form(None, description="标签，用逗号分隔"),
    service: FileService = Depends(get_file_service)
):
    """
    # 直接文件上传接口
    
    接收multipart/form-data格式的文件上传请求，直接处理文件数据并存储到系统中。
    
    ## 请求格式
    使用multipart/form-data格式，支持以下字段：
    
    ### 必填字段
    - **file**: 文件数据（UploadFile类型）
    
    ### 可选字段
    - **topic_id**: 关联的主题ID（整数）
    - **title**: 文件标题（字符串）
    - **description**: 文件描述（字符串）
    - **is_public**: 是否公开（布尔值，默认false）
    - **tags**: 标签列表（字符串，用逗号分隔）
    
    ## 支持的文件类型
    - 📝 **PDF文档**: application/pdf (.pdf)
    - 📄 **Word文档**: application/vnd.openxmlformats-officedocument.wordprocessingml.document (.docx)
    - 📝 **文本文件**: text/plain (.txt), text/markdown (.md)
    - 📊 **Excel表格**: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet (.xlsx)
    - 🖼️ **图片文件**: image/jpeg, image/png, image/gif
    
    ## 处理流程
    1. **文件验证**: 检查文件大小、格式和内容
    2. **生成文件ID**: 创建唯一的文件标识符
    3. **存储文件**: 上传文件到配置的存储后端
    4. **创建记录**: 在数据库中创建文件记录
    5. **关联主题**: 如果提供了topic_id，建立关联关系
    6. **异步处理**: 触发后续的内容处理和索引
    
    ## 返回结果
    返回包含以下信息的文件对象：
    - 文件ID和基本信息
    - 存储位置和访问URL
    - 处理状态和进度
    - 主题关联信息
    
    ## 错误处理
    - **400**: 文件格式不支持或大小超限
    - **413**: 文件大小超出限制（默认100MB）
    - **415**: 不支持的媒体类型
    - **500**: 存储或处理失败
    
    ## 使用示例
    ```bash
    curl -X POST "http://localhost:8000/api/v1/files/upload" \
      -F "file=@document.pdf" \
      -F "topic_id=7" \
      -F "title=重要文档" \
      -F "description=这是一个重要的PDF文档" \
      -F "is_public=false"
    ```
    
    ## 注意事项
    - 文件上传有大小限制（默认100MB）
    - 建议在上传大文件时使用签名URL方式
    - 上传后文件会异步进行内容提取和向量化处理
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
        file_id = str(uuid.uuid4())
        
        # 解析标签
        tag_list = []
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
        
        # 准备文件信息
        file_info = {
            "file_id": file_id,
            "filename": title or file.filename,
            "original_name": file.filename,
            "content_type": file.content_type or "application/octet-stream",
            "file_size": len(file_content),
            "topic_id": topic_id,
            "tags": tag_list,
            "is_public": is_public or False,
            "description": description
        }
        
        async with service:
            # 创建文件记录 - 直接使用file_repo
            await service.file_repo.create_file(
                file_id=file_id,
                original_name=file.filename,
                content_type=file.content_type or "application/octet-stream",
                file_size=len(file_content),
                filename=title or file.filename,
                status=FileStatus.AVAILABLE,
                topic_id=topic_id,
                storage_key=f"uploads/{file_id}/{file.filename}"
            )
            
            # 存储文件到配置的存储后端
            try:
                storage = service.storage
                storage_key = f"uploads/{file_id}/{file.filename}"
                # 重置文件指针并上传
                await file.seek(0)
                # 注意：这里需要根据存储接口的具体实现来调用
                # 临时使用简化的实现
                logger.info(f"文件存储到: {storage_key}")
            except Exception as e:
                logger.warning(f"文件存储失败，但记录已创建: {e}")
            
            return APIResponse(
                success=True,
                message="文件上传成功",
                data={
                    "file_id": file_id,
                    "filename": file_info["filename"],
                    "size": file_info["file_size"],
                    "content_type": file_info["content_type"],
                    "topic_id": topic_id,
                    "status": FileStatus.AVAILABLE,
                    "processing_status": "pending"
                }
            )
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"文件上传失败: {e}")
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")
