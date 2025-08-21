"""
文件上传服务实现

提供完整的文件上传管理功能。
"""

from typing import Dict, Any, Optional
from uuid import uuid4
from datetime import datetime

from .base import IFileUploadService
from ..storage import IStorage, MockStorage, MinIOStorage
from ..database import get_session
from ..repository import FileRepository
from ..database.models import FileStatus
from ..tasks.base import ITaskService, TaskPriority
from logging_system import get_logger, log_execution_time, log_errors

logger = get_logger(__name__)

class FileUploadService(IFileUploadService):
    """文件上传服务实现"""
    
    def __init__(self, 
                 storage: Optional[IStorage] = None,
                 task_service: Optional[ITaskService] = None):
        """
        初始化文件上传服务
        
        Args:
            storage: 存储后端，如果不提供则使用默认的MinIOStorage
            task_service: 任务服务，用于触发异步处理任务
        """
        self.storage = storage or MinIOStorage()
        self.task_service = task_service
    
    @log_execution_time(threshold_ms=100)
    @log_errors()
    async def generate_upload_url(self,
                                filename: str,
                                content_type: str,
                                topic_id: Optional[int] = None,
                                expires_in: int = 3600) -> Dict[str, Any]:
        """生成文件上传的签名URL"""
        
        try:
            # 生成唯一文件ID
            file_id = str(uuid4())
            
            # 生成存储键
            file_key = f"uploads/{file_id}/{filename}"
            
            # 生成签名上传URL
            upload_info = await self.storage.generate_signed_upload_url(
                file_key=file_key,
                content_type=content_type,
                expires_in=expires_in
            )
            
            # 在数据库中创建文件记录
            async with get_session() as session:
                file_repo = FileRepository(session)
                file_record = await file_repo.create_file(
                    file_id=file_id,
                    original_name=filename,
                    content_type=content_type,
                    storage_bucket=upload_info.get('bucket'),
                    storage_key=file_key,
                    topic_id=topic_id,
                    status=FileStatus.UPLOADING,
                    metadata={
                        "upload_method": "signed_url",
                        "expires_at": upload_info.get('expires_at')
                    }
                )
            
            if not file_record:
                raise Exception(f"创建文件记录失败: 返回None")
            
            # 组装返回结果
            result = {
                "file_id": file_id,
                "upload_url": upload_info["upload_url"],
                "method": upload_info["method"],
                "headers": upload_info.get("headers", {}),
                "fields": upload_info.get("fields", {}),
                "expires_at": upload_info.get("expires_at"),
                "max_file_size": 100 * 1024 * 1024,  # 100MB 限制
                "allowed_types": [
                    "application/pdf",
                    "application/msword", 
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    "text/plain",
                    "text/markdown",
                    "text/html",
                    "application/json",
                    "text/csv"
                ]
            }
            
            logger.info(f"生成上传URL: {filename} (文件ID: {file_id})")
            return result
            
        except Exception as e:
            logger.error(f"生成上传URL失败: {e}")
            raise
    
    @log_execution_time(threshold_ms=200)
    @log_errors()
    async def confirm_upload(self,
                           file_id: str,
                           actual_size: Optional[int] = None,
                           file_hash: Optional[str] = None) -> Dict[str, Any]:
        """确认文件上传完成"""
        
        try:
            # 获取文件记录
            async with get_session() as session:
                file_repo = FileRepository(session)
                file_info = await file_repo.get_file_by_id(file_id)
                
                if not file_info:
                    return {
                        "success": False,
                        "error": f"文件记录不存在: {file_id}"
                    }
                
                # 验证文件是否真的存在于存储中
                file_exists = await self.storage.file_exists(file_info.storage_key)
                if not file_exists:
                    return {
                        "success": False,
                        "error": "文件未找到，上传可能失败"
                    }
                
                # 获取存储中的文件信息
                storage_info = await self.storage.get_file_info(file_info.storage_key)
                
                # 更新文件状态和信息
                updated_file = await file_repo.update_file_status(
                    file_id=file_id,
                    status=FileStatus.AVAILABLE,
                    processing_status="上传完成",
                    file_size=actual_size or storage_info.get('size', 0),
                    file_hash=file_hash or storage_info.get('hash'),
                    storage_url=storage_info.get('access_url')
                )
                
                if not updated_file:
                    return {
                        "success": False,
                        "error": "更新文件状态失败"
                    }
                
                # 异步触发RAG处理任务（如果文件类型支持RAG处理）
                if self.task_service and self._is_rag_supported_file(file_info.content_type):
                    # 使用asyncio.create_task在后台异步提交任务，不阻塞主流程
                    import asyncio
                    asyncio.create_task(self._submit_rag_task_async(
                        file_id=file_id,
                        file_path=file_info.storage_key,
                        content_type=file_info.content_type,
                        topic_id=file_info.topic_id
                    ))
                
                logger.info(f"确认文件上传完成: {file_id}")
                return {
                    "success": True,
                    "file_id": file_id,
                    "status": "completed",
                    "message": "文件上传确认成功",
                    "file_size": actual_size or storage_info.get('size', 0),
                    "download_url": await self.get_download_url(file_id)
                }
                
        except Exception as e:
            logger.error(f"确认文件上传失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _submit_rag_task_async(self, file_id: str, file_path: str, content_type: str, topic_id: Optional[int]) -> None:
        """
        异步提交RAG处理任务的后台函数，不阻塞主流程
        
        Args:
            file_id: 文件ID
            file_path: 文件路径
            content_type: 文件类型
            topic_id: 主题ID
        """
        try:
            task_id = await self.task_service.submit_task(
                "rag.process_document",
                file_id=file_id,
                file_path=file_path,
                content_type=content_type,
                topic_id=topic_id,
                priority=TaskPriority.NORMAL
            )
            logger.info(f"后台RAG任务提交成功: {task_id} for file: {file_id}")
        except Exception as task_error:
            logger.warning(f"后台RAG任务提交失败: {task_error} for file: {file_id}")
            # 任务提交失败不影响文件上传确认成功

    def _is_rag_supported_file(self, content_type: str) -> bool:
        """检查文件类型是否支持RAG处理"""
        supported_types = {
            "application/pdf",
            "application/msword", 
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "text/plain",
            "text/markdown",
            "text/html",
            "text/csv"
        }
        return content_type in supported_types
    
    async def get_download_url(self,
                             file_id: str,
                             expires_in: int = 3600) -> str:
        """获取文件下载URL"""
        
        try:
            # 获取文件记录
            async with get_session() as session:
                file_repo = FileRepository(session)
                file_info = await file_repo.get_file_by_id(file_id)
                
                if not file_info:
                    raise Exception(f"文件记录不存在: {file_id}")
                
                # 生成签名下载URL
                download_url = await self.storage.generate_signed_download_url(
                    file_key=file_info.storage_key,
                    expires_in=expires_in
                )
                
                logger.info(f"生成下载URL: {file_id}")
                return download_url
            
        except Exception as e:
            logger.error(f"生成下载URL失败: {e}")
            raise
    
    async def delete_file(self, file_id: str) -> bool:
        """删除文件"""
        
        try:
            # 获取文件记录
            async with get_session() as session:
                file_repo = FileRepository(session)
                file_info = await file_repo.get_file_by_id(file_id)
                
                if not file_info:
                    logger.warning(f"文件记录不存在: {file_id}")
                    return False
                
                # 从存储中删除文件
                storage_deleted = await self.storage.delete_file(file_info.storage_key)
                
                # 软删除数据库记录
                db_deleted = await file_repo.delete_file(file_id)
                
                success = storage_deleted and db_deleted
                
                if success:
                    logger.info(f"删除文件成功: {file_id}")
                else:
                    logger.warning(f"删除文件部分失败: {file_id} (存储: {storage_deleted}, 数据库: {db_deleted})")
                
                return success
            
        except Exception as e:
            logger.error(f"删除文件失败: {e}")
            return False
    
    async def get_file_info(self, file_id: str) -> Optional[Dict[str, Any]]:
        """获取文件详细信息"""
        
        try:
            # 从数据库获取文件信息
            async with get_session() as session:
                file_repo = FileRepository(session)
                file_info = await file_repo.get_file_by_id(file_id)
                
                if not file_info:
                    return None
                
                # 从存储获取额外信息
                storage_info = await self.storage.get_file_info(file_info.storage_key)
                
                # 合并信息
                result = {
                    "file_id": file_info.file_id,
                    "original_name": file_info.original_name,
                    "content_type": file_info.content_type,
                    "file_size": file_info.file_size,
                    "status": file_info.status,
                    "storage_key": file_info.storage_key,
                    "topic_id": file_info.topic_id,
                    "created_at": file_info.created_at,
                    "updated_at": file_info.updated_at,
                    "storage_info": storage_info,
                    "is_downloadable": file_info.status == FileStatus.AVAILABLE
                }
                
                return result
            
        except Exception as e:
            logger.error(f"获取文件信息失败: {e}")
            return None
    
    async def list_files(self,
                        topic_id: Optional[int] = None,
                        status: Optional[str] = None,
                        page: int = 1,
                        page_size: int = 20) -> Dict[str, Any]:
        """列出文件"""
        
        try:
            async with get_session() as session:
                file_repo = FileRepository(session)
                
                if topic_id:
                    return await file_repo.list_topic_files(
                        topic_id=topic_id,
                        page=page,
                        page_size=page_size,
                        status=status
                    )
                else:
                    # 这里可以扩展为列出所有文件
                    return {
                        "files": [],
                        "message": "列出全部文件功能待实现"
                    }
                
        except Exception as e:
            logger.error(f"列出文件失败: {e}")
            return {
                "files": [],
                "error": str(e)
            }
