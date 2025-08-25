"""
文件Repository实现

处理文件相关的数据访问逻辑。
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc, select, update
from sqlalchemy.orm import selectinload

from modules.database.models import File
from modules.repository.base_repository import BaseRepository
from modules.repository.interfaces import IFileRepository
from modules.schemas.enums import FileStatus

logger = logging.getLogger(__name__)


class FileRepository(BaseRepository, IFileRepository):
    """文件Repository实现"""

    async def create_file(
        self,
        file_id: str,
        original_name: str,
        content_type: str,
        file_size: int = 0,
        **kwargs,
    ) -> File:
        """创建文件记录"""
        # 提供必需字段的默认值
        storage_bucket = kwargs.get("storage_bucket") or "rag-uploads"  # 默认存储桶
        storage_key = (
            kwargs.get("storage_key") or f"uploads/{file_id}/{original_name}"
        )  # 默认存储键

        file_record = File(
            id=file_id,
            filename=kwargs.get("filename", original_name),
            original_name=original_name,
            content_type=content_type,
            file_size=file_size,
            file_hash=kwargs.get("file_hash"),
            storage_bucket=storage_bucket,
            storage_key=storage_key,
            storage_url=kwargs.get("storage_url"),
            status=kwargs.get("status", FileStatus.UPLOADING),  # 使用枚举值
            topic_id=kwargs.get("topic_id"),
            access_level=kwargs.get("access_level", "private"),  # 默认访问级别
            download_count=0,  # 初始下载次数
            # 移除user_id和file_metadata，因为数据库模型中没有这些字段
        )

        self.session.add(file_record)
        await self.session.flush()
        await self.session.refresh(file_record)

        logger.info(f"创建文件记录: {original_name} (ID: {file_id})")
        return file_record

    async def get_file_by_id(self, file_id: str) -> Optional[File]:
        """根据ID获取文件"""
        result = await self.session.execute(
            select(File)
            .where(and_(File.id == file_id, File.is_deleted == False))
            .options(selectinload(File.topic))
        )
        return result.scalar_one_or_none()

    async def get_files_by_topic(
        self,
        topic_id: int,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> List[File]:
        """获取主题下的文件列表"""
        query = select(File).where(
            and_(File.topic_id == topic_id, File.is_deleted == False)
        )

        if status:
            query = query.where(File.status == status)

        # 添加排序
        sort_column = getattr(File, sort_by, File.created_at)
        if sort_order.lower() == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(sort_column)

        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def update_file_status(
        self,
        file_id: str,
        status: str,
        processing_status: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> Optional[File]:
        """更新文件状态"""
        file_record = await self.get_file_by_id(file_id)
        if not file_record:
            return None

        file_record.status = status
        if processing_status is not None:
            file_record.processing_status = processing_status
        if error_message is not None:
            file_record.error_message = error_message

        file_record.updated_at = datetime.utcnow()
        await self.session.flush()
        await self.session.refresh(file_record)

        logger.info(f"更新文件状态: {file_id} -> {status}")
        return file_record

    async def soft_delete_file(self, file_id: str) -> bool:
        """软删除文件"""
        result = await self.session.execute(
            update(File)
            .where(File.id == file_id)
            .values(is_deleted=True, updated_at=datetime.utcnow())
        )
        success = result.rowcount > 0

        if success:
            logger.info(f"软删除文件: {file_id}")

        return success

    async def get_files_by_status(self, status: str) -> List[File]:
        """根据状态获取文件"""
        result = await self.session.execute(
            select(File)
            .where(and_(File.status == status, File.is_deleted == False))
            .order_by(desc(File.created_at))
        )
        return result.scalars().all()

    async def get_files_by_user(self, user_id: int) -> List[File]:
        """获取用户的文件列表"""
        result = await self.session.execute(
            select(File)
            .where(and_(File.user_id == user_id, File.is_deleted == False))
            .order_by(desc(File.created_at))
        )
        return result.scalars().all()

    async def search_files(self, query: str, limit: int = 10) -> List[File]:
        """搜索文件"""
        search_query = (
            select(File)
            .where(
                and_(File.original_name.ilike(f"%{query}%"), File.is_deleted == False)
            )
            .limit(limit)
        )

        result = await self.session.execute(search_query)
        return result.scalars().all()

    # 实现基类抽象方法
    async def create(self, entity_data: Dict[str, Any]) -> File:
        return await self.create_file(**entity_data)

    async def get_by_id(self, entity_id: str) -> Optional[File]:
        return await self.get_file_by_id(entity_id)

    async def update(self, entity_id: str, updates: Dict[str, Any]) -> Optional[File]:
        file_record = await self.get_file_by_id(entity_id)
        if not file_record:
            return None

        for key, value in updates.items():
            if hasattr(file_record, key):
                setattr(file_record, key, value)

        file_record.updated_at = datetime.utcnow()
        await self.session.flush()
        await self.session.refresh(file_record)

        return file_record

    async def delete(self, entity_id: str) -> bool:
        return await self.soft_delete_file(entity_id)

    async def list(
        self,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
    ) -> List[File]:
        query = select(File).where(File.is_deleted == False)

        if filters:
            if "status" in filters:
                query = query.where(File.status == filters["status"])
            if "topic_id" in filters:
                query = query.where(File.topic_id == filters["topic_id"])
            if "user_id" in filters:
                query = query.where(File.user_id == filters["user_id"])

        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size).order_by(desc(File.created_at))

        result = await self.session.execute(query)
        return result.scalars().all()
