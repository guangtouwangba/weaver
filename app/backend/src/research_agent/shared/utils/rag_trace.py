"""RAG Pipeline Tracing for end-to-end observability.

This module provides structured logging for the entire RAG pipeline,
enabling easy debugging, performance analysis, and optimization.

Usage:
    from research_agent.shared.utils.rag_trace import RAGTrace, rag_log

    # In the main entry point (stream_message.py):
    async with RAGTrace(query, project_id, session_id) as trace:
        # ... pipeline execution
        trace.log("RETRIEVE", docs_count=5, latency_ms=120)

    # In other modules (rag_graph.py):
    rag_log("GENERATE", tokens=150, latency_ms=800)

Grafana LogQL queries:
    # Trace a single request
    {service="backend"} |= "RAG:abc12345"

    # P95 latency
    {service="backend"} |= "COMPLETE" | json | unwrap total_latency_ms | quantile_over_time(0.95, [1h])
"""

import json
import time
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any, Optional
from uuid import uuid4

from research_agent.shared.utils.logger import logger

# Context variable for trace_id propagation across async calls
_current_trace: ContextVar[Optional["RAGTrace"]] = ContextVar("rag_trace", default=None)


# Stage icons for visual distinction in logs
STAGE_ICONS = {
    "ENTRY": "🚀",
    "HISTORY": "📜",
    "CONTEXT": "📎",
    "TRANSFORM": "📝",
    "INTENT": "🎯",
    "RETRIEVE": "🔍",
    "RERANK": "📊",
    "GRADE": "✓",
    "GENERATE": "💬",
    "STREAM": "⚡",
    "COMPLETE": "✅",
    "ERROR": "❌",
}


@dataclass
class StageMetrics:
    """Metrics for a single pipeline stage."""

    stage: str
    start_time: float
    end_time: float | None = None
    metrics: dict[str, Any] = field(default_factory=dict)

    @property
    def latency_ms(self) -> float:
        if self.end_time is None:
            return 0
        return round((self.end_time - self.start_time) * 1000, 2)


