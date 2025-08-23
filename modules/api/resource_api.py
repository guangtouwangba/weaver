"""
Resource API层

提供统一的资源管理接口，简化前端调用。
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from modules.database import get_db_session
from modules.schemas import APIResponse
from modules.services import FileService
from modules.storage import MinIOStorage

router = APIRouter(prefix="/resources", tags=["resources"])
logger = logging.getLogger(__name__)


# 依赖注入
async def get_file_service(
    session: AsyncSession = Depends(get_db_session),
) -> FileService:
    """获取文件服务实例"""
    from config import get_config

    config = get_config()
    storage = MinIOStorage(
        endpoint=config.storage.minio_endpoint or "localhost:9000",
        access_key=config.storage.minio_access_key or "minioadmin",
        secret_key=config.storage.minio_secret_key or "minioadmin123",
        secure=config.storage.minio_secure,
        bucket_name=config.storage.bucket_name or "rag-uploads",
    )
    return FileService(session, storage)


@router.get("/{resource_id}", response_model=APIResponse, summary="获取资源详情")
async def get_resource(
    resource_id: str, service: FileService = Depends(get_file_service)
):
    """
    # 获取资源详细信息

    根据资源ID获取资源的完整信息，包括文件元数据、关联主题等。

    ## 路径参数
    - **resource_id**: 资源ID（文件ID）

    ## 返回内容
    - 文件基本信息（名称、大小、类型等）
    - 关联的主题信息
    - 处理状态和进度
    - 创建和修改时间

    ## 错误状态
    - **404**: 资源不存在
    - **500**: 服务器内部错误
    """
    try:
        async with service:
            file_record = await service.get_file(resource_id)
            if not file_record:
                raise HTTPException(status_code=404, detail="资源不存在")

            return APIResponse(
                success=True, message="获取资源信息成功", data=file_record
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取资源失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取资源失败: {str(e)}")


@router.delete("/{resource_id}", response_model=APIResponse, summary="删除资源")
async def delete_resource(
    resource_id: str, service: FileService = Depends(get_file_service)
):
    """
    # 删除资源

    彻底删除指定的资源，包括文件数据和所有相关元数据。
    这是一个不可逆的操作，请谨慎使用。

    ## 路径参数
    - **resource_id**: 资源ID（文件ID）

    ## 删除操作
    删除操作将执行以下步骤：
    1. **验证权限**: 确认用户有权删除该资源
    2. **解除关联**: 从所有关联的主题中移除
    3. **删除文件**: 从存储后端删除物理文件
    4. **清理数据**: 删除数据库中的相关记录
    5. **清理索引**: 从搜索索引中移除相关数据

    ## 返回结果
    - **success**: 删除操作是否成功
    - **message**: 操作结果描述
    - **data**: 被删除资源的基本信息

    ## 错误处理
    - **400**: 资源正在使用中，无法删除
    - **404**: 资源不存在或已被删除
    - **403**: 没有删除权限
    - **500**: 删除过程中发生错误

    ## 使用示例
    ```bash
    curl -X DELETE "http://localhost:8000/api/v1/resources/463bbc1d-6fe3-4a78-bdf5-feab5a0132d4"
    ```

    ## 注意事项
    - 删除操作是不可逆的，建议在删除前进行确认
    - 如果资源被多个主题引用，将从所有主题中移除
    - 删除大文件可能需要较长时间
    """
    try:
        # 首先获取资源信息以便返回
        async with service:
            file_record = await service.get_file(resource_id)
            if not file_record:
                raise HTTPException(status_code=404, detail="资源不存在")

            # 执行删除操作
            success = await service.delete_file(resource_id)
            if not success:
                raise HTTPException(status_code=500, detail="删除操作失败")

            logger.info(f"成功删除资源: {resource_id}")

            return APIResponse(
                success=True,
                message=f"资源 {resource_id} 已成功删除",
                data={
                    "resource_id": resource_id,
                    "original_name": file_record.original_name,
                    "deleted_at": "now",
                },
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除资源失败 {resource_id}: {e}")
        raise HTTPException(status_code=500, detail=f"删除资源失败: {str(e)}")


@router.put("/{resource_id}", response_model=APIResponse, summary="更新资源信息")
async def update_resource(
    resource_id: str,
    resource_data: dict,
    service: FileService = Depends(get_file_service),
):
    """
    # 更新资源信息

    更新资源的元数据信息，如标题、描述、标签等。

    ## 路径参数
    - **resource_id**: 资源ID（文件ID）

    ## 请求体
    - **filename**: 显示名称
    - **description**: 资源描述
    - **tags**: 标签列表
    - **is_public**: 是否公开

    ## 返回结果
    返回更新后的资源信息

    ## 错误状态
    - **404**: 资源不存在
    - **400**: Request parameters错误
    - **500**: 更新失败
    """
    try:
        from ..schemas import FileUpdate

        # 构造更新对象
        update_data = FileUpdate(**resource_data)

        async with service:
            updated_file = await service.update_file(resource_id, update_data)
            if not updated_file:
                raise HTTPException(status_code=404, detail="资源不存在")

            return APIResponse(
                success=True, message="资源信息更新成功", data=updated_file
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新资源失败 {resource_id}: {e}")
        raise HTTPException(status_code=500, detail=f"更新资源失败: {str(e)}")
