"""Topic ORM model for knowledge management."""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from rag_core.storage.database import Base


class GoalType(str, Enum):
    """Learning goal type for a topic."""

    THEORY = "theory"  # 理论研究型：构建完整知识体系
    PRACTICE = "practice"  # 实践应用型：提取可执行策略
    QUICK = "quick"  # 快速了解型：获取核心要点


class TopicStatus(str, Enum):
    """Topic learning status."""

    LEARNING = "learning"  # 学习中
    PAUSED = "paused"  # 已暂停
    COMPLETED = "completed"  # 已完成
    ARCHIVED = "archived"  # 已归档


class Topic(Base):
    """
    Topic ORM model representing a learning topic.
    
    A topic is the central organizing unit for knowledge management,
    containing metadata about learning goals, progress, and statistics.
    """

    __tablename__ = "topics"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Basic information
    name = Column(String(200), nullable=False, index=True)
    goal_type = Column(String(20), nullable=False, index=True)
    description = Column(Text, nullable=True)
    status = Column(String(20), default=TopicStatus.LEARNING, index=True)

    # Progress tracking
    completion_progress = Column(Float, default=0.0)  # 0-100

    # Statistics
    total_contents = Column(Integer, default=0)  # 总内容数
    understood_contents = Column(Integer, default=0)  # 已理解内容数
    practiced_contents = Column(Integer, default=0)  # 已实践内容数（仅practice类型有意义）

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    contents = relationship("TopicContent", back_populates="topic", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="topic", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        """String representation of Topic."""
        return f"<Topic(id={self.id}, name='{self.name}', goal_type='{self.goal_type}', status='{self.status}')>"

    def calculate_progress(self) -> float:
        """
        Calculate completion progress based on goal type.
        
        For PRACTICE topics: based on practiced_contents
        For THEORY/QUICK topics: based on understood_contents
        
        Returns:
            Progress percentage (0-100)
        """
        if self.total_contents == 0:
            return 0.0

        if self.goal_type == GoalType.PRACTICE:
            return (self.practiced_contents / self.total_contents) * 100
        else:
            return (self.understood_contents / self.total_contents) * 100

