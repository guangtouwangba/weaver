"""
存储配置模块

提供对象存储相关的配置管理功能，支持多种存储后端。
"""

import os
from dataclasses import dataclass
from typing import Optional, Dict, Any
from enum import Enum


class StorageProvider(Enum):
    """存储提供商枚举"""

    MINIO = "minio"
    AWS_S3 = "aws_s3"
    GOOGLE_GCS = "google_gcs"
    ALIBABA_OSS = "alibaba_oss"
    LOCAL = "local"


@dataclass
class StorageConfig:
    """存储配置"""

    # 存储提供商
    provider: StorageProvider = StorageProvider.MINIO

    # 连接配置
    endpoint_url: Optional[str] = None
    access_key: Optional[str] = None
    secret_key: Optional[str] = None
    region: str = "us-east-1"

    # 桶配置
    bucket_name: str = "rag-uploads"
    bucket_prefix: str = ""  # 桶内前缀

    # 安全配置
    use_ssl: bool = True
    verify_ssl: bool = True

    # 上传配置
    multipart_threshold: int = 64 * 1024 * 1024  # 64MB
    multipart_chunksize: int = 16 * 1024 * 1024  # 16MB
    max_concurrency: int = 10

    # 签名URL配置
    presigned_url_expires: int = 3600  # 1小时

    # 本地存储配置 (当provider为LOCAL时使用)
    local_path: str = "./uploads"

    # 缓存配置
    enable_cache: bool = True
    cache_ttl: int = 300  # 5分钟

    def get_connection_params(self) -> Dict[str, Any]:
        """获取存储连接参数"""
        params = {
            "region": self.region,
            "use_ssl": self.use_ssl,
            "verify_ssl": self.verify_ssl,
        }

        if self.provider == StorageProvider.MINIO:
            params.update(
                {
                    "endpoint_url": self.endpoint_url or "http://localhost:9000",
                    "aws_access_key_id": self.access_key,
                    "aws_secret_access_key": self.secret_key,
                }
            )

        elif self.provider == StorageProvider.AWS_S3:
            params.update(
                {
                    "aws_access_key_id": self.access_key,
                    "aws_secret_access_key": self.secret_key,
                }
            )
            if self.endpoint_url:
                params["endpoint_url"] = self.endpoint_url

        elif self.provider == StorageProvider.GOOGLE_GCS:
            # Google Cloud Storage特定配置
            if self.secret_key:  # 这里secret_key可以是服务账号JSON路径
                params["google_application_credentials"] = self.secret_key

        elif self.provider == StorageProvider.ALIBABA_OSS:
            params.update(
                {
                    "endpoint_url": self.endpoint_url,
                    "access_key_id": self.access_key,
                    "access_key_secret": self.secret_key,
                }
            )

        elif self.provider == StorageProvider.LOCAL:
            params.update({"local_path": self.local_path})

        return params

    def get_upload_config(self) -> Dict[str, Any]:
        """获取上传配置"""
        return {
            "multipart_threshold": self.multipart_threshold,
            "multipart_chunksize": self.multipart_chunksize,
            "max_concurrency": self.max_concurrency,
            "use_threads": True,
        }

    @classmethod
    def from_env(cls) -> "StorageConfig":
        """从环境变量创建配置"""
        provider_str = os.getenv("STORAGE_PROVIDER", "minio").lower()
        try:
            provider = StorageProvider(provider_str)
        except ValueError:
            provider = StorageProvider.MINIO

        return cls(
            provider=provider,
            endpoint_url=os.getenv("STORAGE_ENDPOINT_URL"),
            access_key=os.getenv("STORAGE_ACCESS_KEY"),
            secret_key=os.getenv("STORAGE_SECRET_KEY"),
            region=os.getenv("STORAGE_REGION", "us-east-1"),
            bucket_name=os.getenv("STORAGE_BUCKET_NAME", "rag-uploads"),
            bucket_prefix=os.getenv("STORAGE_BUCKET_PREFIX", ""),
            use_ssl=os.getenv("STORAGE_USE_SSL", "true").lower() == "true",
            verify_ssl=os.getenv("STORAGE_VERIFY_SSL", "true").lower() == "true",
            multipart_threshold=int(
                os.getenv("STORAGE_MULTIPART_THRESHOLD", str(64 * 1024 * 1024))
            ),
            multipart_chunksize=int(
                os.getenv("STORAGE_MULTIPART_CHUNKSIZE", str(16 * 1024 * 1024))
            ),
            max_concurrency=int(os.getenv("STORAGE_MAX_CONCURRENCY", "10")),
            presigned_url_expires=int(
                os.getenv("STORAGE_PRESIGNED_URL_EXPIRES", "3600")
            ),
            local_path=os.getenv("STORAGE_LOCAL_PATH", "./uploads"),
            enable_cache=os.getenv("STORAGE_ENABLE_CACHE", "true").lower() == "true",
            cache_ttl=int(os.getenv("STORAGE_CACHE_TTL", "300")),
        )


# 默认存储配置实例
default_storage_config = StorageConfig.from_env()
