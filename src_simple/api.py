"""
All API endpoints in one file.

FastAPI application with all routes and schemas.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging

from .services import create_rag_service, RAGService
from .models import *


# API Schemas (Pydantic models)
class DocumentCreateSchema(BaseModel):
    title: str
    content: str
    content_type: str = "text"
    file_id: Optional[str] = None


class DocumentResponseSchema(BaseModel):
    id: str
    title: str
    content: Optional[str]
    content_type: str
    status: str
    created_at: str
    updated_at: str


class SearchSchema(BaseModel):
    query: str
    limit: int = 10
    use_semantic: bool = True


class ChatMessageSchema(BaseModel):
    session_id: str
    message: str
    use_context: bool = True


class ChatResponseSchema(BaseModel):
    content: str
    role: str
    timestamp: str


class TopicCreateSchema(BaseModel):
    name: str
    description: Optional[str] = None


class TopicResponseSchema(BaseModel):
    id: int
    name: str
    description: Optional[str]
    status: str
    total_resources: int
    created_at: str


# Global service instance
rag_service: RAGService = None


def create_app() -> FastAPI:
    """Create FastAPI application."""
    global rag_service
    
    app = FastAPI(
        title="Simple RAG API",
        description="Minimal file architecture for RAG system",
        version="1.0.0"
    )
    
    # Initialize service
    rag_service = create_rag_service()
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "architecture": "simplified"}
    
    # Document endpoints
    @app.post("/documents", response_model=DocumentResponseSchema)
    async def create_document(request: DocumentCreateSchema):
        """Create a new document."""
        try:
            doc_request = CreateDocumentRequest(
                title=request.title,
                content=request.content,
                content_type=request.content_type,
                file_id=request.file_id
            )
            
            document = await rag_service.create_document(doc_request)
            
            return DocumentResponseSchema(
                id=document.id,
                title=document.title,
                content=document.content,
                content_type=document.content_type,
                status=document.status,
                created_at=document.created_at.isoformat(),
                updated_at=document.updated_at.isoformat()
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.get("/documents/{doc_id}", response_model=DocumentResponseSchema)
    async def get_document(doc_id: str):
        """Get document by ID."""
        document = await rag_service.get_document(doc_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return DocumentResponseSchema(
            id=document.id,
            title=document.title,
            content=document.content,
            content_type=document.content_type,
            status=document.status,
            created_at=document.created_at.isoformat(),
            updated_at=document.updated_at.isoformat()
        )
    
    @app.post("/documents/search", response_model=List[DocumentResponseSchema])
    async def search_documents(request: SearchSchema):
        """Search documents."""
        search_request = SearchRequest(
            query=request.query,
            limit=request.limit,
            use_semantic=request.use_semantic
        )
        
        documents = await rag_service.search_documents(search_request)
        
        return [
            DocumentResponseSchema(
                id=doc.id,
                title=doc.title,
                content=doc.content,
                content_type=doc.content_type,
                status=doc.status,
                created_at=doc.created_at.isoformat(),
                updated_at=doc.updated_at.isoformat()
            )
            for doc in documents
        ]
    
    # Topic endpoints
    @app.post("/topics", response_model=TopicResponseSchema)
    async def create_topic(request: TopicCreateSchema):
        """Create a new topic."""
        topic = await rag_service.create_topic(request.name, request.description)
        
        return TopicResponseSchema(
            id=topic.id,
            name=topic.name,
            description=topic.description,
            status=topic.status.value,
            total_resources=topic.total_resources,
            created_at=topic.created_at.isoformat()
        )
    
    @app.get("/topics/{topic_id}", response_model=TopicResponseSchema)
    async def get_topic(topic_id: int):
        """Get topic by ID."""
        topic = await rag_service.get_topic(topic_id)
        if not topic:
            raise HTTPException(status_code=404, detail="Topic not found")
        
        return TopicResponseSchema(
            id=topic.id,
            name=topic.name,
            description=topic.description,
            status=topic.status.value,
            total_resources=topic.total_resources,
            created_at=topic.created_at.isoformat()
        )
    
    # Chat endpoints
    @app.post("/chat/sessions")
    async def start_chat_session(topic_id: Optional[int] = None):
        """Start a new chat session."""
        session = await rag_service.start_chat_session(topic_id)
        return {"session_id": session.id, "topic_id": session.topic_id}
    
    @app.post("/chat/message", response_model=ChatResponseSchema)
    async def send_message(request: ChatMessageSchema):
        """Send a chat message."""
        try:
            chat_request = ChatRequest(
                session_id=request.session_id,
                message=request.message,
                use_context=request.use_context
            )
            
            response = await rag_service.send_message(chat_request)
            
            return ChatResponseSchema(
                content=response.content,
                role=response.role.value,
                timestamp=response.timestamp.isoformat()
            )
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    # Analytics endpoint
    @app.get("/analytics")
    async def get_analytics():
        """Get system analytics."""
        analytics = rag_service.event_bus.get_analytics()
        return {
            "events": analytics,
            "total_events": sum(analytics.values())
        }
    
    return app


# For running with uvicorn
app = create_app()