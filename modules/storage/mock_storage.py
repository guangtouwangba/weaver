"""
模拟存储实现

用于开发和测试环境的简单存储模拟。
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from uuid import uuid4

from .interface import IStorage, StorageError

logger = logging.getLogger(__name__)

class MockStorage(IStorage):
    """模拟存储实现"""
    
    def __init__(self, base_url: str = "http://localhost:9000"):
        """
        初始化模拟存储
        
        Args:
            base_url: 模拟存储的基础URL
        """
        self.base_url = base_url.rstrip('/')
        self.bucket_name = "rag-uploads"
        self._files = {}  # 模拟文件存储
        
    async def generate_presigned_url(self, 
                                    key: str,
                                    content_type: str = None,
                                    expires_in: int = 3600) -> str:
        """生成预签名上传URL（兼容方法）"""
        result = await self.generate_signed_upload_url(key, content_type or "application/octet-stream", expires_in)
        return result["upload_url"]
    
    async def generate_signed_upload_url(self, 
                                       file_key: str,
                                       content_type: str,
                                       expires_in: int = 3600) -> Dict[str, Any]:
        """生成模拟的签名上传URL"""
        
        # 生成模拟的签名URL
        upload_url = f"{self.base_url}/{self.bucket_name}/{file_key}"
        
        # 生成临时令牌
        upload_token = str(uuid4())
        
        result = {
            "upload_url": upload_url,
            "method": "PUT",
            "headers": {
                "Content-Type": content_type,
                "X-Upload-Token": upload_token
            },
            "fields": {},
            "bucket": self.bucket_name,
            "key": file_key,
            "expires_at": (datetime.utcnow() + timedelta(seconds=expires_in)).isoformat(),
            "upload_token": upload_token
        }
        
        logger.info(f"生成签名上传URL: {file_key}")
        return result
    
    async def generate_signed_download_url(self,
                                         file_key: str,
                                         expires_in: int = 3600) -> str:
        """生成模拟的签名下载URL"""
        
        download_url = f"{self.base_url}/{self.bucket_name}/{file_key}?token={uuid4()}&expires={expires_in}"
        
        logger.info(f"生成签名下载URL: {file_key}")
        return download_url
    
    async def upload_file(self,
                         file_key: str,
                         file_data: bytes,
                         content_type: str,
                         metadata: Optional[Dict[str, str]] = None) -> str:
        """模拟文件上传"""
        
        # 模拟存储文件信息
        self._files[file_key] = {
            "size": len(file_data),
            "content_type": content_type,
            "metadata": metadata or {},
            "uploaded_at": datetime.utcnow().isoformat(),
            "data": file_data  # 在实际实现中不会存储原始数据
        }
        
        access_url = f"{self.base_url}/{self.bucket_name}/{file_key}"
        
        logger.info(f"模拟上传文件: {file_key} ({len(file_data)} bytes)")
        return access_url
    
    async def delete_file(self, file_key: str) -> bool:
        """模拟删除文件"""
        
        if file_key in self._files:
            del self._files[file_key]
            logger.info(f"模拟删除文件: {file_key}")
            return True
        
        return False
    
    async def file_exists(self, file_key: str) -> bool:
        """检查文件是否存在"""
        exists = file_key in self._files
        logger.debug(f"检查文件存在: {file_key} = {exists}")
        return exists
    
    async def get_file_info(self, file_key: str) -> Optional[Dict[str, Any]]:
        """获取文件信息"""
        
        if file_key not in self._files:
            return None
        
        file_info = self._files[file_key].copy()
        # 不返回原始数据
        file_info.pop('data', None)
        file_info['file_key'] = file_key
        file_info['access_url'] = f"{self.base_url}/{self.bucket_name}/{file_key}"
        
        return file_info
