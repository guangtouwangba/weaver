#!/usr/bin/env python3
"""
Standalone event system demonstration.

Shows the event-driven architecture without importing problematic modules.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import uuid4

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


# Simple Event System Implementation
class BaseEvent:
    """Base event class."""
    
    def __init__(self, aggregate_id: str, **kwargs):
        self.event_id = str(uuid4())
        self.occurred_at = datetime.utcnow()
        self.aggregate_id = aggregate_id
        self.event_type = self.__class__.__name__
        self.data = kwargs
    
    def __repr__(self):
        return f"{self.event_type}(id={self.event_id[:8]}..., aggregate={self.aggregate_id})"


class DocumentCreatedEvent(BaseEvent):
    """Event fired when a document is created."""
    
    def __init__(self, document_id: str, title: str, content_type: str, file_id: Optional[str] = None):
        super().__init__(document_id, title=title, content_type=content_type, file_id=file_id)
        self.title = title
        self.content_type = content_type
        self.file_id = file_id


class DocumentProcessedEvent(BaseEvent):
    """Event fired when a document has been processed."""
    
    def __init__(self, document_id: str, chunks_created: int, processing_time: float):
        super().__init__(document_id, chunks_created=chunks_created, processing_time=processing_time)
        self.chunks_created = chunks_created
        self.processing_time = processing_time


class DocumentSearchedEvent(BaseEvent):
    """Event fired when documents are searched."""
    
    def __init__(self, query: str, results_count: int, search_type: str = "semantic"):
        super().__init__(f"search_{query[:20]}", query=query, results_count=results_count, search_type=search_type)
        self.query = query
        self.results_count = results_count
        self.search_type = search_type


class ChatSessionStartedEvent(BaseEvent):
    """Event fired when a chat session is started."""
    
    def __init__(self, session_id: str, topic_id: Optional[int] = None, user_id: Optional[int] = None):
        super().__init__(session_id, topic_id=topic_id, user_id=user_id)
        self.topic_id = topic_id
        self.user_id = user_id


class MessageSentEvent(BaseEvent):
    """Event fired when a message is sent."""
    
    def __init__(self, message_id: str, session_id: str, message_role: str, message_length: int):
        super().__init__(message_id, session_id=session_id, message_role=message_role, message_length=message_length)
        self.session_id = session_id
        self.message_role = message_role
        self.message_length = message_length


class EventDispatcher:
    """Simple event dispatcher."""
    
    def __init__(self):
        self.handlers = {}
        self.analytics = {}
        self.total_events = 0
    
    def register_handler(self, event_type: type, handler):
        """Register an event handler."""
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler)
        logging.info(f"Registered handler for {event_type.__name__}")
    
    async def dispatch(self, event):
        """Dispatch an event to handlers."""
        event_type = type(event)
        event_name = event_type.__name__
        
        # Update analytics
        if event_name not in self.analytics:
            self.analytics[event_name] = 0
        self.analytics[event_name] += 1
        self.total_events += 1
        
        # Call handlers
        handlers = self.handlers.get(event_type, [])
        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                logging.error(f"Error in handler for {event_name}: {e}")
        
        logging.debug(f"Dispatched {event_name} to {len(handlers)} handler(s)")


# Event Handlers
async def document_created_handler(event: DocumentCreatedEvent):
    """Handle document created events."""
    logging.info(f"📄 Document created: '{event.title}' (ID: {event.aggregate_id})")
    # In real system: send notifications, update statistics, trigger indexing


async def document_processed_handler(event: DocumentProcessedEvent):
    """Handle document processed events."""
    logging.info(f"⚙️ Document processed: {event.chunks_created} chunks in {event.processing_time:.2f}s")
    # In real system: update search index, notify users, record metrics


async def search_handler(event: DocumentSearchedEvent):
    """Handle search events."""
    logging.info(f"🔍 Search: '{event.query}' -> {event.results_count} results ({event.search_type})")
    # In real system: improve search suggestions, track popular queries


async def chat_session_handler(event: ChatSessionStartedEvent):
    """Handle chat session events."""
    logging.info(f"💬 Chat session started: {event.aggregate_id} (topic: {event.topic_id})")
    # In real system: initialize context, send welcome message


async def message_handler(event: MessageSentEvent):
    """Handle message events."""
    logging.info(f"📝 Message sent: {event.message_role} ({event.message_length} chars) in session {event.session_id}")
    # In real system: update conversation metrics, track engagement


async def analytics_handler(event):
    """Universal analytics handler."""
    logging.debug(f"📊 Analytics: {event.event_type} at {event.occurred_at.strftime('%H:%M:%S')}")
    # In real system: send to analytics service, update dashboards


async def audit_handler(event):
    """Audit trail handler."""
    logging.debug(f"📋 Audit: {event} by system")
    # In real system: store in audit database for compliance


async def main():
    """Demonstrate the event system."""
    print("🎯 Event-Driven Architecture Demonstration")
    print("=" * 60)
    
    # Create event dispatcher
    dispatcher = EventDispatcher()
    
    # Register handlers - multiple handlers per event type
    dispatcher.register_handler(DocumentCreatedEvent, document_created_handler)
    dispatcher.register_handler(DocumentCreatedEvent, analytics_handler)
    dispatcher.register_handler(DocumentCreatedEvent, audit_handler)
    
    dispatcher.register_handler(DocumentProcessedEvent, document_processed_handler)
    dispatcher.register_handler(DocumentProcessedEvent, analytics_handler)
    
    dispatcher.register_handler(DocumentSearchedEvent, search_handler)
    dispatcher.register_handler(DocumentSearchedEvent, analytics_handler)
    
    dispatcher.register_handler(ChatSessionStartedEvent, chat_session_handler)
    dispatcher.register_handler(ChatSessionStartedEvent, analytics_handler)
    
    dispatcher.register_handler(MessageSentEvent, message_handler)
    dispatcher.register_handler(MessageSentEvent, analytics_handler)
    
    print(f"✓ Event dispatcher initialized with {len(dispatcher.handlers)} event types")
    print()
    
    # Test 1: Document lifecycle
    print("📄 Test 1: Document Lifecycle Events")
    print("-" * 40)
    
    # Document created
    doc_created = DocumentCreatedEvent(
        document_id="doc-ml-guide-123",
        title="Machine Learning Fundamentals Guide",
        content_type="markdown",
        file_id="file-upload-456"
    )
    await dispatcher.dispatch(doc_created)
    
    # Simulate some processing time
    await asyncio.sleep(0.1)
    
    # Document processed
    doc_processed = DocumentProcessedEvent(
        document_id="doc-ml-guide-123",
        chunks_created=25,
        processing_time=3.47
    )
    await dispatcher.dispatch(doc_processed)
    
    print()
    
    # Test 2: User interactions
    print("🔍 Test 2: User Interaction Events")
    print("-" * 40)
    
    # Search event
    search_event = DocumentSearchedEvent(
        query="machine learning algorithms comparison",
        results_count=12,
        search_type="hybrid"
    )
    await dispatcher.dispatch(search_event)
    
    # Chat session started
    chat_started = ChatSessionStartedEvent(
        session_id="chat-session-789",
        topic_id=42,
        user_id=1001
    )
    await dispatcher.dispatch(chat_started)
    
    # Message sent
    message_sent = MessageSentEvent(
        message_id="msg-abc-101",
        session_id="chat-session-789",
        message_role="user",
        message_length=127
    )
    await dispatcher.dispatch(message_sent)
    
    print()
    
    # Test 3: Batch processing simulation
    print("🚀 Test 3: Batch Processing Simulation")
    print("-" * 40)
    
    # Simulate multiple documents being created
    document_titles = [
        "Python Best Practices",
        "Clean Architecture Principles", 
        "Database Design Patterns",
        "API Security Guidelines",
        "Microservices Architecture"
    ]
    
    for i, title in enumerate(document_titles):
        event = DocumentCreatedEvent(
            document_id=f"batch-doc-{i+1}",
            title=title,
            content_type="text"
        )
        await dispatcher.dispatch(event)
        await asyncio.sleep(0.05)  # Small delay to simulate real processing
    
    print()
    
    # Test 4: Analytics and reporting
    print("📊 Test 4: Event Analytics")
    print("-" * 40)
    
    print(f"Total events processed: {dispatcher.total_events}")
    print("Event breakdown:")
    for event_type, count in sorted(dispatcher.analytics.items()):
        print(f"  • {event_type}: {count} events")
    
    print()
    
    # Test 5: Event details
    print("🔍 Test 5: Event Structure Details")
    print("-" * 40)
    
    sample_event = DocumentCreatedEvent(
        document_id="sample-doc",
        title="Sample Document",
        content_type="text"
    )
    
    print(f"Event ID: {sample_event.event_id}")
    print(f"Event Type: {sample_event.event_type}")
    print(f"Occurred At: {sample_event.occurred_at}")
    print(f"Aggregate ID: {sample_event.aggregate_id}")
    print(f"Title: {sample_event.title}")
    print(f"Content Type: {sample_event.content_type}")
    print(f"Additional Data: {sample_event.data}")
    
    print()
    print("🎉 Event System Demonstration Complete!")
    print("=" * 60)
    
    print("\n🏗️ Architecture Benefits Demonstrated:")
    print("✓ Decoupling - Components communicate through events, not direct calls")
    print("✓ Extensibility - New event handlers can be added without changing existing code")
    print("✓ Audit Trail - All important system actions are captured as events")
    print("✓ Analytics - Easy to collect metrics and understand system usage")
    print("✓ Error Isolation - Handler failures don't affect other handlers or event sources")
    print("✓ Async Processing - Events are handled asynchronously for better performance")
    print("✓ Multiple Handlers - Single event can trigger multiple actions")
    
    print("\n🚀 Real-World Applications:")
    print("📧 Email notifications when documents are processed")
    print("📊 Real-time dashboard updates")
    print("🔍 Search improvement based on query patterns")
    print("🤖 ML model training triggers")
    print("📝 Compliance audit logging")
    print("💾 Data backup triggers")
    print("⚠️ Alert systems for errors or anomalies")
    
    print(f"\n📈 Performance: Processed {dispatcher.total_events} events across {len(dispatcher.handlers)} handler types")


if __name__ == "__main__":
    asyncio.run(main())