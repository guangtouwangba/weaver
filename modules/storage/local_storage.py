"""
本地文件存储实现

用于开发环境的本地文件系统存储。
"""

import os
import logging
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from uuid import uuid4

from .base import IStorage, StorageError

logger = logging.getLogger(__name__)

class LocalStorage(IStorage):
    """本地文件存储实现"""
    
    def __init__(self, storage_path: str = "./uploads", base_url: str = "http://localhost:8000"):
        """
        初始化本地存储
        
        Args:
            storage_path: 本地存储路径
            base_url: 访问文件的基础URL
        """
        self.storage_path = Path(storage_path)
        self.base_url = base_url.rstrip('/')
        
        # 确保存储目录存在
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"本地存储初始化: {self.storage_path}")
    
    def _get_file_path(self, file_key: str) -> Path:
        """获取文件的完整路径"""
        return self.storage_path / file_key
    
    async def generate_signed_upload_url(self, 
                                       file_key: str,
                                       content_type: str,
                                       expires_in: int = 3600) -> Dict[str, Any]:
        """生成本地上传URL"""
        
        # 生成上传令牌
        upload_token = str(uuid4())
        
        # 本地上传通过特殊的API端点
        upload_url = f"{self.base_url}/api/v1/files/upload/local"
        
        result = {
            "upload_url": upload_url,
            "method": "POST",
            "headers": {
                "Content-Type": "multipart/form-data"
            },
            "fields": {
                "file_key": file_key,
                "upload_token": upload_token,
                "content_type": content_type
            },
            "bucket": "local",
            "key": file_key,
            "expires_at": (datetime.utcnow() + timedelta(seconds=expires_in)).isoformat(),
            "upload_token": upload_token
        }
        
        logger.info(f"生成本地上传URL: {file_key}")
        return result
    
    async def generate_signed_download_url(self,
                                         file_key: str,
                                         expires_in: int = 3600) -> str:
        """生成本地下载URL"""
        
        download_url = f"{self.base_url}/api/v1/files/download/{file_key}?token={uuid4()}"
        
        logger.info(f"生成本地下载URL: {file_key}")
        return download_url
    
    async def upload_file(self,
                         file_key: str,
                         file_data: bytes,
                         content_type: str,
                         metadata: Optional[Dict[str, str]] = None) -> str:
        """上传文件到本地存储"""
        
        try:
            file_path = self._get_file_path(file_key)
            
            # 确保父目录存在
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 写入文件
            with open(file_path, 'wb') as f:
                f.write(file_data)
            
            # 生成文件哈希
            file_hash = hashlib.sha256(file_data).hexdigest()
            
            # 保存元数据
            if metadata:
                metadata_path = file_path.with_suffix(file_path.suffix + '.meta')
                import json
                with open(metadata_path, 'w') as f:
                    json.dump({
                        'content_type': content_type,
                        'size': len(file_data),
                        'hash': file_hash,
                        'uploaded_at': datetime.utcnow().isoformat(),
                        **metadata
                    }, f)
            
            access_url = f"{self.base_url}/api/v1/files/download/{file_key}"
            
            logger.info(f"本地上传文件: {file_key} ({len(file_data)} bytes)")
            return access_url
            
        except Exception as e:
            logger.error(f"本地文件上传失败: {e}")
            raise StorageError(f"本地文件上传失败: {e}")
    
    async def delete_file(self, file_key: str) -> bool:
        """删除本地文件"""
        
        try:
            file_path = self._get_file_path(file_key)
            
            if file_path.exists():
                file_path.unlink()
                
                # 删除元数据文件
                metadata_path = file_path.with_suffix(file_path.suffix + '.meta')
                if metadata_path.exists():
                    metadata_path.unlink()
                
                logger.info(f"本地删除文件: {file_key}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"本地文件删除失败: {e}")
            return False
    
    async def file_exists(self, file_key: str) -> bool:
        """检查本地文件是否存在"""
        file_path = self._get_file_path(file_key)
        exists = file_path.exists()
        logger.debug(f"检查本地文件存在: {file_key} = {exists}")
        return exists
    
    async def get_file_info(self, file_key: str) -> Optional[Dict[str, Any]]:
        """获取本地文件信息"""
        
        try:
            file_path = self._get_file_path(file_key)
            
            if not file_path.exists():
                return None
            
            # 基础文件信息
            stat = file_path.stat()
            file_info = {
                'file_key': file_key,
                'size': stat.st_size,
                'modified_at': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'access_url': f"{self.base_url}/api/v1/files/download/{file_key}"
            }
            
            # 尝试读取元数据
            metadata_path = file_path.with_suffix(file_path.suffix + '.meta')
            if metadata_path.exists():
                import json
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                    file_info.update(metadata)
            
            return file_info
            
        except Exception as e:
            logger.error(f"获取本地文件信息失败: {e}")
            return None
