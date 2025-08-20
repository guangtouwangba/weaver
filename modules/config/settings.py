"""
应用配置设置

使用pydantic管理配置，支持从环境变量和.env文件读取。
"""

import os
import getpass
from typing import Optional, List
from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings


class DatabaseConfig(BaseModel):
    """数据库配置"""
    
    host: str = Field(default="localhost", description="数据库主机")
    port: int = Field(default=5432, description="数据库端口") 
    name: str = Field(default="ragdb", description="数据库名称")
    user: str = Field(default_factory=getpass.getuser, description="数据库用户")
    password: Optional[str] = Field(default=None, description="数据库密码")
    driver: str = Field(default="asyncpg", description="数据库驱动")
    
    # 连接池配置
    pool_size: int = Field(default=5, description="连接池大小")
    max_overflow: int = Field(default=10, description="最大溢出连接数")
    pool_timeout: int = Field(default=30, description="连接池超时时间")
    pool_recycle: int = Field(default=3600, description="连接回收时间")
    
    # 其他配置
    echo: bool = Field(default=False, description="是否显示SQL日志")
    
    @property
    def url(self) -> str:
        """构建数据库连接URL"""
        if self.password:
            return f"postgresql+{self.driver}://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"
        else:
            return f"postgresql+{self.driver}://{self.user}@{self.host}:{self.port}/{self.name}"
    
    @validator('driver')
    def validate_driver(cls, v):
        """验证数据库驱动"""
        allowed_drivers = ['asyncpg', 'psycopg2']
        if v not in allowed_drivers:
            raise ValueError(f"Driver must be one of {allowed_drivers}")
        return v


class StorageConfig(BaseModel):
    """存储配置"""
    
    provider: str = Field(default="local", description="存储提供商")
    bucket_name: str = Field(default="rag-files", description="存储桶名称")
    
    # 本地存储
    local_path: str = Field(default="./storage", description="本地存储路径")
    
    # MinIO配置
    minio_endpoint: str = Field(default="localhost:9000", description="MinIO端点")
    minio_access_key: str = Field(default="minioadmin", description="MinIO访问密钥")
    minio_secret_key: str = Field(default="minioadmin123", description="MinIO密钥")
    minio_secure: bool = Field(default=False, description="是否使用HTTPS")
    
    # AWS S3配置
    aws_access_key_id: Optional[str] = Field(default=None, description="AWS访问密钥ID")
    aws_secret_access_key: Optional[str] = Field(default=None, description="AWS密钥")
    aws_region: str = Field(default="us-east-1", description="AWS区域")
    
    @validator('provider')
    def validate_provider(cls, v):
        """验证存储提供商"""
        allowed_providers = ['local', 'minio', 's3', 'gcs', 'oss']
        if v not in allowed_providers:
            raise ValueError(f"Provider must be one of {allowed_providers}")
        return v


class LoggingConfig(BaseModel):
    """日志配置"""
    
    level: str = Field(default="INFO", description="日志级别")
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="日志格式"
    )
    file: Optional[str] = Field(default=None, description="日志文件路径")
    max_size: int = Field(default=10, description="日志文件最大大小(MB)")
    backup_count: int = Field(default=5, description="日志文件备份数量")


class AppConfig(BaseSettings):
    """应用程序主配置"""
    
    # 应用基础配置
    app_name: str = Field(default="RAG API", description="应用名称")
    app_version: str = Field(default="2.0.0", description="应用版本")
    debug: bool = Field(default=False, description="调试模式")
    host: str = Field(default="0.0.0.0", description="服务器主机")
    port: int = Field(default=8000, description="服务器端口")
    
    # 环境配置
    environment: str = Field(default="development", description="运行环境")
    
    # CORS配置
    cors_origins: List[str] = Field(default=["*"], description="允许的CORS源")
    cors_methods: List[str] = Field(default=["*"], description="允许的CORS方法")
    cors_headers: List[str] = Field(default=["*"], description="允许的CORS头")
    
    # 子配置
    database: DatabaseConfig = Field(default_factory=DatabaseConfig, description="数据库配置")
    storage: StorageConfig = Field(default_factory=StorageConfig, description="存储配置")
    logging: LoggingConfig = Field(default_factory=LoggingConfig, description="日志配置")
    
    class Config:
        # 从.env文件读取环境变量
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"  # 支持嵌套配置，如 DATABASE__HOST
        case_sensitive = False
        
        # 环境变量前缀
        env_prefix = ""
        
        # 忽略未定义的额外字段，避免旧环境变量导致验证错误
        extra = "ignore"
    
    @validator('environment')
    def validate_environment(cls, v):
        """验证运行环境"""
        allowed_envs = ['development', 'testing', 'staging', 'production']
        if v.lower() not in allowed_envs:
            raise ValueError(f"Environment must be one of {allowed_envs}")
        return v.lower()
    
    def is_development(self) -> bool:
        """是否为开发环境"""
        return self.environment == 'development'
    
    def is_production(self) -> bool:
        """是否为生产环境"""
        return self.environment == 'production'


# 全局配置实例
_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """获取全局配置实例"""
    global _config
    
    if _config is None:
        # 加载配置，自动从.env文件读取
        _config = AppConfig()
        
        # 如果存在自定义数据库URL环境变量，解析并覆盖配置
        database_url = os.getenv('DATABASE_URL')
        if database_url:
            _config.database = _parse_database_url(database_url)
    
    return _config


def _parse_database_url(url: str) -> DatabaseConfig:
    """解析数据库URL为配置对象"""
    try:
        from urllib.parse import urlparse
        
        parsed = urlparse(url)
        
        # 解析驱动
        scheme_parts = parsed.scheme.split('+')
        if len(scheme_parts) == 2:
            driver = scheme_parts[1]
        else:
            driver = 'asyncpg'  # 默认驱动
        
        return DatabaseConfig(
            host=parsed.hostname or 'localhost',
            port=parsed.port or 5432,
            name=parsed.path.lstrip('/') if parsed.path else 'ragdb',
            user=parsed.username or getpass.getuser(),
            password=parsed.password,
            driver=driver
        )
    except Exception as e:
        # 如果解析失败，返回默认配置
        import logging
        logging.warning(f"Failed to parse DATABASE_URL: {e}, using default config")
        return DatabaseConfig()


def reload_config() -> AppConfig:
    """重新加载配置"""
    global _config
    _config = None
    return get_config()
