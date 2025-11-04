"""Topic management endpoints."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from domain_models.topic import TopicStatus
from domain_models.topic_schemas import (
    TopicCreate,
    TopicListResponse,
    TopicProgressUpdate,
    TopicResponse,
    TopicStatistics,
    TopicUpdate,
)
from rag_core.services.topic_service import TopicService
from rag_core.storage.database import get_db

router = APIRouter(prefix="/topics", tags=["topics"])


@router.post("/", response_model=TopicResponse, status_code=201, summary="Create a new topic")
def create_topic(topic: TopicCreate, db: Session = Depends(get_db)) -> TopicResponse:
    """
    Create a new learning topic.

    Args:
        topic: Topic creation data
        db: Database session (dependency injected)

    Returns:
        Created topic with all fields
    """
    created_topic = TopicService.create_topic(db, topic)
    return TopicResponse.model_validate(created_topic)


@router.get("/", response_model=TopicListResponse, summary="List all topics")
def list_topics(
    status: Optional[TopicStatus] = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
) -> TopicListResponse:
    """
    List topics with optional filtering and pagination.

    Args:
        status: Optional status filter
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        db: Database session (dependency injected)

    Returns:
        List of topics with total count
    """
    topics = TopicService.list_topics(db, status=status, skip=skip, limit=limit)
    topic_responses = [TopicResponse.model_validate(topic) for topic in topics]
    return TopicListResponse(total=len(topic_responses), topics=topic_responses)


@router.get("/statistics", response_model=TopicStatistics, summary="Get topic statistics")
def get_statistics(db: Session = Depends(get_db)) -> TopicStatistics:
    """
    Get aggregate statistics across all topics.

    Args:
        db: Database session (dependency injected)

    Returns:
        Statistics with counts by status
    """
    return TopicService.get_statistics(db)


@router.get("/search", response_model=List[TopicResponse], summary="Search topics")
def search_topics(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
    db: Session = Depends(get_db),
) -> List[TopicResponse]:
    """
    Search topics by name or description.

    Args:
        q: Search query string
        limit: Maximum number of results
        db: Database session (dependency injected)

    Returns:
        List of matching topics
    """
    topics = TopicService.search_topics(db, query=q, limit=limit)
    return [TopicResponse.model_validate(topic) for topic in topics]


@router.get("/{topic_id}", response_model=TopicResponse, summary="Get topic by ID")
def get_topic(topic_id: str, db: Session = Depends(get_db)) -> TopicResponse:
    """
    Get a specific topic by ID.

    Args:
        topic_id: Topic UUID
        db: Database session (dependency injected)

    Returns:
        Topic details

    Raises:
        HTTPException: 404 if topic not found
    """
    topic = TopicService.get_topic(db, topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail=f"Topic with id {topic_id} not found")
    return TopicResponse.model_validate(topic)


@router.put("/{topic_id}", response_model=TopicResponse, summary="Update topic")
def update_topic(topic_id: str, topic_data: TopicUpdate, db: Session = Depends(get_db)) -> TopicResponse:
    """
    Update an existing topic.

    Args:
        topic_id: Topic UUID
        topic_data: Fields to update
        db: Database session (dependency injected)

    Returns:
        Updated topic

    Raises:
        HTTPException: 404 if topic not found
    """
    topic = TopicService.update_topic(db, topic_id, topic_data)
    if not topic:
        raise HTTPException(status_code=404, detail=f"Topic with id {topic_id} not found")
    return TopicResponse.model_validate(topic)


@router.delete("/{topic_id}", status_code=204, summary="Delete topic")
def delete_topic(topic_id: str, db: Session = Depends(get_db)) -> None:
    """
    Delete a topic.

    Args:
        topic_id: Topic UUID
        db: Database session (dependency injected)

    Raises:
        HTTPException: 404 if topic not found
    """
    if not TopicService.delete_topic(db, topic_id):
        raise HTTPException(status_code=404, detail=f"Topic with id {topic_id} not found")


@router.put("/{topic_id}/progress", response_model=TopicResponse, summary="Update topic progress")
def update_progress(topic_id: str, progress: TopicProgressUpdate, db: Session = Depends(get_db)) -> TopicResponse:
    """
    Update topic progress statistics and recalculate completion percentage.

    The completion percentage is automatically calculated based on:
    - For PRACTICE topics: practiced_contents / total_contents
    - For THEORY/QUICK topics: understood_contents / total_contents

    Args:
        topic_id: Topic UUID
        progress: Progress update data
        db: Database session (dependency injected)

    Returns:
        Updated topic with recalculated progress

    Raises:
        HTTPException: 404 if topic not found
    """
    topic = TopicService.update_progress(db, topic_id, progress)
    if not topic:
        raise HTTPException(status_code=404, detail=f"Topic with id {topic_id} not found")
    return TopicResponse.model_validate(topic)

