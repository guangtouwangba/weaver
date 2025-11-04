"""Message management endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from domain_models import (
    MessageCreate,
    MessageResponse,
    MessageListResponse,
)
from rag_core.services.message_service import MessageService
from rag_core.storage.database import get_db

router = APIRouter(prefix="/messages", tags=["messages"])


@router.post("/", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def create_message(
    message_data: MessageCreate,
    db: Session = Depends(get_db),
) -> MessageResponse:
    """Create a new message."""
    message = MessageService.create_message(
        db,
        conversation_id=message_data.conversation_id,
        role=message_data.role,
        content=message_data.content,
        sources=message_data.sources,
    )
    return MessageResponse.model_validate(message)


@router.get("/{message_id}", response_model=MessageResponse)
def get_message(
    message_id: str,
    db: Session = Depends(get_db),
) -> MessageResponse:
    """Get a message by ID."""
    message = MessageService.get_message(db, message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    return MessageResponse.model_validate(message)


@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_message(
    message_id: str,
    db: Session = Depends(get_db),
):
    """Delete a message."""
    success = MessageService.delete_message(db, message_id)
    if not success:
        raise HTTPException(status_code=404, detail="Message not found")


@router.get("/conversations/{conversation_id}/messages", response_model=MessageListResponse)
def list_conversation_messages(
    conversation_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> MessageListResponse:
    """List messages for a conversation."""
    messages, total = MessageService.list_messages(db, conversation_id, skip, limit)
    return MessageListResponse(
        total=total,
        messages=[MessageResponse.model_validate(m) for m in messages]
    )

