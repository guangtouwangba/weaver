"""Conversation management endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from domain_models import (
    ConversationCreate,
    ConversationUpdate,
    ConversationResponse,
    ConversationListResponse,
)
from rag_core.services.conversation_service import ConversationService
from rag_core.storage.database import get_db

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("/", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
def create_conversation(
    conversation_data: ConversationCreate,
    db: Session = Depends(get_db),
) -> ConversationResponse:
    """Create a new conversation."""
    conversation = ConversationService.create_conversation(db, conversation_data)
    return ConversationResponse.model_validate(conversation)


@router.get("/{conversation_id}", response_model=ConversationResponse)
def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
) -> ConversationResponse:
    """Get a conversation by ID."""
    conversation = ConversationService.get_conversation(db, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return ConversationResponse.model_validate(conversation)


@router.put("/{conversation_id}", response_model=ConversationResponse)
def update_conversation(
    conversation_id: str,
    update_data: ConversationUpdate,
    db: Session = Depends(get_db),
) -> ConversationResponse:
    """Update a conversation."""
    conversation = ConversationService.update_conversation(db, conversation_id, update_data)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return ConversationResponse.model_validate(conversation)


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
):
    """Delete a conversation."""
    success = ConversationService.delete_conversation(db, conversation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")


@router.get("/topics/{topic_id}/conversations", response_model=ConversationListResponse)
def list_topic_conversations(
    topic_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> ConversationListResponse:
    """List conversations for a topic."""
    conversations, total = ConversationService.list_conversations(db, topic_id, skip, limit)
    return ConversationListResponse(
        total=total,
        conversations=[ConversationResponse.model_validate(c) for c in conversations]
    )

