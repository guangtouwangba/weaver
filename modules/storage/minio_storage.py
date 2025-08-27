"""
MinIO存储实现

基于MinIO的真实存储服务实现。
"""

import urllib.parse
import time
from datetime import datetime, timedelta
from io import BytesIO
from typing import Any, Dict, Optional

try:
    import urllib3
    URLLIB3_AVAILABLE = True
except ImportError:
    URLLIB3_AVAILABLE = False

from minio import Minio
from minio.error import S3Error

from logging_system import get_logger, log_errors, log_execution_time
from modules.storage.base import IStorage, StorageError

logger = get_logger(__name__)


class MinIOStorage(IStorage):
    """MinIO存储实现"""

    def __init__(
        self,
        endpoint: str = "localhost:9000",
        access_key: str = "minioadmin",
        secret_key: str = "minioadmin123",
        bucket_name: str = "rag-uploads",
        secure: bool = False,
        connection_timeout: int = 30,
        max_retry_attempts: int = 3,
    ):
        """
        初始化MinIO存储

        Args:
            endpoint: MinIO服务端点
            access_key: 访问密钥
            secret_key: 私密密钥
            bucket_name: 存储桶名称
            secure: 是否使用HTTPS
            connection_timeout: 连接超时时间（秒）
            max_retry_attempts: 最大重试次数
        """
        self.endpoint = endpoint
        self.bucket_name = bucket_name
        self.secure = secure
        self.connection_timeout = connection_timeout
        self.max_retry_attempts = max_retry_attempts

        # 初始化MinIO客户端
        self.client = Minio(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
        )
        
        # 设置更短的超时时间以避免长时间阻塞
        if URLLIB3_AVAILABLE and hasattr(self.client, '_http'):
            try:
                self.client._http.timeout = urllib3.util.Timeout(
                    connect=5.0,  # 连接超时5秒
                    read=10.0     # 读取超时10秒
                )
            except Exception as e:
                logger.warning(f"Could not set HTTP timeout: {e}")

        # 延迟初始化存储桶 - 使用重试逻辑
        self._bucket_initialized = False
        
        # 不在初始化时连接MinIO，而是在首次使用时连接
        logger.info(f"MinIO storage initialized for endpoint {endpoint}, bucket will be created on first use")

    def _ensure_bucket_exists(self):
        """确保存储桶存在（带重试逻辑）"""
        if self._bucket_initialized:
            return
            
        last_exception = None
        
        for attempt in range(self.max_retry_attempts):
            try:
                # 检查存储桶是否存在
                if not self.client.bucket_exists(self.bucket_name):
                    self.client.make_bucket(self.bucket_name)
                    logger.info(f"Created bucket: {self.bucket_name}")
                else:
                    logger.debug(f"Bucket already exists: {self.bucket_name}")
                
                # 成功连接，标记为已初始化
                self._bucket_initialized = True
                return
                
            except (S3Error, Exception) as e:
                last_exception = e
                logger.warning(
                    f"Attempt {attempt + 1}/{self.max_retry_attempts} failed to connect to MinIO: {e}"
                )
                
                if attempt < self.max_retry_attempts - 1:
                    # 指数退避重试
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    # 最后一次尝试失败
                    error_msg = f"Failed to connect to MinIO after {self.max_retry_attempts} attempts: {last_exception}"
                    logger.error(error_msg)
                    raise StorageError(error_msg)
                    
    def _lazy_ensure_bucket(self):
        """延迟确保存储桶存在（用于API调用前）"""
        if not self._bucket_initialized:
            try:
                self._ensure_bucket_exists()
            except StorageError:
                # 如果初始化失败，记录警告但不抛出异常
                # 让具体的API调用来处理连接问题
                logger.warning("MinIO bucket initialization failed, will retry on next API call")

    async def generate_presigned_url(
        self, key: str, content_type: str = None, expires_in: int = 3600
    ) -> str:
        """生成预签名上传URL（兼容方法）"""
        result = await self.generate_signed_upload_url(
            key, content_type or "application/octet-stream", expires_in
        )
        return result["upload_url"]

    @log_execution_time(threshold_ms=100)
    @log_errors()
    async def generate_signed_upload_url(
        self, file_key: str, content_type: str, expires_in: int = 3600
    ) -> Dict[str, Any]:
        """生成签名上传URL"""
        
        # 确保MinIO连接可用
        self._lazy_ensure_bucket()

        try:
            # URL编码文件键以处理中文文件名
            encoded_key = urllib.parse.quote(file_key, safe="/")

            # 生成预签名PUT URL
            upload_url = self.client.presigned_put_object(
                bucket_name=self.bucket_name,
                object_name=file_key,  # MinIO内部会处理编码
                expires=timedelta(seconds=expires_in),
            )

            result = {
                "upload_url": upload_url,
                "method": "PUT",
                "headers": {"Content-Type": content_type},
                "fields": {},
                "bucket": self.bucket_name,
                "key": file_key,
                "encoded_key": encoded_key,
                "expires_at": (
                    datetime.utcnow() + timedelta(seconds=expires_in)
                ).isoformat(),
            }

            logger.info(f"Generated signed upload URL for: {file_key}")
            return result

        except S3Error as e:
            logger.error(f"Failed to generate signed upload URL for {file_key}: {e}")
            raise StorageError(f"Signed URL generation failed: {e}")

    @log_execution_time(threshold_ms=100)
    @log_errors()
    async def generate_signed_download_url(
        self, file_key: str, expires_in: int = 3600
    ) -> str:
        """生成签名下载URL"""

        try:
            download_url = self.client.presigned_get_object(
                bucket_name=self.bucket_name,
                object_name=file_key,
                expires=timedelta(seconds=expires_in),
            )

            logger.info(f"Generated signed download URL for: {file_key}")
            return download_url

        except S3Error as e:
            logger.error(f"Failed to generate signed download URL for {file_key}: {e}")
            raise StorageError(f"Download URL generation failed: {e}")

    @log_execution_time(threshold_ms=1000)
    @log_errors()
    async def upload_file(
        self,
        file_key: str,
        file_data: bytes,
        content_type: str,
        metadata: Optional[Dict[str, str]] = None,
    ) -> str:
        """直接上传文件"""

        try:
            # 创建文件流
            file_stream = BytesIO(file_data)
            file_size = len(file_data)

            # 上传文件
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=file_key,
                data=file_stream,
                length=file_size,
                content_type=content_type,
                metadata=metadata,
            )

            # 生成访问URL
            if self.secure:
                protocol = "https"
            else:
                protocol = "http"

            encoded_key = urllib.parse.quote(file_key, safe="/")
            access_url = (
                f"{protocol}://{self.endpoint}/{self.bucket_name}/{encoded_key}"
            )

            logger.info(f"Uploaded file: {file_key} ({file_size} bytes)")
            return access_url

        except S3Error as e:
            logger.error(f"Failed to upload file {file_key}: {e}")
            raise StorageError(f"File upload failed: {e}")

    async def delete_file(self, file_key: str) -> bool:
        """删除文件"""

        try:
            self.client.remove_object(
                bucket_name=self.bucket_name, object_name=file_key
            )

            logger.info(f"Deleted file: {file_key}")
            return True

        except S3Error as e:
            logger.error(f"Failed to delete file {file_key}: {e}")
            return False

    async def file_exists(self, file_key: str) -> bool:
        """检查文件是否存在"""

        try:
            self.client.stat_object(bucket_name=self.bucket_name, object_name=file_key)
            return True

        except S3Error as e:
            if e.code == "NoSuchKey":
                return False
            logger.error(f"Error checking file existence {file_key}: {e}")
            return False

    async def get_file_info(self, file_key: str) -> Optional[Dict[str, Any]]:
        """获取文件信息"""

        try:
            stat = self.client.stat_object(
                bucket_name=self.bucket_name, object_name=file_key
            )

            # 生成访问URL
            if self.secure:
                protocol = "https"
            else:
                protocol = "http"

            encoded_key = urllib.parse.quote(file_key, safe="/")
            access_url = (
                f"{protocol}://{self.endpoint}/{self.bucket_name}/{encoded_key}"
            )

            file_info = {
                "file_key": file_key,
                "size": stat.size,
                "content_type": stat.content_type,
                "last_modified": (
                    stat.last_modified.isoformat() if stat.last_modified else None
                ),
                "etag": stat.etag,
                "metadata": stat.metadata,
                "access_url": access_url,
                "bucket": self.bucket_name,
            }

            # 计算文件哈希（如果有ETag）
            if stat.etag:
                file_info["hash"] = stat.etag.strip('"')

            return file_info

        except S3Error as e:
            if e.code == "NoSuchKey":
                return None
            logger.error(f"Failed to get file info for {file_key}: {e}")
            return None

    async def read_file(self, file_key: str) -> bytes:
        """读取文件内容"""

        try:
            # 获取文件对象
            response = self.client.get_object(
                bucket_name=self.bucket_name, object_name=file_key
            )

            # 读取所有内容
            file_content = response.read()

            logger.debug(
                f"Successfully read file {file_key} ({len(file_content)} bytes)"
            )
            return file_content

        except S3Error as e:
            if e.code == "NoSuchKey":
                raise StorageError(f"文件不存在: {file_key}")
            logger.error(f"Failed to read file {file_key}: {e}")
            raise StorageError(f"读取文件失败: {e}")
        finally:
            # 确保响应被关闭
            if "response" in locals():
                response.close()
                response.release_conn()

    def get_bucket_info(self) -> Dict[str, Any]:
        """获取存储桶信息"""

        try:
            buckets = self.client.list_buckets()
            bucket_info = None

            for bucket in buckets:
                if bucket.name == self.bucket_name:
                    bucket_info = {
                        "name": bucket.name,
                        "creation_date": (
                            bucket.creation_date.isoformat()
                            if bucket.creation_date
                            else None
                        ),
                    }
                    break

            return {
                "endpoint": self.endpoint,
                "bucket": bucket_info,
                "secure": self.secure,
            }

        except S3Error as e:
            logger.error(f"Failed to get bucket info: {e}")
            return {"error": str(e)}
            
    async def health_check(self) -> Dict[str, Any]:
        """检查MinIO服务健康状态"""
        try:
            # 快速健康检查 - 尝试列出buckets
            start_time = time.time()
            buckets = self.client.list_buckets()
            response_time = (time.time() - start_time) * 1000  # ms
            
            # 检查我们的bucket是否存在
            bucket_exists = any(bucket.name == self.bucket_name for bucket in buckets)
            
            return {
                "status": "healthy",
                "endpoint": self.endpoint,
                "bucket_name": self.bucket_name,
                "bucket_exists": bucket_exists,
                "response_time_ms": response_time,
                "connected": True,
                "total_buckets": len(buckets),
                "initialized": self._bucket_initialized
            }
            
        except Exception as e:
            return {
                "status": "unhealthy", 
                "endpoint": self.endpoint,
                "bucket_name": self.bucket_name,
                "error": str(e),
                "connected": False,
                "initialized": self._bucket_initialized
            }
