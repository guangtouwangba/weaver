"""
StreamEventProcessor - Streaming Event Processor.

Responsible for handling streaming events returned by the RAG pipeline
and converting them into StreamEvent consumable by the frontend.
"""

from typing import Any
from uuid import UUID

from research_agent.shared.utils.rag_trace import RAGTrace

from .models import StreamResult
from .stream_message import SourceRef, StreamEvent, StreamingRefInjector


class StreamEventProcessor:
    """
    Handles streaming events from the RAG pipeline.

    Usage:
        processor = StreamEventProcessor(
            ref_injector=StreamingRefInjector(video_id),
            trace=trace,
            initial_entities=ctx.active_entities,
            initial_focus=ctx.current_focus,
        )

        async for event in stream_rag_response(...):
            result = processor.process(event)
            if result:
                yield result

        # Get final result
        final_result = processor.get_result()
    """

    def __init__(
        self,
        ref_injector: StreamingRefInjector,
        trace: RAGTrace,
        initial_entities: dict[str, dict[str, Any]],
        initial_focus: dict[str, Any] | None,
    ):
        """
        Initialize processor.

        Args:
            ref_injector: Video timestamp reference injector
            trace: RAG trace object for recording metrics
            initial_entities: Initial active entity state
            initial_focus: Initial focus entity
        """
        self._ref_injector = ref_injector
        self._trace = trace

        # Response state
        self._full_response = ""
        self._token_count = 0
        self._response_sources: list[dict[str, Any]] = []
        self._retrieved_contexts: list[str] = []

        # Entity state (may be updated during processing)
        self._active_entities = dict(initial_entities)
        self._current_focus = initial_focus

    def process(self, event: dict[str, Any]) -> StreamEvent | None:
        """
        Process a single RAG event.

        Args:
            event: Event emitted by RAG pipeline

        Returns:
            StreamEvent: Event to be sent to frontend, or None if no event needed
        """
        event_type = event.get("type")

        if event_type == "sources":
            return self._handle_sources_event(event)
        elif event_type == "context_update":
            self._handle_context_update_event(event)
            return None  # No frontend event generated
        elif event_type == "status":
            return self._handle_status_event(event)
        elif event_type == "token":
            return self._handle_token_event(event)
        elif event_type == "done":
            return self._handle_done_event()

        return None

    def get_result(self) -> StreamResult:
        """
        Get results after processing is complete.

        Should be called after all events are processed.
        """
        return StreamResult(
            full_response=self._full_response,
            sources=self._response_sources,
            retrieved_contexts=self._retrieved_contexts,
            token_count=self._token_count,
            active_entities=self._active_entities,
            current_focus=self._current_focus,
        )

    # ========== Private Event Handlers ==========

    def _handle_sources_event(self, event: dict[str, Any]) -> StreamEvent:
        """Handle sources event - retrieved document sources."""
        documents = event.get("documents", [])

        # Calculate max similarity
        top_similarity = max(
            [doc.metadata.get("similarity", 0.0) for doc in documents],
            default=0.0,
        )

        # Update trace metrics
        self._trace.metrics["docs_count"] = len(documents)
        self._trace.metrics["top_similarity"] = round(top_similarity, 3)

        # Convert to SourceRef
        sources = [
            SourceRef(
                document_id=UUID(doc.metadata["document_id"]),
                page_number=doc.metadata["page_number"],
                snippet=(
                    doc.page_content[:200] + "..."
                    if len(doc.page_content) > 200
                    else doc.page_content
                ),
                similarity=doc.metadata.get("similarity", 0.0),
            )
            for doc in documents
        ]

        # Store original context for evaluation
        self._retrieved_contexts = [doc.page_content for doc in documents]

        # Store format for saving to DB
        self._response_sources = [
            {
                "document_id": str(s.document_id),
                "page_number": s.page_number,
                "snippet": s.snippet,
                "similarity": s.similarity,
            }
            for s in sources
        ]

        # Record citations count
        citations_data = event.get("citations", [])
        self._trace.metrics["citations_count"] = len(citations_data)

        return StreamEvent(type="sources", sources=sources)

    def _handle_context_update_event(self, event: dict[str, Any]) -> None:
        """Handle context_update event - update entity state."""
        if "active_entities" in event:
            self._active_entities.update(event["active_entities"])
        if "current_focus" in event:
            self._current_focus = event["current_focus"]

    def _handle_status_event(self, event: dict[str, Any]) -> StreamEvent:
        """Handle status event - thinking status update."""
        return StreamEvent(
            type="status",
            step=event.get("step"),
            message=event.get("message"),
        )

    def _handle_token_event(self, event: dict[str, Any]) -> StreamEvent | None:
        """Handle token event - streaming token."""
        content = event.get("content", "")
        injected = self._ref_injector.process_token(content)

        self._full_response += injected
        self._token_count += 1

        if injected:
            return StreamEvent(type="token", content=injected)
        return None

    def _handle_done_event(self) -> StreamEvent:
        """Handle done event - stream finished."""
        # Flush injector buffer
        remaining = self._ref_injector.flush()
        if remaining:
            self._full_response += remaining
            # We need to send remaining tokens first, but we can only return one event
            # So append to full_response, done event returned separately

        # Record final metrics
        self._trace.metrics["token_count"] = self._token_count
        self._trace.metrics["answer_length"] = len(self._full_response)

        return StreamEvent(type="done")

    def get_remaining_content(self) -> str | None:
        """
        Get remaining content from injector.

        Called before done event to send final tokens.
        """
        remaining = self._ref_injector.flush()
        if remaining:
            self._full_response += remaining
            return remaining
        return None
