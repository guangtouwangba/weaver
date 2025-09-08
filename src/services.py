"""
All business logic and services in one file.

Contains repositories, use cases, and domain services.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import asyncio
import logging
import os
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
    
    async def semantic_search(self, query_embedding: List[float], limit: int = 10) -> List[Document]:
        """Semantic search using embeddings (simplified implementation)"""
        # In a real implementation, this would use proper vector similarity
        # For now, we'll use a simple text-based fallback
        results = []
        for doc in self._docs.values():
            if doc.content:
                # Simple heuristic: longer content gets higher priority
                score = len(doc.content) / 1000  # Normalize by content length
                results.append((doc, score))
        
        # Sort by score and return top results
        results.sort(key=lambda x: x[1], reverse=True)
        return [doc for doc, score in results[:limit]]


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


# Enhanced AI Service with OpenAI integration
class EnhancedAIService(AIService):
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.use_openai = bool(self.api_key)
        
        if self.use_openai:
            try:
                import openai
                self.client = openai.AsyncOpenAI(api_key=self.api_key)
                logging.info("✓ OpenAI client initialized")
            except ImportError:
                logging.warning("OpenAI not installed, using mock responses")
                self.use_openai = False
        else:
            logging.info("No OpenAI API key, using mock responses")
    
    async def generate_embedding(self, text: str) -> List[float]:
        if self.use_openai:
            try:
                response = await self.client.embeddings.create(
                    model="text-embedding-ada-002",
                    input=text
                )
                return response.data[0].embedding
            except Exception as e:
                logging.error(f"OpenAI embedding error: {e}")
        
        # Fallback to mock embedding
        import hashlib
        hash_obj = hashlib.md5(text.encode())
        seed = int(hash_obj.hexdigest(), 16) % 1000000
        import random
        random.seed(seed)
        return [random.random() * 2 - 1 for _ in range(1536)]
    
    async def generate_response(self, message: str, context: str = "") -> str:
        if self.use_openai:
            try:
                messages = [
                    {"role": "system", "content": "You are a helpful AI assistant for a RAG knowledge management system."}
                ]
                
                if context:
                    messages.append({"role": "system", "content": f"Context information:\n{context}"})
                
                messages.append({"role": "user", "content": message})
                
                response = await self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=messages,
                    max_tokens=1000,
                    temperature=0.7
                )
                
                return response.choices[0].message.content
            except Exception as e:
                logging.error(f"OpenAI chat error: {e}")
        
        # Fallback to intelligent mock response
        if "python" in message.lower():
            return "Python is a versatile programming language known for its simplicity and readability. It's widely used in data science, web development, and AI applications."
        elif "machine learning" in message.lower() or "ml" in message.lower():
            return "Machine Learning is a subset of artificial intelligence that enables systems to learn and improve from data without being explicitly programmed."
        elif "what" in message.lower() or "?" in message:
            return f"Based on the available knowledge, here's what I can tell you about your question: {message[:100]}... This is a comprehensive topic that involves multiple aspects."
        else:
            return f"I understand you're asking about: {message[:50]}{'...' if len(message) > 50 else ''}. Let me provide you with relevant information based on the knowledge base."
    
    def extract_text(self, file_path: str) -> str:
        """Extract text from various file types"""
        try:
            if file_path.endswith('.txt'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            elif file_path.endswith('.md'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                # For demo purposes, return sample content
                return f"Sample content extracted from {file_path}. In a real implementation, this would use libraries like PyMuPDF for PDFs, python-docx for Word documents, etc."
        except Exception as e:
            logging.error(f"Text extraction error: {e}")
            return f"Error extracting text from {file_path}: {str(e)}"
    
    def chunk_content(self, content: str, size: int = 1000) -> List[DocumentChunk]:
        """Intelligent content chunking"""
        if not content:
            return []
        
        chunks = []
        
        # Split by paragraphs first
        paragraphs = content.split('\n\n')
        current_chunk = ""
        chunk_index = 0
        
        for paragraph in paragraphs:
            # If adding this paragraph would exceed size, create a chunk
            if len(current_chunk) + len(paragraph) > size and current_chunk:
                chunk = DocumentChunk(
                    content=current_chunk.strip(),
                    chunk_index=chunk_index
                )
                chunks.append(chunk)
                chunk_index += 1
                current_chunk = paragraph
            else:
                current_chunk += "\n\n" + paragraph if current_chunk else paragraph
        
        # Add the last chunk if it has content
        if current_chunk.strip():
            chunk = DocumentChunk(
                content=current_chunk.strip(),
                chunk_index=chunk_index
            )
            chunks.append(chunk)
        
        return chunks


# Mock AI Service (fallback)
class MockAIService(AIService):
    async def generate_embedding(self, text: str) -> List[float]:
        # Deterministic mock embedding based on text content
        import hashlib
        hash_obj = hashlib.md5(text.encode())
        seed = int(hash_obj.hexdigest(), 16) % 1000000
        import random
        random.seed(seed)
        return [random.random() * 2 - 1 for _ in range(1536)]
    
    async def generate_response(self, message: str, context: str = "") -> str:
        return f"Mock AI response to: {message[:50]}{'...' if len(message) > 50 else ''}"
    
    def extract_text(self, file_path: str) -> str:
        return f"Mock extracted text from {file_path}"
    
    def chunk_content(self, content: str, size: int = 1000) -> List[DocumentChunk]:
        # Simple word-based chunking
        words = content.split()
        chunks = []
        for i in range(0, len(words), size//10):
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
        """Search documents with optional semantic search."""
        if request.use_semantic and hasattr(self.doc_repo, 'semantic_search'):
            # Use semantic search if available
            query_embedding = await self.ai_service.generate_embedding(request.query)
            results = await self.doc_repo.semantic_search(query_embedding, request.limit)
        else:
            # Fallback to text search
            results = await self.doc_repo.search(request.query, request.limit)
        
        # Publish search event
        event = Event(
            type="document_searched",
            data={
                "query": request.query, 
                "results_count": len(results),
                "search_type": "semantic" if request.use_semantic else "text"
            }
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
def create_rag_service(use_enhanced_ai: bool = True) -> RAGService:
    """Create RAG service with default implementations."""
    doc_repo = MemoryDocumentRepository()
    topic_repo = MemoryTopicRepository()
    chat_repo = MemoryChatRepository()
    ai_service = EnhancedAIService() if use_enhanced_ai else MockAIService()
    event_bus = EventBus()
    
    # Setup some default event handlers
    async def log_event(event: Event):
        logging.info(f"Event: {event.type} - {event.data}")
    
    event_bus.subscribe("document_created", log_event)
    event_bus.subscribe("document_processed", log_event)
    event_bus.subscribe("message_sent", log_event)
    
    return RAGService(doc_repo, topic_repo, chat_repo, ai_service, event_bus)