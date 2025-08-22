"""
主题Service层

处理主题相关的Business logic。
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from ..repository import DocumentRepository, FileRepository, TopicRepository
from ..schemas import (
    AddResourceRequest,
    FileResponse,
    TopicCreate,
    TopicList,
    TopicResponse,
    TopicUpdate,
    file_to_response,
    topic_to_response,
    topics_to_responses,
)
from .base_service import BaseService

logger = logging.getLogger(__name__)


class TopicService(BaseService):
    """主题Business service"""

    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.topic_repo = TopicRepository(session)
        self.file_repo = FileRepository(session)

    async def create_topic(self, topic_data: TopicCreate) -> TopicResponse:
        """创建主题"""
        try:
            # 验证业务规则
            await self._validate_topic_creation(topic_data)

            # 创建主题
            topic = await self.topic_repo.create_topic(
                name=topic_data.name,
                description=topic_data.description,
                category=topic_data.category,
                user_id=topic_data.user_id,
                conversation_id=topic_data.conversation_id,
                parent_topic_id=topic_data.parent_topic_id,
                settings=topic_data.settings or {},
            )

            self.logger.info(f"Created topic: {topic.name} (ID: {topic.id})")
            return topic_to_response(topic)

        except Exception as e:
            self._handle_error(e, "create_topic")

    async def get_topic(self, topic_id: int) -> Optional[TopicResponse]:
        """获取主题详情"""
        try:
            topic = await self.topic_repo.get_topic_by_id(topic_id)
            if not topic:
                return None

            # 获取统计信息
            files = await self.file_repo.get_files_by_topic(topic_id, page=1, page_size=1000)
            file_count = len(files)

            return topic_to_response(topic, file_count=file_count)

        except Exception as e:
            self._handle_error(e, f"get_topic_{topic_id}")

    async def update_topic(self, topic_id: int, topic_data: TopicUpdate) -> Optional[TopicResponse]:
        """更新主题"""
        try:
            # 检查主题是否存在
            existing_topic = await self.topic_repo.get_topic_by_id(topic_id)
            if not existing_topic:
                return None

            # 验证更新数据
            await self._validate_topic_update(topic_id, topic_data)

            # 准备更新字典
            update_dict = topic_data.model_dump(exclude_none=True)

            # 更新主题
            updated_topic = await self.topic_repo.update_topic(topic_id, **update_dict)

            self.logger.info(f"Updated topic: {topic_id}")
            return topic_to_response(updated_topic) if updated_topic else None

        except Exception as e:
            self._handle_error(e, f"update_topic_{topic_id}")

    async def delete_topic(self, topic_id: int) -> bool:
        """删除主题"""
        try:
            # 检查是否可以删除
            await self._validate_topic_deletion(topic_id)

            # 软删除相关文件
            files = await self.file_repo.get_files_by_topic(topic_id, page=1, page_size=1000)
            for file in files:
                await self.file_repo.soft_delete_file(file.id)

            # 删除主题
            success = await self.topic_repo.delete_topic(topic_id)

            if success:
                self.logger.info(f"Deleted topic: {topic_id}")

            return success

        except Exception as e:
            self._handle_error(e, f"delete_topic_{topic_id}")

    async def list_topics(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        user_id: Optional[int] = None,
        category: Optional[str] = None,
    ) -> TopicList:
        """获取主题列表"""
        try:
            # 构建过滤条件
            filters = {}
            if status:
                filters["status"] = status
            if user_id:
                filters["user_id"] = user_id

            # 获取主题列表
            topics = await self.topic_repo.list(page=page, page_size=page_size, filters=filters)

            # 获取总数（这里简化，实际应该有专门的count方法）
            all_topics = await self.topic_repo.list(page=1, page_size=1000, filters=filters)
            total = len(all_topics)
            total_pages = (total + page_size - 1) // page_size

            # 转换为响应Schema
            topic_responses = topics_to_responses(topics)

            return TopicList(
                topics=topic_responses,
                total=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages,
            )

        except Exception as e:
            self._handle_error(e, "list_topics")

    async def search_topics(self, query: str, limit: int = 10) -> List[TopicResponse]:
        """搜索主题"""
        try:
            topics = await self.topic_repo.search_topics(query, limit)
            return topics_to_responses(topics)

        except Exception as e:
            self._handle_error(e, f"search_topics_{query}")

    async def get_user_topics(self, user_id: int) -> List[TopicResponse]:
        """获取用户的主题列表"""
        try:
            topics = await self.topic_repo.get_topics_by_user(user_id)
            return topics_to_responses(topics)

        except Exception as e:
            self._handle_error(e, f"get_user_topics_{user_id}")

    # 私有验证方法
    async def _validate_topic_creation(self, topic_data: TopicCreate) -> None:
        """验证主题创建"""
        # 检查名称是否重复（如果需要的话）
        if topic_data.user_id:
            existing_topics = await self.topic_repo.get_topics_by_user(topic_data.user_id)
            if any(topic.name == topic_data.name for topic in existing_topics):
                raise ValueError(f"用户已存在名称为 '{topic_data.name}' 的主题")

    async def _validate_topic_update(self, topic_id: int, topic_data: TopicUpdate) -> None:
        """验证主题更新"""
        # 如果更新名称，检查是否重复
        if topic_data.name:
            topic = await self.topic_repo.get_topic_by_id(topic_id)
            if topic and topic.user_id:
                user_topics = await self.topic_repo.get_topics_by_user(topic.user_id)
                if any(t.name == topic_data.name and t.id != topic_id for t in user_topics):
                    raise ValueError(f"用户已存在名称为 '{topic_data.name}' 的主题")

    async def _validate_topic_deletion(self, topic_id: int) -> None:
        """验证主题删除"""
        # 检查主题是否存在
        topic = await self.topic_repo.get_topic_by_id(topic_id)
        if not topic:
            raise ValueError(f"主题 {topic_id} 不存在")

        # 可以添加其他业务规则，比如检查是否有子主题等

    async def add_resource_to_topic(
        self, topic_id: int, resource_data: AddResourceRequest
    ) -> FileResponse:
        """向主题添加资源（文件）"""
        try:
            # 验证主题是否存在
            topic = await self.topic_repo.get_topic_by_id(topic_id)
            if not topic:
                raise ValueError(f"主题 {topic_id} 不存在")

            # 验证文件是否存在
            file_record = await self.file_repo.get_by_id(resource_data.file_id)
            if not file_record:
                raise ValueError(f"文件 {resource_data.file_id} 不存在")

            # 检查文件是否已经关联到其他主题
            if file_record.topic_id and file_record.topic_id != topic_id:
                self.logger.warning(
                    f"文件 {resource_data.file_id} 已关联到主题 {file_record.topic_id}，将更新为新主题 {topic_id}"
                )

            # 准备更新数据
            update_data = {"topic_id": topic_id}

            # 如果提供了标题，更新文件名
            if resource_data.title:
                update_data["filename"] = resource_data.title

            # 更新文件的主题关联
            updated_file = await self.file_repo.update(resource_data.file_id, update_data)

            if not updated_file:
                raise RuntimeError(f"更新文件 {resource_data.file_id} 失败")

            self.logger.info(f"成功将文件 {resource_data.file_id} 添加到主题 {topic_id}")
            return file_to_response(updated_file)

        except ValueError:
            raise
        except Exception as e:
            self.logger.error(f"添加资源到主题失败: {e}")
            raise RuntimeError(f"添加资源到主题失败: {str(e)}")

    async def remove_resource_from_topic(self, topic_id: int, file_id: str) -> bool:
        """从主题中移除资源"""
        try:
            # 验证主题是否存在
            topic = await self.topic_repo.get_topic_by_id(topic_id)
            if not topic:
                raise ValueError(f"主题 {topic_id} 不存在")

            # 验证文件是否存在且属于该主题
            file_record = await self.file_repo.get_by_id(file_id)
            if not file_record:
                raise ValueError(f"文件 {file_id} 不存在")

            if file_record.topic_id != topic_id:
                raise ValueError(f"文件 {file_id} 不属于主题 {topic_id}")

            # 移除主题关联（设置为None）
            updated_file = await self.file_repo.update(file_id, {"topic_id": None})

            if not updated_file:
                raise RuntimeError(f"移除文件 {file_id} 的主题关联失败")

            self.logger.info(f"成功从主题 {topic_id} 移除文件 {file_id}")
            return True

        except ValueError:
            raise
        except Exception as e:
            self.logger.error(f"从主题移除资源失败: {e}")
            raise RuntimeError(f"从主题移除资源失败: {str(e)}")

    async def get_topic_resources(
        self, topic_id: int, page: int = 1, page_size: int = 20
    ) -> Dict[str, Any]:
        """获取主题的所有资源"""
        try:
            # 验证主题是否存在
            topic = await self.topic_repo.get_topic_by_id(topic_id)
            if not topic:
                raise ValueError(f"主题 {topic_id} 不存在")

            # 获取主题下的所有文件
            files = await self.file_repo.get_files_by_topic(
                topic_id=topic_id, page=page, page_size=page_size
            )

            # 转换为响应格式
            file_responses = [file_to_response(file) for file in files.get("files", [])]

            return {
                "resources": file_responses,
                "total": files.get("total", 0),
                "page": page,
                "page_size": page_size,
                "total_pages": (files.get("total", 0) + page_size - 1) // page_size,
            }

        except ValueError:
            raise
        except Exception as e:
            self.logger.error(f"获取主题资源失败: {e}")
            raise RuntimeError(f"获取主题资源失败: {str(e)}")
