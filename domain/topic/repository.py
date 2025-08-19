"""
Domain Topic Repository Interface

定义主题领域的数据访问接口，遵循依赖倒置原则。
基础设施层将提供具体实现。
"""

from abc import ABC, abstractmethod
from typing import Optional, List
from .topic import TopicEntity


class ITopicRepository(ABC):
    """主题实体仓储接口"""
    
    @abstractmethod
    async def save(self, topic_entity: TopicEntity) -> TopicEntity:
        """保存主题实体"""
        pass
    
    @abstractmethod
    async def get_by_id(self, topic_id: int) -> Optional[TopicEntity]:
        """根据ID获取主题实体"""
        pass
    
    @abstractmethod
    async def get_by_user(self, user_id: int) -> List[TopicEntity]:
        """根据用户ID获取主题列表"""
        pass
    
    @abstractmethod
    async def get_by_name(self, name: str, user_id: Optional[int] = None) -> Optional[TopicEntity]:
        """根据名称获取主题"""
        pass
    
    @abstractmethod
    async def search(self, query: str, user_id: Optional[int] = None) -> List[TopicEntity]:
        """搜索主题"""
        pass
    
    @abstractmethod
    async def update(self, topic_entity: TopicEntity) -> TopicEntity:
        """更新主题实体"""
        pass
    
    @abstractmethod
    async def delete(self, topic_id: int) -> bool:
        """删除主题实体"""
        pass
    
    @abstractmethod
    async def exists(self, topic_id: int) -> bool:
        """检查主题是否存在"""
        pass


class ITagRepository(ABC):
    """标签仓储接口"""
    
    @abstractmethod
    async def get_by_topic(self, topic_id: int) -> List[str]:
        """获取主题的所有标签"""
        pass
    
    @abstractmethod
    async def add_to_topic(self, topic_id: int, tags: List[str]) -> None:
        """为主题添加标签"""
        pass
    
    @abstractmethod
    async def remove_from_topic(self, topic_id: int, tags: List[str]) -> None:
        """从主题移除标签"""
        pass
    
    @abstractmethod
    async def get_popular_tags(self, limit: int = 10) -> List[str]:
        """获取热门标签"""
        pass