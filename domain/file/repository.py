"""
Domain File Repository Interface

定义文件领域的数据访问接口，遵循依赖倒置原则。
基础设施层将提供具体实现。
"""

from abc import ABC, abstractmethod
from typing import Optional, List
from .file import FileEntity


class IFileRepository(ABC):
    """文件实体仓储接口"""
    
    @abstractmethod
    async def save(self, file_entity: FileEntity) -> FileEntity:
        """保存文件实体"""
        pass
    
    @abstractmethod
    async def get_by_id(self, file_id: str) -> Optional[FileEntity]:
        """根据ID获取文件实体"""
        pass
    
    @abstractmethod
    async def get_by_owner(self, owner_id: str) -> List[FileEntity]:
        """根据拥有者ID获取文件列表"""
        pass
    
    @abstractmethod
    async def get_by_topic(self, topic_id: int) -> List[FileEntity]:
        """根据主题ID获取文件列表"""
        pass
    
    @abstractmethod
    async def update_status(self, file_id: str, status) -> bool:
        """更新文件状态"""
        pass
    
    @abstractmethod
    async def delete(self, file_id: str) -> bool:
        """删除文件实体"""
        pass
    
    @abstractmethod
    async def exists(self, file_id: str) -> bool:
        """检查文件是否存在"""
        pass


    @abstractmethod
    async def update_by_id(self, file_id: str, file_entity: FileEntity) -> bool:
        """根据ID更新文件实体"""
        pass


class IUploadSessionRepository(ABC):
    """上传会话仓储接口"""
    
    @abstractmethod
    async def save(self, session) -> None:
        """保存上传会话"""
        pass
    
    @abstractmethod
    async def get_by_id(self, session_id: str):
        """根据ID获取上传会话"""
        pass
    
    @abstractmethod
    async def update_status(self, session_id: str, status: str) -> bool:
        """更新会话状态"""
        pass
    
    @abstractmethod
    async def delete(self, session_id: str) -> bool:
        """删除上传会话"""
        pass