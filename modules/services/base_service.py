"""
基础Service层

提供Service层的基础抽象和通用功能。
"""

import logging
from abc import ABC

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class BaseService(ABC):
    """基础Service抽象类"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.logger = logging.getLogger(self.__class__.__name__)

    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if exc_type is not None:
            # 如果有异常，回滚事务
            await self.session.rollback()
            self.logger.error(f"Service operation failed: {exc_type.__name__}: {exc_val}")
        else:
            # 如果没有异常，提交事务
            await self.session.commit()

    async def commit(self):
        """手动提交事务"""
        await self.session.commit()

    async def rollback(self):
        """手动回滚事务"""
        await self.session.rollback()

    def _handle_error(self, error: Exception, operation: str) -> None:
        """统一错误处理"""
        self.logger.error(f"Error in {operation}: {str(error)}")
        raise error
