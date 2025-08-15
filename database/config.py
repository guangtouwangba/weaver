"""
数据库配置
"""

import os
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv

# 加载环境变量
load_dotenv('.env.middleware')


class DatabaseConfig:
    """数据库配置类"""
    
    def __init__(self):
        self.host = os.getenv('POSTGRES_HOST', 'localhost')
        self.port = int(os.getenv('POSTGRES_PORT', 5432))
        self.database = os.getenv('POSTGRES_DB', 'rag_db')
        self.username = os.getenv('POSTGRES_USER', 'rag_user')
        self.password = os.getenv('POSTGRES_PASSWORD', 'rag_password')
        self.echo = os.getenv('SQL_ECHO', 'false').lower() == 'true'
    
    @property
    def sync_url(self) -> str:
        """同步数据库连接URL"""
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    @property
    def async_url(self) -> str:
        """异步数据库连接URL"""
        return f"postgresql+asyncpg://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    @property
    def alembic_url(self) -> str:
        """Alembic数据库连接URL"""
        return self.sync_url


# 全局配置实例
db_config = DatabaseConfig()

# 同步引擎和会话
sync_engine = create_engine(
    db_config.sync_url,
    echo=db_config.echo,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600
)

SyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=sync_engine
)

# 异步引擎和会话
async_engine = create_async_engine(
    db_config.async_url,
    echo=db_config.echo,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600
)

AsyncSessionLocal = sessionmaker(
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    bind=async_engine
)


def get_sync_session() -> Session:
    """获取同步数据库会话"""
    return SyncSessionLocal()


async def get_async_session() -> AsyncSession:
    """获取异步数据库会话"""
    return AsyncSessionLocal()


# 依赖注入函数（用于FastAPI等框架）
def get_db_session():
    """获取数据库会话的依赖注入函数"""
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db_session():
    """获取异步数据库会话的依赖注入函数"""
    async with AsyncSessionLocal() as session:
        yield session