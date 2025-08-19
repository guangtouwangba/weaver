from abc import ABC
from datetime import datetime
from typing import Dict, Any
from uuid import uuid4

from domain.shared.event_types import EventType


class DomainEvent(ABC):
    """领域事件基类"""

    def __init__(self, event_type: EventType, **kwargs):
        self.event_id = str(uuid4())
        self.occurred_at = datetime.utcnow()
        self._event_type = event_type

        # 将所有kwargs作为事件数据
        for key, value in kwargs.items():
            setattr(self, key, value)

    @property
    def event_type(self) -> str:
        """获取事件类型 - 使用枚举值"""
        return self._event_type.value

    @property
    def event_type_enum(self) -> EventType:
        """获取事件类型枚举"""
        return self._event_type

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式，支持复杂对象的序列化"""
        def serialize_value(value):
            """递归序列化值"""
            if value is None:
                return None
            elif isinstance(value, (str, int, float, bool)):
                return value
            elif isinstance(value, datetime):
                return value.isoformat()
            elif hasattr(value, 'to_dict'):
                return value.to_dict()
            elif hasattr(value, '__dict__'):
                return {k: serialize_value(v) for k, v in value.__dict__.items() 
                       if not k.startswith('_')}
            elif isinstance(value, (list, tuple)):
                return [serialize_value(item) for item in value]
            elif isinstance(value, dict):
                return {k: serialize_value(v) for k, v in value.items()}
            else:
                return str(value)  # Fallback to string representation
        
        result = {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "occurred_at": self.occurred_at.isoformat(),
        }
        
        # Add all other attributes with proper serialization
        for k, v in self.__dict__.items():
            if not k.startswith('_') and k not in ['event_id', 'occurred_at']:
                result[k] = serialize_value(v)
        
        return result
