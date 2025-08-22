"""
文件上传接口

定义文件上传服务的抽象接口。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class IFileUploadService(ABC):
    """文件上传服务接口"""

    @abstractmethod
    async def generate_upload_url(
        self,
        filename: str,
        content_type: str,
        topic_id: Optional[int] = None,
        expires_in: int = 3600,
    ) -> Dict[str, Any]:
        """
        生成文件上传的签名URL

        Args:
            filename: 原始文件名
            content_type: 文件MIME类型
            topic_id: 关联的主题ID（可选）
            expires_in: URL过期时间（秒）

        Returns:
            包含上传URL和相关信息的字典
        """
        pass

    @abstractmethod
    async def confirm_upload(
        self,
        file_id: str,
        actual_size: Optional[int] = None,
        file_hash: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        确认文件上传完成

        Args:
            file_id: 文件ID
            actual_size: 实际文件大小
            file_hash: 文件哈希值

        Returns:
            确认结果
        """
        pass

    @abstractmethod
    async def get_download_url(self, file_id: str, expires_in: int = 3600) -> str:
        """
        获取文件下载URL

        Args:
            file_id: 文件ID
            expires_in: URL过期时间（秒）

        Returns:
            下载URL
        """
        pass

    @abstractmethod
    async def delete_file(self, file_id: str) -> bool:
        """
        删除文件

        Args:
            file_id: 文件ID

        Returns:
            是否删除成功
        """
        pass
