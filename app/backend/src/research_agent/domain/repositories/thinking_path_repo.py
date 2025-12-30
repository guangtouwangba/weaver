"""Repository interface for Thinking Path entities."""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from research_agent.domain.entities.thinking_path import (
    ClaimNode,
    ConceptNode,
    QuestionNode,
    ResumeModeSummary,
    SourceAnchor,
    ThinkingPathCheckpoint,
    ThinkingPathEvent,
)


class ThinkingPathRepository(ABC):
    """Abstract repository for Thinking Path operations."""

    # =========================================================================
    # Source Anchors
    # =========================================================================

    @abstractmethod
    async def create_anchor(self, anchor: SourceAnchor) -> SourceAnchor:
        """Create a new source anchor."""
        pass

    @abstractmethod
    async def get_anchor(self, anchor_id: UUID) -> Optional[SourceAnchor]:
        """Get an anchor by ID."""
        pass

    @abstractmethod
    async def get_anchors_by_project(self, project_id: UUID) -> List[SourceAnchor]:
        """Get all anchors for a project."""
        pass

    @abstractmethod
    async def update_anchor(self, anchor: SourceAnchor) -> SourceAnchor:
        """Update an existing anchor."""
        pass

    @abstractmethod
    async def delete_anchor(self, anchor_id: UUID) -> bool:
        """Delete an anchor."""
        pass

    # =========================================================================
    # Claim Nodes
    # =========================================================================

    @abstractmethod
    async def create_claim(self, claim: ClaimNode) -> ClaimNode:
        """Create a new claim node."""
        pass

    @abstractmethod
    async def get_claim(self, claim_id: UUID) -> Optional[ClaimNode]:
        """Get a claim by ID."""
        pass

    @abstractmethod
    async def get_claim_by_canvas_node(
        self, project_id: UUID, canvas_node_id: str
    ) -> Optional[ClaimNode]:
        """Get a claim by its canvas node ID."""
        pass

    @abstractmethod
    async def get_claims_by_project(self, project_id: UUID) -> List[ClaimNode]:
        """Get all claims for a project."""
        pass

    @abstractmethod
    async def update_claim(self, claim: ClaimNode) -> ClaimNode:
        """Update an existing claim."""
        pass

    @abstractmethod
    async def delete_claim(self, claim_id: UUID) -> bool:
        """Delete a claim."""
        pass

    # =========================================================================
    # Question Nodes
    # =========================================================================

    @abstractmethod
    async def create_question(self, question: QuestionNode) -> QuestionNode:
        """Create a new question node."""
        pass

    @abstractmethod
    async def get_question(self, question_id: UUID) -> Optional[QuestionNode]:
        """Get a question by ID."""
        pass

    @abstractmethod
    async def get_questions_by_project(
        self, project_id: UUID, status: Optional[str] = None
    ) -> List[QuestionNode]:
        """Get all questions for a project, optionally filtered by status."""
        pass

    @abstractmethod
    async def update_question(self, question: QuestionNode) -> QuestionNode:
        """Update an existing question."""
        pass

    @abstractmethod
    async def delete_question(self, question_id: UUID) -> bool:
        """Delete a question."""
        pass

    # =========================================================================
    # Concept Nodes
    # =========================================================================

    @abstractmethod
    async def create_concept(self, concept: ConceptNode) -> ConceptNode:
        """Create a new concept node."""
        pass

    @abstractmethod
    async def get_concept(self, concept_id: UUID) -> Optional[ConceptNode]:
        """Get a concept by ID."""
        pass

    @abstractmethod
    async def get_concepts_by_project(self, project_id: UUID) -> List[ConceptNode]:
        """Get all concepts for a project."""
        pass

    @abstractmethod
    async def update_concept(self, concept: ConceptNode) -> ConceptNode:
        """Update an existing concept."""
        pass

    @abstractmethod
    async def delete_concept(self, concept_id: UUID) -> bool:
        """Delete a concept."""
        pass

    # =========================================================================
    # Thinking Path Events
    # =========================================================================

    @abstractmethod
    async def create_event(self, event: ThinkingPathEvent) -> ThinkingPathEvent:
        """Record a new thinking path event."""
        pass

    @abstractmethod
    async def get_events_by_project(
        self, project_id: UUID, limit: int = 50, offset: int = 0
    ) -> List[ThinkingPathEvent]:
        """Get recent events for a project."""
        pass

    @abstractmethod
    async def get_events_by_node(self, project_id: UUID, node_id: str) -> List[ThinkingPathEvent]:
        """Get all events for a specific node."""
        pass

    # =========================================================================
    # Checkpoints
    # =========================================================================

    @abstractmethod
    async def create_checkpoint(self, checkpoint: ThinkingPathCheckpoint) -> ThinkingPathCheckpoint:
        """Create a new checkpoint."""
        pass

    @abstractmethod
    async def get_checkpoint(self, checkpoint_id: UUID) -> Optional[ThinkingPathCheckpoint]:
        """Get a checkpoint by ID."""
        pass

    @abstractmethod
    async def get_checkpoints_by_project(self, project_id: UUID) -> List[ThinkingPathCheckpoint]:
        """Get all checkpoints for a project."""
        pass

    @abstractmethod
    async def get_latest_checkpoint(self, project_id: UUID) -> Optional[ThinkingPathCheckpoint]:
        """Get the most recent checkpoint for a project."""
        pass

    @abstractmethod
    async def delete_checkpoint(self, checkpoint_id: UUID) -> bool:
        """Delete a checkpoint."""
        pass

    # =========================================================================
    # Resume Mode
    # =========================================================================

    @abstractmethod
    async def get_resume_summary(self, project_id: UUID) -> ResumeModeSummary:
        """
        Get the resume mode summary for a project.

        This aggregates:
        - Top clusters (groups of related claims)
        - Open questions
        - Recent changes
        - Last checkpoint
        """
        pass
















