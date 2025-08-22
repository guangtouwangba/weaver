"""
文件Service层

处理文件相关的Business logic。
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from .base_service import BaseService
from ..repository import FileRepository, TopicRepository
from ..schemas import (
    FileCreate, FileUpdate, FileResponse, FileList,
    UploadUrlRequest, UploadUrlResponse, ConfirmUploadRequest, ConfirmUploadResponse,
    file_to_response, files_to_responses
)
from ..schemas.enums import FileStatus
from ..storage import IStorage

logger = logging.getLogger(__name__)

class FileService(BaseService):
    """文件Business service"""
    
    def __init__(self, session: AsyncSession, storage: IStorage):
        super().__init__(session)
        self.file_repo = FileRepository(session)
        self.topic_repo = TopicRepository(session)
        self.storage = storage
    
    async def generate_upload_url(self, request: UploadUrlRequest) -> UploadUrlResponse:
        """生成上传URL"""
        try:
            # 验证请求
            await self._validate_upload_request(request)
            
            # 生成文件ID
            file_id = self._generate_file_id()
            
            # 生成上传URL
            upload_url = await self.storage.generate_presigned_url(
                key=f"uploads/{file_id}/{request.filename}",
                content_type=request.content_type,
                expires_in=3600  # 1小时
            )
            
            # 验证topic_id
            topic_id = None
            if request.topic_id and request.topic_id > 0:
                # 验证主题是否存在
                topic = await self.topic_repo.get_topic_by_id(request.topic_id)
                if topic:
                    topic_id = request.topic_id
                    
            # 创建文件记录
            await self.file_repo.create_file(
                file_id=file_id,
                original_name=request.filename,
                content_type=request.content_type,
                file_size=request.file_size or 0,
                status=FileStatus.UPLOADING,  # 使用枚举值
                topic_id=topic_id,  # 使用验证后的topic_id或None
                storage_key=f"uploads/{file_id}/{request.filename}"
            )
            
            self.logger.info(f"Generated upload URL for file: {request.filename} (ID: {file_id})")
            
            return UploadUrlResponse(
                upload_url=upload_url,
                file_id=file_id,
                expires_at=datetime.utcnow() + timedelta(hours=1)
            )
            
        except Exception as e:
            self._handle_error(e, "generate_upload_url")
    
    async def confirm_upload(self, request: ConfirmUploadRequest) -> ConfirmUploadResponse:
        """确认文件上传完成"""
        try:
            # 更新文件状态
            file_record = await self.file_repo.update_file_status(
                file_id=request.file_id,
                status=FileStatus.AVAILABLE,
                processing_status="pending"
            )
            
            if not file_record:
                raise ValueError(f"文件 {request.file_id} 不存在")
            
            # 更新文件大小和哈希
            if request.actual_size:
                await self.file_repo.update(request.file_id, {
                    'file_size': request.actual_size,
                    'file_hash': request.file_hash
                })
            
            self.logger.info(f"Confirmed upload for file: {request.file_id}")
            
            return ConfirmUploadResponse(
                file_id=request.file_id,
                status=FileStatus.AVAILABLE,
                processing_queued=True,
                estimated_processing_time=60,  # 预计60秒
                file_path=file_record.storage_key  # 文件存储路径
            )
            
        except Exception as e:
            self._handle_error(e, f"confirm_upload_{request.file_id}")
    
    async def get_file(self, file_id: str) -> Optional[FileResponse]:
        """获取文件详情"""
        try:
            file_record = await self.file_repo.get_file_by_id(file_id)
            if not file_record:
                return None
            
            return file_to_response(file_record)
            
        except Exception as e:
            self._handle_error(e, f"get_file_{file_id}")
    
    async def update_file(self, file_id: str, file_data: FileUpdate) -> Optional[FileResponse]:
        """更新文件信息"""
        try:
            # 检查文件是否存在
            existing_file = await self.file_repo.get_file_by_id(file_id)
            if not existing_file:
                return None
            
            # 准备更新字典
            update_dict = file_data.model_dump(exclude_none=True)
            
            # 更新文件
            updated_file = await self.file_repo.update(file_id, update_dict)
            
            self.logger.info(f"Updated file: {file_id}")
            return file_to_response(updated_file) if updated_file else None
            
        except Exception as e:
            self._handle_error(e, f"update_file_{file_id}")
    
    async def delete_file(self, file_id: str) -> bool:
        """删除文件"""
        try:
            # 获取文件信息
            file_record = await self.file_repo.get_file_by_id(file_id)
            if not file_record:
                return False
            
            # 从存储中删除文件
            if file_record.storage_key:
                await self.storage.delete_file(file_record.storage_key)
            
            # 软删除文件记录
            success = await self.file_repo.soft_delete_file(file_id)
            
            if success:
                self.logger.info(f"Deleted file: {file_id}")
            
            return success
            
        except Exception as e:
            self._handle_error(e, f"delete_file_{file_id}")
    
    async def list_files(self, 
                        page: int = 1, 
                        page_size: int = 20,
                        topic_id: Optional[int] = None,
                        status: Optional[str] = None,
                        user_id: Optional[int] = None) -> FileList:
        """获取文件列表"""
        try:
            # 构建过滤条件
            filters = {}
            if topic_id:
                filters['topic_id'] = topic_id
            if status:
                filters['status'] = status
            if user_id:
                filters['user_id'] = user_id
            
            # 获取文件列表
            files = await self.file_repo.list(
                page=page,
                page_size=page_size,
                filters=filters
            )
            
            # 获取总数
            all_files = await self.file_repo.list(page=1, page_size=1000, filters=filters)
            total = len(all_files)
            total_pages = (total + page_size - 1) // page_size
            
            # 转换为响应Schema
            file_responses = files_to_responses(files)
            
            return FileList(
                files=file_responses,
                total=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages
            )
            
        except Exception as e:
            self._handle_error(e, "list_files")
    
    async def get_topic_files(
        self, 
        topic_id: int, 
        page: int = 1, 
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> FileList:
        """获取主题下的文件列表"""
        try:
            # 检查主题是否存在
            topic = await self.topic_repo.get_topic_by_id(topic_id)
            if not topic:
                raise ValueError(f"主题 {topic_id} 不存在")
            
            # 获取文件列表（带排序）
            files = await self.file_repo.get_files_by_topic(
                topic_id=topic_id,
                page=page,
                page_size=page_size,
                sort_by=sort_by,
                sort_order=sort_order
            )
            
            # 获取总数
            all_files = await self.file_repo.get_files_by_topic(topic_id, page=1, page_size=1000)
            total = len(all_files)
            total_pages = (total + page_size - 1) // page_size
            
            # 转换为响应Schema
            file_responses = files_to_responses(files)
            
            logger.info(f"获取主题{topic_id}的文件列表成功: {len(file_responses)} 个文件")
            
            return FileList(
                files=file_responses,
                total=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages
            )
            
        except Exception as e:
            self._handle_error(e, f"get_topic_files_{topic_id}")
    
    async def search_files(self, query: str, limit: int = 10) -> List[FileResponse]:
        """搜索文件"""
        try:
            files = await self.file_repo.search_files(query, limit)
            return files_to_responses(files)
            
        except Exception as e:
            self._handle_error(e, f"search_files_{query}")
    
    async def get_file_download_url(self, file_id: str) -> Optional[str]:
        """获取文件下载URL"""
        try:
            file_record = await self.file_repo.get_file_by_id(file_id)
            if not file_record or not file_record.storage_key:
                return None
            
            # 生成下载URL
            download_url = await self.storage.generate_presigned_url(
                key=file_record.storage_key,
                expires_in=3600,  # 1小时
                method='GET'
            )
            
            return download_url
            
        except Exception as e:
            self._handle_error(e, f"get_file_download_url_{file_id}")
    
    # 私有方法
    def _generate_file_id(self) -> str:
        """生成文件ID"""
        import uuid
        return str(uuid.uuid4())
    
    async def _validate_upload_request(self, request: UploadUrlRequest) -> None:
        """验证上传请求"""
        # 检查文件名
        if not request.filename or len(request.filename) > 255:
            raise ValueError("文件名无效")
        
        # 检查文件大小
        if request.file_size and request.file_size > 100 * 1024 * 1024:  # 100MB
            raise ValueError("文件大小超过限制")
        
        # 检查主题是否存在
        if request.topic_id:
            topic = await self.topic_repo.get_topic_by_id(request.topic_id)
            if not topic:
                raise ValueError(f"主题 {request.topic_id} 不存在")
