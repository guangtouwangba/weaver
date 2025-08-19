from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict
from uuid import uuid4


class DomainEvent(ABC):
    """
    Base class for domain events.
    """

    def __init__(self, event_type: str):
        self.event_type = event_type
        self.event_id = str(uuid4())
        self.occurred_on = datetime.utcnow()
        # Versioning for the event, can be used for event sourcing or version control
        self.version = 1

    def __repr__(self):
        return f"{self.__class__.__name__}(event_type={self.event_type})"

    def __str__(self):
        return f"{self.__class__.__name__} of type {self.event_type}"

    @property
    @abstractmethod
    def event_type(self) -> str:
        """事件类型标识"""
        pass

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {
            'event_id': self.event_id,
            'event_type': self.event_type,
            'occurred_on': self.occurred_on.isoformat(),
            'version': self.version
        }
        # 添加具体事件数据
        result.update(self._get_event_data())
        return result


    @abstractmethod
    def _get_event_data(self) -> Dict[str, Any]:
        """获取事件特定数据"""
        pass
