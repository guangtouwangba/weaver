"""
存储接口

定义文件存储的抽象接口。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from logging_system import get_logger

logger = get_logger(__name__)


class StorageError(Exception):
    """存储操作异常"""
    pass

class IStorage(ABC):
    """存储接口"""
    
    @abstractmethod
    async def generate_signed_upload_url(self, 
                                       file_key: str,
                                       content_type: str,
                                       expires_in: int = 3600) -> Dict[str, Any]:
        """
        生成签名上传URL
        
        Args:
            file_key: 文件在存储中的唯一标识
            content_type: 文件MIME类型
            expires_in: URL过期时间（秒）
            
        Returns:
            包含签名URL和相关信息的字典
        """
        pass
    
    @abstractmethod
    async def generate_signed_download_url(self,
                                         file_key: str,
                                         expires_in: int = 3600) -> str:
        """
        生成签名下载URL
        
        Args:
            file_key: 文件标识
            expires_in: URL过期时间（秒）
            
        Returns:
            签名下载URL
        """
        pass
    
    @abstractmethod
    async def upload_file(self,
                         file_key: str,
                         file_data: bytes,
                         content_type: str,
                         metadata: Optional[Dict[str, str]] = None) -> str:
        """
        直接上传文件
        
        Args:
            file_key: 文件标识
            file_data: 文件数据
            content_type: 文件类型
            metadata: 文件元数据
            
        Returns:
            文件访问URL
        """
        pass
    
    @abstractmethod
    async def delete_file(self, file_key: str) -> bool:
        """
        删除文件
        
        Args:
            file_key: 文件标识
            
        Returns:
            是否删除成功
        """
        pass
    
    @abstractmethod
    async def file_exists(self, file_key: str) -> bool:
        """
        检查文件是否存在
        
        Args:
            file_key: 文件标识
            
        Returns:
            文件是否存在
        """
        pass
    
    @abstractmethod
    async def get_file_info(self, file_key: str) -> Optional[Dict[str, Any]]:
        """
        获取文件信息
        
        Args:
            file_key: 文件标识
            
        Returns:
            文件信息字典或None
        """
        pass
    
    @abstractmethod
    async def read_file(self, file_key: str) -> bytes:
        """
        读取文件内容
        
        Args:
            file_key: 文件标识
            
        Returns:
            文件内容字节数据
            
        Raises:
            StorageError: 文件不存在或读取失败
        """
        pass


def create_storage_service() -> IStorage:
    """创建存储服务实例"""
    try:
        from config import get_config
        config = get_config()

        if config.storage.provider == "local":
            # Import locally to avoid circular imports
            from .local_storage import LocalStorage
            return LocalStorage(
                storage_path=config.storage.local_path,
                base_url="http://localhost:8000"
            )
        elif config.storage.provider == "minio":
            # Import locally to avoid circular imports
            from .minio_storage import MinIOStorage
            logger.info("Using MinIO storage service")
            return MinIOStorage(
                endpoint=config.storage.minio_endpoint,
                access_key=config.storage.minio_access_key,
                secret_key=config.storage.minio_secret_key,
                secure=config.storage.minio_secure,
                bucket_name=config.storage.bucket_name
            )
        else:
            # 默认使用本地存储
            from .local_storage import LocalStorage
            logger.warning(f"Unknown storage provider: {config.storage.provider}, falling back to local storage")
            return LocalStorage()
    except Exception as e:
        logger.error(f"Failed to create storage service: {e}")
        # 如果配置加载失败，使用默认的本地存储
        from .local_storage import LocalStorage
        return LocalStorage()

