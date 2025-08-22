"""
主题Repository实现

处理主题相关的数据访问逻辑。
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, asc, delete, desc, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database.models import Topic
from ..schemas.enums import TopicStatus
from .base_repository import BaseRepository
from .interfaces import ITopicRepository

logger = logging.getLogger(__name__)


class TopicRepository(BaseRepository, ITopicRepository):
    """主题Repository实现"""

    async def create_topic(self, name: str, description: str = "", **kwargs) -> Topic:
        """创建主题"""
        topic = Topic(
            name=name,
            description=description,
            status=kwargs.get("status", TopicStatus.ACTIVE),
            category=kwargs.get("category"),
            user_id=kwargs.get("user_id"),
            conversation_id=kwargs.get("conversation_id"),
            parent_topic_id=kwargs.get("parent_topic_id"),
            settings=kwargs.get("settings", {}),
            # 统计信息字段
            concept_relationships=0,
            total_resources=0,
            total_conversations=0,
            core_concepts_discovered=0,
            missing_materials_count=0,
        )

        self.session.add(topic)
        await self.session.flush()
        await self.session.refresh(topic)

        logger.info(f"创建主题: {topic.name} (ID: {topic.id})")
        return topic

    async def get_topic_by_id(self, topic_id: int) -> Optional[Topic]:
        """根据ID获取主题"""
        result = await self.session.execute(
            select(Topic).where(Topic.id == topic_id).options(selectinload(Topic.files))
        )
        return result.scalar_one_or_none()

    async def get_topics(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        user_id: Optional[int] = None,
    ) -> List[Topic]:
        """获取主题列表"""
        query = select(Topic)

        # 添加过滤条件
        conditions = []
        if status:
            conditions.append(Topic.status == status)
        if user_id:
            conditions.append(Topic.user_id == user_id)

        if conditions:
            query = query.where(and_(*conditions))

        # 添加分页
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size).order_by(desc(Topic.created_at))

        result = await self.session.execute(query)
        return result.scalars().all()

    async def update_topic(self, topic_id: int, **updates) -> Optional[Topic]:
        """更新主题"""
        topic = await self.get_topic_by_id(topic_id)
        if not topic:
            return None

        for key, value in updates.items():
            if hasattr(topic, key):
                setattr(topic, key, value)

        topic.updated_at = datetime.utcnow()
        await self.session.flush()
        await self.session.refresh(topic)

        logger.info(f"更新主题: {topic.name} (ID: {topic.id})")
        return topic

    async def delete_topic(self, topic_id: int) -> bool:
        """删除主题"""
        result = await self.session.execute(delete(Topic).where(Topic.id == topic_id))
        success = result.rowcount > 0

        if success:
            logger.info(f"删除主题 ID: {topic_id}")

        return success

    async def get_topics_by_user(self, user_id: int) -> List[Topic]:
        """获取用户的主题列表"""
        result = await self.session.execute(
            select(Topic).where(Topic.user_id == user_id).order_by(desc(Topic.created_at))
        )
        return result.scalars().all()

    async def search_topics(self, query: str, limit: int = 10) -> List[Topic]:
        """搜索主题"""
        search_query = (
            select(Topic)
            .where(or_(Topic.name.ilike(f"%{query}%"), Topic.description.ilike(f"%{query}%")))
            .limit(limit)
        )

        result = await self.session.execute(search_query)
        return result.scalars().all()

    # 实现基类抽象方法
    async def create(self, entity_data: Dict[str, Any]) -> Topic:
        return await self.create_topic(**entity_data)

    async def get_by_id(self, entity_id: int) -> Optional[Topic]:
        return await self.get_topic_by_id(entity_id)

    async def update(self, entity_id: int, updates: Dict[str, Any]) -> Optional[Topic]:
        return await self.update_topic(entity_id, **updates)

    async def delete(self, entity_id: int) -> bool:
        return await self.delete_topic(entity_id)

    async def list(
        self,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
    ) -> List[Topic]:
        status = filters.get("status") if filters else None
        user_id = filters.get("user_id") if filters else None
        return await self.get_topics(page, page_size, status, user_id)
