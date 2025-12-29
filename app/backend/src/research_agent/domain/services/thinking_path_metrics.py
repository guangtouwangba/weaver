"""
Thinking Path Metrics Service.

This module defines the metrics and instrumentation for measuring
the success of Thinking Path MVP features.

Key Metrics:
1. TTR (Time to Re-orient): Time from project_open to first meaningful action
2. Checkpoint revisit rate: % of checkpoints that are revisited
3. Anchor jump success rate: % of anchor jumps that successfully locate
4. Citation coverage: % of claims with at least one evidence anchor

Events to Track:
- project_open: User opens a project
- resume_view: User views resume mode
- checkpoint_jump: User jumps to a checkpoint
- anchor_jump: User clicks to jump to an anchor
- anchor_jump_success: Anchor successfully located
- anchor_jump_failure: Anchor could not be located
- claim_create: Claim created
- first_action: First meaningful action after project_open
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from research_agent.shared.utils.logger import logger


class MetricEventType(str, Enum):
    """Types of metric events to track."""

    # Project/Session events
    PROJECT_OPEN = "project_open"
    RESUME_VIEW = "resume_view"
    FIRST_ACTION = "first_action"  # First meaningful action after open

    # Checkpoint events
    CHECKPOINT_CREATE = "checkpoint_create"
    CHECKPOINT_VIEW = "checkpoint_view"
    CHECKPOINT_JUMP = "checkpoint_jump"

    # Anchor events
    ANCHOR_JUMP = "anchor_jump"
    ANCHOR_JUMP_SUCCESS = "anchor_jump_success"
    ANCHOR_JUMP_FAILURE = "anchor_jump_failure"

    # Node events (for coverage)
    CLAIM_CREATE = "claim_create"
    CLAIM_ADD_EVIDENCE = "claim_add_evidence"


@dataclass
class MetricEvent:
    """A metric event to be recorded."""

    id: UUID = field(default_factory=uuid4)
    project_id: Optional[UUID] = None
    event_type: MetricEventType = MetricEventType.PROJECT_OPEN
    event_data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    session_id: Optional[str] = None  # For tracking within a session

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "projectId": str(self.project_id) if self.project_id else None,
            "eventType": self.event_type.value
            if isinstance(self.event_type, MetricEventType)
            else self.event_type,
            "eventData": self.event_data,
            "timestamp": self.timestamp.isoformat(),
            "sessionId": self.session_id,
        }


@dataclass
class TTRMetric:
    """
    Time to Re-orient metric.

    Measures how long it takes a user to get back into the flow
    after opening a project.

    Target: < 60 seconds
    """

    project_id: UUID
    session_id: str
    project_open_time: datetime
    first_action_time: Optional[datetime] = None
    first_action_type: Optional[str] = None
    ttr_seconds: Optional[float] = None

    def calculate_ttr(self) -> Optional[float]:
        """Calculate TTR in seconds."""
        if self.first_action_time:
            delta = self.first_action_time - self.project_open_time
            self.ttr_seconds = delta.total_seconds()
            return self.ttr_seconds
        return None

    def is_within_target(self, target_seconds: float = 60.0) -> bool:
        """Check if TTR is within target."""
        if self.ttr_seconds is not None:
            return self.ttr_seconds <= target_seconds
        return False


@dataclass
class CheckpointRevisitMetric:
    """
    Checkpoint revisit rate metric.

    Measures what percentage of checkpoints are revisited by users.
    Higher rates indicate checkpoints are useful for re-entry.
    """

    project_id: UUID
    total_checkpoints: int = 0
    revisited_checkpoints: int = 0
    revisit_rate: float = 0.0

    def calculate_rate(self) -> float:
        """Calculate revisit rate."""
        if self.total_checkpoints > 0:
            self.revisit_rate = self.revisited_checkpoints / self.total_checkpoints
        return self.revisit_rate


@dataclass
class AnchorJumpMetric:
    """
    Anchor jump success rate metric.

    Measures what percentage of anchor jump attempts successfully
    locate the source position.
    """

    project_id: UUID
    total_jumps: int = 0
    successful_jumps: int = 0
    failed_jumps: int = 0
    success_rate: float = 0.0

    def calculate_rate(self) -> float:
        """Calculate success rate."""
        if self.total_jumps > 0:
            self.success_rate = self.successful_jumps / self.total_jumps
        return self.success_rate


@dataclass
class CitationCoverageMetric:
    """
    Citation coverage metric.

    Measures what percentage of claims have at least one evidence anchor.
    Higher coverage means better-supported claims.
    """

    project_id: UUID
    total_claims: int = 0
    claims_with_evidence: int = 0
    coverage_rate: float = 0.0

    def calculate_rate(self) -> float:
        """Calculate coverage rate."""
        if self.total_claims > 0:
            self.coverage_rate = self.claims_with_evidence / self.total_claims
        return self.coverage_rate


class ThinkingPathMetricsService:
    """
    Service for tracking and calculating Thinking Path metrics.

    This is an in-memory implementation for MVP.
    In production, this would persist to a metrics store.
    """

    def __init__(self):
        """Initialize the metrics service."""
        # In-memory storage for MVP
        self._events: List[MetricEvent] = []
        self._active_sessions: Dict[str, TTRMetric] = {}

    # =========================================================================
    # Event Recording
    # =========================================================================

    def record_event(
        self,
        project_id: UUID,
        event_type: MetricEventType,
        event_data: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ) -> MetricEvent:
        """
        Record a metric event.

        Args:
            project_id: Project ID
            event_type: Type of event
            event_data: Additional event data
            session_id: Session identifier

        Returns:
            Recorded event
        """
        event = MetricEvent(
            project_id=project_id,
            event_type=event_type,
            event_data=event_data or {},
            session_id=session_id,
        )
        self._events.append(event)

        # Log for observability
        logger.info(
            f"[Metrics] {event_type.value} for project {project_id}"
            f"{f' session {session_id}' if session_id else ''}"
        )

        return event

    # =========================================================================
    # TTR (Time to Re-orient) Tracking
    # =========================================================================

    def start_session(
        self,
        project_id: UUID,
        session_id: str,
    ) -> None:
        """
        Start tracking a new session for TTR calculation.

        Call this when a project is opened.
        """
        self._active_sessions[session_id] = TTRMetric(
            project_id=project_id,
            session_id=session_id,
            project_open_time=datetime.utcnow(),
        )

        self.record_event(
            project_id=project_id,
            event_type=MetricEventType.PROJECT_OPEN,
            session_id=session_id,
        )

    def record_first_action(
        self,
        session_id: str,
        action_type: str,
    ) -> Optional[TTRMetric]:
        """
        Record the first meaningful action in a session.

        Call this when user performs first action after opening project.

        Args:
            session_id: Session ID
            action_type: Type of action (e.g., "edit_node", "view_anchor")

        Returns:
            TTR metric with calculated time, or None if session not found
        """
        if session_id not in self._active_sessions:
            return None

        metric = self._active_sessions[session_id]

        # Only record if not already recorded
        if metric.first_action_time is None:
            metric.first_action_time = datetime.utcnow()
            metric.first_action_type = action_type
            metric.calculate_ttr()

            self.record_event(
                project_id=metric.project_id,
                event_type=MetricEventType.FIRST_ACTION,
                event_data={
                    "action_type": action_type,
                    "ttr_seconds": metric.ttr_seconds,
                },
                session_id=session_id,
            )

            logger.info(
                f"[Metrics] TTR for session {session_id}: {metric.ttr_seconds:.1f}s "
                f"(target: 60s, {'OK' if metric.is_within_target() else 'SLOW'})"
            )

        return metric

    def get_ttr_stats(
        self,
        project_id: UUID,
        days: int = 7,
    ) -> Dict[str, Any]:
        """
        Get TTR statistics for a project.

        Args:
            project_id: Project ID
            days: Number of days to look back

        Returns:
            TTR statistics
        """
        cutoff = datetime.utcnow() - timedelta(days=days)

        ttr_values = []
        for event in self._events:
            if (
                event.project_id == project_id
                and event.event_type == MetricEventType.FIRST_ACTION
                and event.timestamp >= cutoff
                and "ttr_seconds" in event.event_data
            ):
                ttr_values.append(event.event_data["ttr_seconds"])

        if not ttr_values:
            return {
                "count": 0,
                "avg_ttr_seconds": None,
                "median_ttr_seconds": None,
                "within_target_rate": None,
            }

        avg_ttr = sum(ttr_values) / len(ttr_values)
        sorted_values = sorted(ttr_values)
        median_ttr = sorted_values[len(sorted_values) // 2]
        within_target = sum(1 for t in ttr_values if t <= 60) / len(ttr_values)

        return {
            "count": len(ttr_values),
            "avg_ttr_seconds": round(avg_ttr, 1),
            "median_ttr_seconds": round(median_ttr, 1),
            "within_target_rate": round(within_target, 2),
        }

    # =========================================================================
    # Checkpoint Revisit Tracking
    # =========================================================================

    def record_checkpoint_view(
        self,
        project_id: UUID,
        checkpoint_id: UUID,
    ) -> None:
        """Record a checkpoint being viewed."""
        self.record_event(
            project_id=project_id,
            event_type=MetricEventType.CHECKPOINT_VIEW,
            event_data={"checkpoint_id": str(checkpoint_id)},
        )

    def record_checkpoint_jump(
        self,
        project_id: UUID,
        checkpoint_id: UUID,
    ) -> None:
        """Record a jump to a checkpoint."""
        self.record_event(
            project_id=project_id,
            event_type=MetricEventType.CHECKPOINT_JUMP,
            event_data={"checkpoint_id": str(checkpoint_id)},
        )

    def get_checkpoint_revisit_stats(
        self,
        project_id: UUID,
        checkpoint_ids: List[str],
    ) -> CheckpointRevisitMetric:
        """
        Calculate checkpoint revisit statistics.

        Args:
            project_id: Project ID
            checkpoint_ids: List of all checkpoint IDs

        Returns:
            Checkpoint revisit metric
        """
        visited_checkpoints = set()

        for event in self._events:
            if event.project_id == project_id and event.event_type in (
                MetricEventType.CHECKPOINT_VIEW,
                MetricEventType.CHECKPOINT_JUMP,
            ):
                cp_id = event.event_data.get("checkpoint_id")
                if cp_id:
                    visited_checkpoints.add(cp_id)

        metric = CheckpointRevisitMetric(
            project_id=project_id,
            total_checkpoints=len(checkpoint_ids),
            revisited_checkpoints=len(visited_checkpoints),
        )
        metric.calculate_rate()

        return metric

    # =========================================================================
    # Anchor Jump Tracking
    # =========================================================================

    def record_anchor_jump(
        self,
        project_id: UUID,
        anchor_id: str,
        success: bool,
    ) -> None:
        """
        Record an anchor jump attempt.

        Args:
            project_id: Project ID
            anchor_id: Anchor ID
            success: Whether the jump was successful
        """
        event_type = (
            MetricEventType.ANCHOR_JUMP_SUCCESS if success else MetricEventType.ANCHOR_JUMP_FAILURE
        )

        self.record_event(
            project_id=project_id,
            event_type=event_type,
            event_data={"anchor_id": anchor_id},
        )

    def get_anchor_jump_stats(
        self,
        project_id: UUID,
        days: int = 7,
    ) -> AnchorJumpMetric:
        """
        Get anchor jump statistics.

        Args:
            project_id: Project ID
            days: Number of days to look back

        Returns:
            Anchor jump metric
        """
        cutoff = datetime.utcnow() - timedelta(days=days)

        successful = 0
        failed = 0

        for event in self._events:
            if event.project_id == project_id and event.timestamp >= cutoff:
                if event.event_type == MetricEventType.ANCHOR_JUMP_SUCCESS:
                    successful += 1
                elif event.event_type == MetricEventType.ANCHOR_JUMP_FAILURE:
                    failed += 1

        metric = AnchorJumpMetric(
            project_id=project_id,
            total_jumps=successful + failed,
            successful_jumps=successful,
            failed_jumps=failed,
        )
        metric.calculate_rate()

        return metric

    # =========================================================================
    # Citation Coverage
    # =========================================================================

    def calculate_citation_coverage(
        self,
        project_id: UUID,
        claims_with_anchors: int,
        total_claims: int,
    ) -> CitationCoverageMetric:
        """
        Calculate citation coverage for a project.

        Args:
            project_id: Project ID
            claims_with_anchors: Number of claims with at least one anchor
            total_claims: Total number of claims

        Returns:
            Citation coverage metric
        """
        metric = CitationCoverageMetric(
            project_id=project_id,
            total_claims=total_claims,
            claims_with_evidence=claims_with_anchors,
        )
        metric.calculate_rate()

        return metric

    # =========================================================================
    # Summary
    # =========================================================================

    def get_project_metrics_summary(
        self,
        project_id: UUID,
        checkpoint_ids: Optional[List[str]] = None,
        claims_with_anchors: int = 0,
        total_claims: int = 0,
    ) -> Dict[str, Any]:
        """
        Get a summary of all metrics for a project.

        Args:
            project_id: Project ID
            checkpoint_ids: List of checkpoint IDs
            claims_with_anchors: Claims with evidence
            total_claims: Total claims

        Returns:
            Summary of all metrics
        """
        ttr_stats = self.get_ttr_stats(project_id)
        anchor_stats = self.get_anchor_jump_stats(project_id)

        checkpoint_stats = None
        if checkpoint_ids:
            checkpoint_metric = self.get_checkpoint_revisit_stats(project_id, checkpoint_ids)
            checkpoint_stats = {
                "total": checkpoint_metric.total_checkpoints,
                "revisited": checkpoint_metric.revisited_checkpoints,
                "revisit_rate": checkpoint_metric.revisit_rate,
            }

        coverage_metric = self.calculate_citation_coverage(
            project_id, claims_with_anchors, total_claims
        )

        return {
            "project_id": str(project_id),
            "ttr": ttr_stats,
            "checkpoint_revisit": checkpoint_stats,
            "anchor_jump": {
                "total": anchor_stats.total_jumps,
                "success_rate": anchor_stats.success_rate,
            },
            "citation_coverage": {
                "total_claims": coverage_metric.total_claims,
                "with_evidence": coverage_metric.claims_with_evidence,
                "coverage_rate": coverage_metric.coverage_rate,
            },
        }


# Global singleton for metrics service
_metrics_service: Optional[ThinkingPathMetricsService] = None


def get_metrics_service() -> ThinkingPathMetricsService:
    """Get the global metrics service instance."""
    global _metrics_service
    if _metrics_service is None:
        _metrics_service = ThinkingPathMetricsService()
    return _metrics_service