class RAGTrace:
    """RAG pipeline tracing for end-to-end observability.

    Provides:
    - Unique trace_id for request correlation
    - Per-stage timing and metrics
    - Structured JSON logging for Grafana/Loki
    - Context propagation for async code

    Example:
        async with RAGTrace(query, project_id) as trace:
            trace.log("RETRIEVE", docs_count=5)
            # ... more stages
        # Automatically logs COMPLETE with summary
    """

    def __init__(
        self,
        query: str,
        project_id: str,
        session_id: str | None = None,
        extra_context: dict[str, Any] | None = None,
    ):
        """Initialize a new trace.

        Args:
            query: User query (truncated to 100 chars in logs)
            project_id: Project UUID
            session_id: Optional chat session UUID
            extra_context: Additional context to include in all logs
        """
        self.trace_id = str(uuid4())[:8]  # Short ID for readability
        self.query = query[:100] if query else ""
        self.query_full = query  # Keep full query for metrics
        self.project_id = str(project_id)[:8] if project_id else "unknown"
        self.session_id = str(session_id)[:8] if session_id else "default"
        self.extra_context = extra_context or {}

        self.start_time = time.time()
        self.stages: list[StageMetrics] = []
        self.current_stage: StageMetrics | None = None
        self.metrics: dict[str, Any] = {}
        self._error: Exception | None = None

    async def __aenter__(self):
        """Async context manager entry."""
        _current_trace.set(self)
        self.log(
            "ENTRY",
            query=self.query,
            query_length=len(self.query_full),
            project=self.project_id,
            session=self.session_id,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if exc_val:
            self._error = exc_val
            self.log(
                "ERROR",
                error_type=exc_type.__name__ if exc_type else "Unknown",
                error_message=str(exc_val)[:200] if exc_val else "",
            )
        self.complete()
        _current_trace.set(None)
        return False  # Don't suppress exceptions

    def __enter__(self):
        """Sync context manager entry."""
        _current_trace.set(self)
        self.log(
            "ENTRY",
            query=self.query,
            query_length=len(self.query_full),
            project=self.project_id,
            session=self.session_id,
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Sync context manager exit."""
        if exc_val:
            self._error = exc_val
            self.log(
                "ERROR",
                error_type=exc_type.__name__ if exc_type else "Unknown",
                error_message=str(exc_val)[:200] if exc_val else "",
            )
        self.complete()
        _current_trace.set(None)
        return False

    def start_stage(self, stage: str) -> None:
        """Mark the start of a pipeline stage.

        Args:
            stage: Stage name (TRANSFORM, INTENT, RETRIEVE, etc.)
        """
        if self.current_stage:
            # End previous stage
            self.current_stage.end_time = time.time()
            self.stages.append(self.current_stage)

        self.current_stage = StageMetrics(stage=stage, start_time=time.time())

    def end_stage(self, **metrics) -> None:
        """Mark the end of current stage with metrics.

        Args:
            **metrics: Stage-specific metrics to log
        """
        if self.current_stage:
            self.current_stage.end_time = time.time()
            self.current_stage.metrics = metrics
            self.stages.append(self.current_stage)
            self.current_stage = None

    def log(self, stage: str, **metrics) -> None:
        """Log a pipeline stage with metrics.

        This is the primary logging method. It creates a structured log entry
        with trace correlation and stage-specific metrics.

        Args:
            stage: Stage name (ENTRY, HISTORY, CONTEXT, TRANSFORM, INTENT,
                   RETRIEVE, RERANK, GRADE, GENERATE, COMPLETE, ERROR)
            **metrics: Stage-specific metrics (e.g., docs_count, latency_ms)
        """
        elapsed = round((time.time() - self.start_time) * 1000, 2)

        # Build structured log data
        log_data = {
            "trace_id": self.trace_id,
            "stage": stage,
            "elapsed_ms": elapsed,
            **self.extra_context,
            **metrics,
        }

        # Store for summary
        self.metrics.update(metrics)

        # Get stage icon
        icon = STAGE_ICONS.get(stage, "•")

        # Log with structured JSON suffix for Grafana parsing
        # Format: [RAG:trace_id] 🔍 STAGE | key=value | JSON: {...}
        metrics_str = " | ".join(f"{k}={v}" for k, v in metrics.items() if k != "query")
        if metrics_str:
            metrics_str = f" | {metrics_str}"

        logger.info(
            f"[RAG:{self.trace_id}] {icon} {stage}{metrics_str} | "
            f"JSON: {json.dumps(log_data, ensure_ascii=False)}"
        )

    def log_with_timing(self, stage: str, start_time: float, **metrics) -> None:
        """Log a stage with automatic latency calculation.

        Args:
            stage: Stage name
            start_time: Stage start time from time.time()
            **metrics: Additional metrics
        """
        latency_ms = round((time.time() - start_time) * 1000, 2)
        self.log(stage, latency_ms=latency_ms, **metrics)

    def complete(self) -> None:
        """Log request completion with summary metrics.

        Called automatically when exiting the context manager.
        """
        total_ms = round((time.time() - self.start_time) * 1000, 2)

        # Build summary
        summary = {
            "trace_id": self.trace_id,
            "total_latency_ms": total_ms,
            "query": self.query,
            "query_length": len(self.query_full),
            "stages_completed": [s.stage for s in self.stages],
            "stage_count": len(self.stages),
            # Key metrics from collected data
            "docs_retrieved": self.metrics.get("docs_count", 0),
            "docs_used": self.metrics.get("docs_used", self.metrics.get("filtered_count", 0)),
            "intent": self.metrics.get("intent_type", "unknown"),
            "confidence": self.metrics.get("confidence", 0),
            "answer_tokens": self.metrics.get("tokens", self.metrics.get("token_count", 0)),
            "has_error": self._error is not None,
        }

        # Calculate stage breakdown
        stage_latencies = {}
        for s in self.stages:
            if s.latency_ms > 0:
                stage_latencies[s.stage] = s.latency_ms
        if stage_latencies:
            summary["stage_latencies"] = stage_latencies

        icon = "❌" if self._error else "✅"
        status = "ERROR" if self._error else "COMPLETE"

        logger.info(
            f"[RAG:{self.trace_id}] {icon} {status} | total={total_ms}ms | "
            f"docs={summary['docs_retrieved']} | intent={summary['intent']} | "
            f"JSON: {json.dumps(summary, ensure_ascii=False)}"
        )


def get_trace() -> RAGTrace | None:
    """Get current trace from context.

    Returns:
        Current RAGTrace instance or None if not in a trace context.
    """
    return _current_trace.get()


def rag_log(stage: str, **metrics) -> None:
    """Log to current trace if exists, otherwise log directly.

    This is a convenience function for logging from anywhere in the pipeline.
    If called within a RAGTrace context, it will use the trace's trace_id.
    Otherwise, it logs with a placeholder trace_id.

    Args:
        stage: Stage name
        **metrics: Stage-specific metrics

    Example:
        # In rag_graph.py
        rag_log("RETRIEVE", docs_count=5, latency_ms=120, search_type="hybrid")
    """
    trace = get_trace()
    if trace:
        trace.log(stage, **metrics)
    else:
        # No active trace - log with placeholder
        icon = STAGE_ICONS.get(stage, "•")
        log_data = {"trace_id": "no-trace", "stage": stage, **metrics}
        metrics_str = " | ".join(f"{k}={v}" for k, v in metrics.items())
        logger.info(
            f"[RAG:no-trace] {icon} {stage} | {metrics_str} | "
            f"JSON: {json.dumps(log_data, ensure_ascii=False)}"
        )


def rag_log_with_timing(stage: str, start_time: float, **metrics) -> None:
    """Log to current trace with automatic latency calculation.

    Args:
        stage: Stage name
        start_time: Stage start time from time.time()
        **metrics: Additional metrics
    """
    latency_ms = round((time.time() - start_time) * 1000, 2)
    rag_log(stage, latency_ms=latency_ms, **metrics)
