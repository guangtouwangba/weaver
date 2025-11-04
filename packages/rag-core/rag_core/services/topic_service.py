"""Topic service layer for business logic."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from domain_models.topic import Topic, TopicStatus
from domain_models.topic_schemas import (
    TopicCreate,
    TopicProgressUpdate,
    TopicStatistics,
    TopicUpdate,
)


class TopicService:
    """Service class for Topic business logic."""

    @staticmethod
    def create_topic(db: Session, topic_data: TopicCreate) -> Topic:
        """
        Create a new topic.

        Args:
            db: Database session
            topic_data: Topic creation data

        Returns:
            Created Topic instance
        """
        topic = Topic(
            name=topic_data.name,
            goal_type=topic_data.goal_type.value,
            description=topic_data.description,
        )
        db.add(topic)
        db.commit()
        db.refresh(topic)
        return topic

    @staticmethod
    def get_topic(db: Session, topic_id: str | UUID) -> Optional[Topic]:
        """
        Get a topic by ID.

        Args:
            db: Database session
            topic_id: Topic UUID

        Returns:
            Topic instance or None if not found
        """
        if isinstance(topic_id, str):
            topic_id = UUID(topic_id)
        return db.query(Topic).filter(Topic.id == topic_id).first()

    @staticmethod
    def list_topics(
        db: Session, status: Optional[TopicStatus] = None, skip: int = 0, limit: int = 100
    ) -> List[Topic]:
        """
        List topics with optional filtering.

        Args:
            db: Database session
            status: Filter by status (optional)
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of Topic instances
        """
        query = db.query(Topic)

        if status:
            query = query.filter(Topic.status == status.value)

        return query.order_by(Topic.updated_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def update_topic(db: Session, topic_id: str | UUID, topic_data: TopicUpdate) -> Optional[Topic]:
        """
        Update a topic.

        Args:
            db: Database session
            topic_id: Topic UUID
            topic_data: Topic update data

        Returns:
            Updated Topic instance or None if not found
        """
        if isinstance(topic_id, str):
            topic_id = UUID(topic_id)

        topic = db.query(Topic).filter(Topic.id == topic_id).first()
        if not topic:
            return None

        # Update only provided fields
        update_data = topic_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if key == "goal_type" and value is not None:
                setattr(topic, key, value.value)
            elif key == "status" and value is not None:
                setattr(topic, key, value.value)
            else:
                setattr(topic, key, value)

        db.commit()
        db.refresh(topic)
        return topic

    @staticmethod
    def delete_topic(db: Session, topic_id: str | UUID) -> bool:
        """
        Delete a topic.

        Args:
            db: Database session
            topic_id: Topic UUID

        Returns:
            True if deleted, False if not found
        """
        if isinstance(topic_id, str):
            topic_id = UUID(topic_id)

        topic = db.query(Topic).filter(Topic.id == topic_id).first()
        if not topic:
            return False

        db.delete(topic)
        db.commit()
        return True

    @staticmethod
    def update_progress(db: Session, topic_id: str | UUID, progress_data: TopicProgressUpdate) -> Optional[Topic]:
        """
        Update topic progress and recalculate completion percentage.

        Args:
            db: Database session
            topic_id: Topic UUID
            progress_data: Progress update data

        Returns:
            Updated Topic instance or None if not found
        """
        if isinstance(topic_id, str):
            topic_id = UUID(topic_id)

        topic = db.query(Topic).filter(Topic.id == topic_id).first()
        if not topic:
            return None

        # Update statistics
        topic.total_contents = progress_data.total_contents
        topic.understood_contents = progress_data.understood_contents
        topic.practiced_contents = progress_data.practiced_contents

        # Recalculate progress
        topic.completion_progress = topic.calculate_progress()

        # Auto-complete if progress reaches 100%
        if topic.completion_progress >= 100.0 and topic.status == TopicStatus.LEARNING.value:
            topic.status = TopicStatus.COMPLETED.value

        db.commit()
        db.refresh(topic)
        return topic

    @staticmethod
    def get_statistics(db: Session) -> TopicStatistics:
        """
        Get topic statistics across all topics.

        Args:
            db: Database session

        Returns:
            TopicStatistics with counts by status
        """
        total_topics = db.query(func.count(Topic.id)).scalar() or 0
        learning = db.query(func.count(Topic.id)).filter(Topic.status == TopicStatus.LEARNING.value).scalar() or 0
        completed = (
            db.query(func.count(Topic.id)).filter(Topic.status == TopicStatus.COMPLETED.value).scalar() or 0
        )
        paused = db.query(func.count(Topic.id)).filter(Topic.status == TopicStatus.PAUSED.value).scalar() or 0
        archived = db.query(func.count(Topic.id)).filter(Topic.status == TopicStatus.ARCHIVED.value).scalar() or 0

        return TopicStatistics(
            total=total_topics, learning=learning, completed=completed, paused=paused, archived=archived
        )

    @staticmethod
    def search_topics(db: Session, query: str, limit: int = 10) -> List[Topic]:
        """
        Search topics by name or description.

        Args:
            db: Database session
            query: Search query string
            limit: Maximum number of results

        Returns:
            List of matching Topic instances
        """
        search_pattern = f"%{query}%"
        return (
            db.query(Topic)
            .filter((Topic.name.ilike(search_pattern)) | (Topic.description.ilike(search_pattern)))
            .order_by(Topic.updated_at.desc())
            .limit(limit)
            .all()
        )

