"""
Infrastructure File Repository Implementation

实现Domain层定义的文件仓储接口。
"""

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete

from domain.file import IFileRepository, IUploadSessionRepository, FileEntity
from infrastructure.database.models.file import File, FileUploadSession
from infrastructure.database.repositories import BaseRepository


class FileRepository(BaseRepository[File], IFileRepository):
    """文件仓储的基础设施层实现"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, File)
        self.session = session

    async def save(self, file_entity: FileEntity) -> FileEntity:
        """保存文件实体到数据库"""
        import uuid
        from domain.file import FileStatus as DomainFileStatus
        from infrastructure.database.models.file import FileStatus as ModelFileStatus
        
        # 确保有ID
        if not hasattr(file_entity, 'id') or not file_entity.id:
            file_entity.id = str(uuid.uuid4())
        
        # 转换为UUID对象（如果是字符串）
        file_uuid = uuid.UUID(file_entity.id) if isinstance(file_entity.id, str) else file_entity.id
        
        # 创建数据库模型
        db_file = File(
            id=file_uuid,
            original_name=file_entity.metadata.original_name if file_entity.metadata else "unknown",
            file_size=file_entity.metadata.file_size if file_entity.metadata else 0,
            content_type=file_entity.metadata.content_type if file_entity.metadata else "application/octet-stream",
            storage_bucket=file_entity.storage_location.bucket if file_entity.storage_location else "default",
            storage_key=file_entity.storage_location.key if file_entity.storage_location else f"uploads/{file_entity.id}",
            is_deleted=False,
            topic_id=file_entity.topic_id,
            status=self._convert_domain_status_to_model(file_entity.status)
        )
        
        self.session.add(db_file)
        await self.session.commit()
        await self.session.refresh(db_file)
        
        # 更新实体ID为字符串格式
        file_entity.id = str(db_file.id)
        
        return file_entity

    async def get_by_id(self, file_id: str) -> Optional[FileEntity]:
        """根据ID获取文件实体"""
        import uuid
        
        # 转换字符串ID为UUID对象
        try:
            file_uuid = uuid.UUID(file_id) if isinstance(file_id, str) else file_id
        except ValueError:
            return None
        
        stmt = select(File).where(File.id == file_uuid)
        result = await self.session.execute(stmt)
        db_file = result.scalar_one_or_none()
        
        if not db_file:
            return None
        
        return self._to_domain_entity(db_file)

    async def get_by_owner(self, owner_id: str) -> List[FileEntity]:
        """根据拥有者获取文件列表"""
        stmt = select(File).where(File.owner_id == owner_id)
        result = await self.session.execute(stmt)
        db_files = result.scalars().all()
        
        return [self._to_domain_entity(db_file) for db_file in db_files]

    async def get_by_topic(self, topic_id: int) -> List[FileEntity]:
        """根据主题获取文件列表"""
        stmt = select(File).where(File.topic_id == topic_id)
        result = await self.session.execute(stmt)
        db_files = result.scalars().all()
        
        return [self._to_domain_entity(db_file) for db_file in db_files]

    async def update_status(self, file_id: str, status) -> bool:
        """更新文件状态"""
        stmt = update(File).where(File.id == file_id).values(status=status)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0

    async def delete(self, file_id: str) -> bool:
        """删除文件"""
        stmt = delete(File).where(File.id == file_id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0

    async def exists(self, file_id: str) -> bool:
        """检查文件是否存在"""
        stmt = select(File.id).where(File.id == file_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def update_by_id(self, file_id: str, file_entity: FileEntity) -> bool:
        """根据ID更新文件实体"""
        import uuid

        # 转换字符串ID为UUID对象
        try:
            file_uuid = uuid.UUID(file_id) if isinstance(file_id, str) else file_id
        except ValueError:
            return False

        # 创建更新语句
        stmt = (
            update(File)
            .where(File.id == file_uuid)
            .values(
                original_name=file_entity.metadata.original_name,
                file_size=file_entity.metadata.file_size,
                content_type=file_entity.metadata.content_type,
                storage_bucket=file_entity.storage_location.bucket,
                storage_key=file_entity.storage_location.key,
                status=self._convert_domain_status_to_model(file_entity.status)
            )
        )

        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0

    def _convert_domain_status_to_model(self, domain_status):
        """转换Domain状态到Model状态"""
        from domain.file import FileStatus as DomainFileStatus
        from infrastructure.database.models.file import FileStatus as ModelFileStatus
        
        # 使用Model枚举对象
        status_mapping = {
            DomainFileStatus.UPLOADING: ModelFileStatus.uploading,
            DomainFileStatus.AVAILABLE: ModelFileStatus.available, 
            DomainFileStatus.PROCESSING: ModelFileStatus.processing,
            DomainFileStatus.FAILED: ModelFileStatus.failed,
            DomainFileStatus.DELETED: ModelFileStatus.deleted,
            DomainFileStatus.QUARANTINED: ModelFileStatus.quarantined,
        }
        return status_mapping.get(domain_status, ModelFileStatus.uploading)
    
    def _convert_model_status_to_domain(self, model_status):
        """转换Model状态到Domain状态"""
        from domain.file import FileStatus as DomainFileStatus
        from infrastructure.database.models.file import FileStatus as ModelFileStatus
        
        # 处理从数据库返回的枚举对象
        status_mapping = {
            ModelFileStatus.uploading: DomainFileStatus.UPLOADING,
            ModelFileStatus.available: DomainFileStatus.AVAILABLE,
            ModelFileStatus.processing: DomainFileStatus.PROCESSING,
            ModelFileStatus.failed: DomainFileStatus.FAILED,
            ModelFileStatus.deleted: DomainFileStatus.DELETED,
            ModelFileStatus.quarantined: DomainFileStatus.QUARANTINED,
        }
        
        # 如果是字符串值，需要转换为枚举对象
        if isinstance(model_status, str):
            try:
                model_status = ModelFileStatus(model_status)
            except ValueError:
                # 处理数据库中可能存在的archived值
                if model_status == "archived":
                    return DomainFileStatus.QUARANTINED
                return DomainFileStatus.UPLOADING
        
        return status_mapping.get(model_status, DomainFileStatus.UPLOADING)

    def _to_domain_entity(self, db_file: File) -> FileEntity:
        """将数据库模型转换为Domain实体"""
        from domain.file import (
            FileEntity, FileMetadata, AccessPermission, StorageLocation, AccessLevel
        )
        from datetime import datetime
        
        # 创建文件元数据
        metadata = FileMetadata(
            original_name=db_file.original_name,
            file_size=db_file.file_size,
            content_type=db_file.content_type,
            category=None,  # 数据库模型中可能没有这个字段
            tags=[],  # 暂时为空
            custom_metadata={}  # 暂时为空
        )
        
        # 创建访问权限（简化实现）
        access_permission = AccessPermission(
            level=AccessLevel.PRIVATE,  # 默认私有
            allowed_users=set()
        )
        
        # 创建存储位置
        storage_location = StorageLocation(
            bucket=db_file.storage_bucket,
            key=db_file.storage_key,
            provider="minio"  # 默认为minio
        )
        
        # 创建实体
        entity = FileEntity(
            owner_id="unknown",  # 需要从数据库模型中获取
            metadata=metadata,
            status=self._convert_model_status_to_domain(db_file.status),
            access_permission=access_permission,
            topic_id=db_file.topic_id,
            download_count=0,
            created_at=db_file.created_at if hasattr(db_file, 'created_at') else datetime.now(),
            updated_at=db_file.updated_at if hasattr(db_file, 'updated_at') else datetime.now()
        )
        
        # 设置ID和存储位置
        entity.id = str(db_file.id)
        entity.storage_location = storage_location
        
        return entity


class UploadSessionRepository(BaseRepository[FileUploadSession], IUploadSessionRepository):
    """上传会话仓储的基础设施层实现"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, FileUploadSession)
        self.session = session

    async def save(self, session_entity) -> None:
        """保存上传会话"""
        # 简化实现
        pass

    async def get_by_id(self, session_id: str):
        """根据ID获取上传会话"""
        # 简化实现
        return None

    async def update_status(self, session_id: str, status: str) -> bool:
        """更新会话状态"""
        # 简化实现
        return True

    async def delete(self, session_id: str) -> bool:
        """删除上传会话"""
        # 简化实现
        return True
