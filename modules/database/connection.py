"""
数据库连接管理

提供简单的数据库连接和会话管理。
"""

import logging
from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

# 导入配置模块
from config import get_config

logger = logging.getLogger(__name__)

# 数据库基础模型
Base = declarative_base()

class DatabaseConnection:
    """数据库连接管理器"""
    
    def __init__(self, database_url: Optional[str] = None):
        """
        初始化数据库连接
        
        Args:
            database_url: 数据库连接URL，如果不提供则从配置读取
        """
        if database_url:
            self.database_url = database_url
        else:
            # 从配置模块获取数据库配置
            config = get_config()
            self.database_url = config.database.url
            self.database_config = config.database
        
        self._engine = None
        self._session_factory = None
    
    async def initialize(self) -> None:
        """初始化数据库连接"""
        try:
            # 如果使用配置模块，应用配置参数
            if hasattr(self, 'database_config'):
                config = self.database_config
                self._engine = create_async_engine(
                    self.database_url,
                    echo=config.echo,
                    pool_size=config.pool_size,
                    max_overflow=config.max_overflow,
                    pool_timeout=config.pool_timeout,
                    pool_recycle=config.pool_recycle
                )
            else:
                # 使用默认配置
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
            
            from sqlalchemy import text
            async with self.get_session() as session:
                result = await session.execute(text("SELECT 1"))
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

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI依赖注入专用：获取数据库会话"""
    db = await get_database_connection()
    async with db.get_session() as session:
        yield session

async def close_database():
    """关闭全局数据库连接"""
    global _db_connection
    if _db_connection:
        await _db_connection.close()
        _db_connection = None
