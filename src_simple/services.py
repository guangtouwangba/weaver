"""
All business logic and services in one file.

Contains repositories, use cases, and domain services.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import asyncio
import logging
from .models import *


# Repository Interfaces (minimal)
class DocumentRepository(ABC):
    @abstractmethod
    async def save(self, document: Document) -> None: pass
    
    @abstractmethod
    async def get_by_id(self, doc_id: str) -> Optional[Document]: pass
    
    @abstractmethod
    async def search(self, query: str, limit: int = 10) -> List[Document]: pass


class TopicRepository(ABC):
    @abstractmethod
    async def save(self, topic: Topic) -> None: pass
    
    @abstractmethod
    async def get_by_id(self, topic_id: int) -> Optional[Topic]: pass


class ChatRepository(ABC):
    @abstractmethod
    async def save_session(self, session: ChatSession) -> None: pass
    
    @abstractmethod
    async def get_session(self, session_id: str) -> Optional[ChatSession]: pass


# Memory Implementations
class MemoryDocumentRepository(DocumentRepository):
    def __init__(self):
        self._docs: Dict[str, Document] = {}
        self._chunks: Dict[str, List[DocumentChunk]] = {}
    
    async def save(self, document: Document) -> None:
        self._docs[document.id] = document
    
    async def get_by_id(self, doc_id: str) -> Optional[Document]:
        return self._docs.get(doc_id)
    
    async def search(self, query: str, limit: int = 10) -> List[Document]:
        results = []
        query_lower = query.lower()
        for doc in self._docs.values():
            if (query_lower in (doc.title or "").lower() or 
                query_lower in (doc.content or "").lower()):
                results.append(doc)
                if len(results) >= limit:
                    break
        return results
    
    async def save_chunks(self, chunks: List[DocumentChunk]) -> None:
        for chunk in chunks:
            if chunk.document_id not in self._chunks:
                self._chunks[chunk.document_id] = []
            self._chunks[chunk.document_id].append(chunk)
    
    async def get_chunks(self, doc_id: str) -> List[DocumentChunk]:
        return self._chunks.get(doc_id, [])


class MemoryTopicRepository(TopicRepository):
    def __init__(self):
        self._topics: Dict[int, Topic] = {}
        self._next_id = 1
    
    async def save(self, topic: Topic) -> None:
        if topic.id == 0:
            topic.id = self._next_id
            self._next_id += 1
        self._topics[topic.id] = topic
    
    async def get_by_id(self, topic_id: int) -> Optional[Topic]:
        return self._topics.get(topic_id)


class MemoryChatRepository(ChatRepository):
    def __init__(self):
        self._sessions: Dict[str, ChatSession] = {}
    
    async def save_session(self, session: ChatSession) -> None:
        self._sessions[session.id] = session
    
    async def get_session(self, session_id: str) -> Optional[ChatSession]:
        return self._sessions.get(session_id)


# AI Service Interface
class AIService(ABC):
    @abstractmethod
    async def generate_embedding(self, text: str) -> List[float]: pass
    
    @abstractmethod
    async def generate_response(self, message: str, context: str = "") -> str: pass
    
    @abstractmethod
    def extract_text(self, file_path: str) -> str: pass
    
    @abstractmethod
    def chunk_content(self, content: str, size: int = 1000) -> List[DocumentChunk]: pass


# Mock AI Service
class MockAIService(AIService):
    async def generate_embedding(self, text: str) -> List[float]:
        # Mock embedding - in real implementation use OpenAI/local model
        return [0.1] * 1536
    
    async def generate_response(self, message: str, context: str = "") -> str:
        # Mock response - in real implementation use OpenAI/local model
        return f"Mock response to: {message[:50]}..."
    
    def extract_text(self, file_path: str) -> str:
        # Mock text extraction
        return f"Extracted text from {file_path}"
    
    def chunk_content(self, content: str, size: int = 1000) -> List[DocumentChunk]:
        # Simple chunking
        chunks = []
        words = content.split()
        for i in range(0, len(words), size//10):  # Rough word-based chunking
            chunk_words = words[i:i + size//10]
            chunk_content = " ".join(chunk_words)
            chunk = DocumentChunk(
                content=chunk_content,
                chunk_index=i//(size//10)
            )
            chunks.append(chunk)
        return chunks


# Event System (simplified)
class EventBus:
    def __init__(self):
        self._handlers: Dict[str, List] = {}
        self._analytics: Dict[str, int] = {}
    
    def subscribe(self, event_type: str, handler):
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
    
    async def publish(self, event: Event):
        # Update analytics
        if event.type not in self._analytics:
            self._analytics[event.type] = 0
        self._analytics[event.type] += 1
        
        # Call handlers
        handlers = self._handlers.get(event.type, [])
        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                logging.error(f"Event handler error: {e}")
    
    def get_analytics(self) -> Dict[str, int]:
        return self._analytics.copy()


# Use Cases (all in one class for simplicity)
class RAGService:
    """Main service containing all use cases."""
    
    def __init__(
        self,
        doc_repo: DocumentRepository,
        topic_repo: TopicRepository,
        chat_repo: ChatRepository,
        ai_service: AIService,
        event_bus: EventBus = None
    ):
        self.doc_repo = doc_repo
        self.topic_repo = topic_repo
        self.chat_repo = chat_repo
        self.ai_service = ai_service
        self.event_bus = event_bus or EventBus()
    
    # Document Use Cases
    async def create_document(self, request: CreateDocumentRequest) -> Document:
        """Create a new document."""
        document = Document(
            title=request.title,
            content=request.content,
            content_type=request.content_type,
            file_id=request.file_id
        )
        
        await self.doc_repo.save(document)
        
        # Publish event
        event = Event.document_created(document.id, document.title)
        await self.event_bus.publish(event)
        
        # Process document asynchronously
        asyncio.create_task(self._process_document(document))
        
        return document
    
    async def get_document(self, doc_id: str) -> Optional[Document]:
        """Get document by ID."""
        return await self.doc_repo.get_by_id(doc_id)
    
    async def search_documents(self, request: SearchRequest) -> List[Document]:
        """Search documents."""
        results = await self.doc_repo.search(request.query, request.limit)
        
        # Publish search event
        event = Event(
            type="document_searched",
            data={"query": request.query, "results_count": len(results)}
        )
        await self.event_bus.publish(event)
        
        return results
    
    async def _process_document(self, document: Document):
        """Process document (chunking, embedding, indexing)."""
        try:
            document.update_status("processing")
            await self.doc_repo.save(document)
            
            # Create chunks
            chunks = self.ai_service.chunk_content(document.content or "")
            for chunk in chunks:
                chunk.document_id = document.id
                chunk.embedding = await self.ai_service.generate_embedding(chunk.content)
            
            # Save chunks (assuming doc_repo handles this)
            if hasattr(self.doc_repo, 'save_chunks'):
                await self.doc_repo.save_chunks(chunks)
            
            document.update_status("completed")
            await self.doc_repo.save(document)
            
            # Publish processed event
            event = Event.document_processed(document.id, len(chunks))
            await self.event_bus.publish(event)
            
        except Exception as e:
            document.update_status("failed")
            await self.doc_repo.save(document)
            logging.error(f"Document processing failed: {e}")
    
    # Topic Use Cases
    async def create_topic(self, name: str, description: str = None) -> Topic:
        """Create a new topic."""
        topic = Topic(name=name, description=description)
        await self.topic_repo.save(topic)
        return topic
    
    async def get_topic(self, topic_id: int) -> Optional[Topic]:
        """Get topic by ID."""
        return await self.topic_repo.get_by_id(topic_id)
    
    # Chat Use Cases
    async def start_chat_session(self, topic_id: int = None) -> ChatSession:
        """Start a new chat session."""
        session = ChatSession(topic_id=topic_id)
        await self.chat_repo.save_session(session)
        return session
    
    async def send_message(self, request: ChatRequest) -> ChatMessage:
        """Send a message and get AI response."""
        session = await self.chat_repo.get_session(request.session_id)
        if not session:
            raise ValueError("Session not found")
        
        # Add user message
        user_message = ChatMessage(
            content=request.message,
            role=MessageRole.USER
        )
        session.add_message(user_message)
        
        # Generate AI response
        context = ""
        if request.use_context:
            # Simple context from recent messages
            recent_messages = session.messages[-5:]  # Last 5 messages
            context = "\n".join([f"{m.role.value}: {m.content}" for m in recent_messages])
        
        ai_response = await self.ai_service.generate_response(request.message, context)
        
        # Add AI message
        assistant_message = ChatMessage(
            content=ai_response,
            role=MessageRole.ASSISTANT
        )
        session.add_message(assistant_message)
        
        await self.chat_repo.save_session(session)
        
        # Publish event
        event = Event.message_sent(session.id, len(request.message))
        await self.event_bus.publish(event)
        
        return assistant_message


# Factory function for easy setup
def create_rag_service(use_mock_ai: bool = True) -> RAGService:
    """Create RAG service with default implementations."""
    doc_repo = MemoryDocumentRepository()
    topic_repo = MemoryTopicRepository()
    chat_repo = MemoryChatRepository()
    ai_service = MockAIService() if use_mock_ai else None  # Replace with real AI service
    event_bus = EventBus()
    
    # Setup some default event handlers
    async def log_event(event: Event):
        logging.info(f"Event: {event.type} - {event.data}")
    
    event_bus.subscribe("document_created", log_event)
    event_bus.subscribe("document_processed", log_event)
    event_bus.subscribe("message_sent", log_event)
    
    return RAGService(doc_repo, topic_repo, chat_repo, ai_service, event_bus)