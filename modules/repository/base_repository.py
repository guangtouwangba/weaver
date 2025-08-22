"""
Base repository实现

提供Repository模式的基础抽象类。
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from .interfaces import IBaseRepository

logger = logging.getLogger(__name__)


class BaseRepository(IBaseRepository):
    """Base repository实现"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, entity_data: Dict[str, Any]) -> Any:
        """通用创建方法（子类应重写）"""
        raise NotImplementedError("Subclasses must implement create method")

    async def get_by_id(self, entity_id: Any) -> Optional[Any]:
        """通用获取方法（子类应重写）"""
        raise NotImplementedError("Subclasses must implement get_by_id method")

    async def update(self, entity_id: Any, updates: Dict[str, Any]) -> Optional[Any]:
        """通用更新方法（子类应重写）"""
        raise NotImplementedError("Subclasses must implement update method")

    async def delete(self, entity_id: Any) -> bool:
        """通用删除方法（子类应重写）"""
        raise NotImplementedError("Subclasses must implement delete method")

    async def list(
        self,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
    ) -> List[Any]:
        """通用列表方法（子类应重写）"""
        raise NotImplementedError("Subclasses must implement list method")
