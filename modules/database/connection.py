"""
数据库连接管理

提供简单的数据库连接和会话管理。
"""

import os
import logging
from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

logger = logging.getLogger(__name__)

# 数据库基础模型
Base = declarative_base()

class DatabaseConnection:
    """数据库连接管理器"""
    
    def __init__(self, database_url: Optional[str] = None):
        """
        初始化数据库连接
        
        Args:
            database_url: 数据库连接URL，如果不提供则从环境变量读取
        """
        self.database_url = database_url or self._get_database_url()
        self._engine = None
        self._session_factory = None
        
    def _get_database_url(self) -> str:
        """从环境变量获取数据库URL"""
        default_url = "postgresql+asyncpg://user:password@localhost:5432/ragdb"
        
        # 尝试多个环境变量
        for env_var in ['DATABASE_URL', 'DB_URL', 'POSTGRES_URL']:
            url = os.getenv(env_var)
            if url:
                # 确保使用异步驱动
                if url.startswith('postgresql://'):
                    url = url.replace('postgresql://', 'postgresql+asyncpg://', 1)
                return url
        
        logger.warning(f"未找到数据库配置，使用默认URL: {default_url}")
        return default_url
    
    async def initialize(self) -> None:
        """初始化数据库连接"""
        try:
            self._engine = create_async_engine(
                self.database_url,
                echo=False,  # 设为True可以看到SQL日志
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=3600
            )
            
            self._session_factory = async_sessionmaker(
                self._engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            logger.info("数据库连接初始化成功")
            
        except Exception as e:
            logger.error(f"数据库连接初始化失败: {e}")
            raise
    
    async def close(self) -> None:
        """关闭数据库连接"""
        if self._engine:
            await self._engine.dispose()
            logger.info("数据库连接已关闭")
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """获取数据库会话"""
        if not self._session_factory:
            raise RuntimeError("数据库未初始化，请先调用 initialize()")
        
        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"数据库操作失败: {e}")
                raise
            finally:
                await session.close()
    
    async def health_check(self) -> bool:
        """数据库健康检查"""
        try:
            if not self._engine:
                return False
                
            async with self.get_session() as session:
                result = await session.execute("SELECT 1")
                return result.scalar() == 1
                
        except Exception as e:
            logger.error(f"数据库健康检查失败: {e}")
            return False

# 全局数据库连接实例
_db_connection: Optional[DatabaseConnection] = None

async def get_database_connection() -> DatabaseConnection:
    """获取全局数据库连接实例"""
    global _db_connection
    
    if _db_connection is None:
        _db_connection = DatabaseConnection()
        await _db_connection.initialize()
    
    return _db_connection

@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话的便捷函数"""
    db = await get_database_connection()
    async with db.get_session() as session:
        yield session

async def close_database():
    """关闭全局数据库连接"""
    global _db_connection
    if _db_connection:
        await _db_connection.close()
        _db_connection = None
