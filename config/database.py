"""
数据库配置模块

提供数据库连接和相关配置管理功能。
"""

import os
from dataclasses import dataclass
from typing import Optional, Dict, Any
from urllib.parse import quote_plus


@dataclass
class DatabaseConfig:
    """数据库配置"""

    # 连接配置
    host: str = "localhost"
    port: int = 5432
    database: str = "rag_db"
    username: str = "postgres"
    password: str = ""

    # 连接池配置
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600
    pool_pre_ping: bool = True

    # SSL配置
    ssl_mode: str = "prefer"  # disable, allow, prefer, require, verify-ca, verify-full
    ssl_cert: Optional[str] = None
    ssl_key: Optional[str] = None
    ssl_ca: Optional[str] = None

    # 性能配置
    echo: bool = False  # SQL日志
    echo_pool: bool = False  # 连接池日志
    query_timeout: int = 30  # 查询超时

    # 应用配置
    application_name: str = "rag-knowledge-system"
    timezone: str = "UTC"

    def build_url(self, async_driver: bool = True) -> str:
        """构建数据库连接URL"""
        # 选择驱动
        if async_driver:
            driver = "postgresql+asyncpg"
        else:
            driver = "postgresql+psycopg2"

        # URL编码密码以处理特殊字符
        encoded_password = quote_plus(self.password) if self.password else ""

        # 构建基础URL
        if encoded_password:
            url = f"{driver}://{self.username}:{encoded_password}@{self.host}:{self.port}/{self.database}"
        else:
            url = f"{driver}://{self.username}@{self.host}:{self.port}/{self.database}"

        # 添加查询参数
        params = []
        if self.application_name:
            params.append(f"application_name={self.application_name}")
        if self.ssl_mode != "prefer":
            params.append(f"sslmode={self.ssl_mode}")
        if self.ssl_cert:
            params.append(f"sslcert={self.ssl_cert}")
        if self.ssl_key:
            params.append(f"sslkey={self.ssl_key}")
        if self.ssl_ca:
            params.append(f"sslrootcert={self.ssl_ca}")

        if params:
            url += "?" + "&".join(params)

        return url

    def get_engine_kwargs(self) -> Dict[str, Any]:
        """获取SQLAlchemy引擎参数"""
        return {
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
            "pool_timeout": self.pool_timeout,
            "pool_recycle": self.pool_recycle,
            "pool_pre_ping": self.pool_pre_ping,
            "echo": self.echo,
            "echo_pool": self.echo_pool,
            "query_cache_size": 1200,
            "connect_args": {
                "server_settings": {
                    "timezone": self.timezone,
                    "application_name": self.application_name,
                }
            },
        }

    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """从环境变量创建配置"""
        return cls(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
            database=os.getenv("DB_NAME", "rag_db"),
            username=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", ""),
            pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "20")),
            pool_timeout=int(os.getenv("DB_POOL_TIMEOUT", "30")),
            pool_recycle=int(os.getenv("DB_POOL_RECYCLE", "3600")),
            ssl_mode=os.getenv("DB_SSL_MODE", "prefer"),
            ssl_cert=os.getenv("DB_SSL_CERT"),
            ssl_key=os.getenv("DB_SSL_KEY"),
            ssl_ca=os.getenv("DB_SSL_CA"),
            echo=os.getenv("DB_ECHO", "false").lower() == "true",
            query_timeout=int(os.getenv("DB_QUERY_TIMEOUT", "30")),
            application_name=os.getenv("DB_APP_NAME", "rag-knowledge-system"),
            timezone=os.getenv("DB_TIMEZONE", "UTC"),
        )


# 默认数据库配置实例
default_db_config = DatabaseConfig.from_env()
