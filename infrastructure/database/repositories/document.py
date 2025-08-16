"""
Document-related repository implementations.
"""

from typing import List, Optional, Dict, Any, Union
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from .base import BaseRepository
from ..models.document import Document, DocumentChunk, QueryHistory, UserSession, VectorIndex


class DocumentRepository(BaseRepository[Document]):
    """Repository for Document entities."""
    
    def __init__(self, session: Union[Session, AsyncSession]):
        super().__init__(session, Document)


class QueryHistoryRepository(BaseRepository[QueryHistory]):
    """Repository for QueryHistory entities."""
    
    def __init__(self, session: Union[Session, AsyncSession]):
        super().__init__(session, QueryHistory)