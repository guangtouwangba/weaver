"""SQLAlchemy implementation of ThinkingPathRepository."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.domain.entities.thinking_path import (
    AnchorStatus,
    CheckpointMethod,
    ClaimNode,
    ClaimStatus,
    ConceptDefinition,
    ConceptNode,
    CreatedFrom,
    QuestionNode,
    QuestionPriority,
    QuestionStatus,
    ResumeModeSummary,
    SourceAnchor,
    ThinkingPathCheckpoint,
    ThinkingPathEvent,
    ThinkingPathEventType,
)
from research_agent.domain.repositories.thinking_path_repo import ThinkingPathRepository
from research_agent.infrastructure.database.models import (
    ClaimNodeModel,
    ConceptNodeModel,
    QuestionNodeModel,
    SourceAnchorModel,
    ThinkingPathCheckpointModel,
    ThinkingPathEventModel,
)
from research_agent.shared.utils.logger import logger


class SQLAlchemyThinkingPathRepository(ThinkingPathRepository):
    """SQLAlchemy implementation of thinking path repository."""

    def __init__(self, session: AsyncSession):
        self._session = session

    # =========================================================================
    # Source Anchors
    # =========================================================================

    async def create_anchor(self, anchor: SourceAnchor) -> SourceAnchor:
        """Create a new source anchor."""
        model = SourceAnchorModel(
            id=anchor.id,
            project_id=anchor.project_id,
            source_type=anchor.source_type,
            source_id=anchor.source_id,
            source_url=anchor.source_url,
            quote_text=anchor.quote_text,
            locator=anchor.locator,
            status=anchor.status.value
            if isinstance(anchor.status, AnchorStatus)
            else anchor.status,
        )
        self._session.add(model)
        await self._session.flush()
        anchor.created_at = model.created_at
        anchor.updated_at = model.updated_at
        return anchor

    async def get_anchor(self, anchor_id: UUID) -> Optional[SourceAnchor]:
        """Get an anchor by ID."""
        result = await self._session.execute(
            select(SourceAnchorModel).where(SourceAnchorModel.id == anchor_id)
        )
        model = result.scalar_one_or_none()
        return self._anchor_model_to_entity(model) if model else None

    async def get_anchors_by_project(self, project_id: UUID) -> List[SourceAnchor]:
        """Get all anchors for a project."""
        result = await self._session.execute(
            select(SourceAnchorModel)
            .where(SourceAnchorModel.project_id == project_id)
            .order_by(desc(SourceAnchorModel.created_at))
        )
        models = result.scalars().all()
        return [self._anchor_model_to_entity(m) for m in models]

    async def update_anchor(self, anchor: SourceAnchor) -> SourceAnchor:
        """Update an existing anchor."""
        result = await self._session.execute(
            select(SourceAnchorModel).where(SourceAnchorModel.id == anchor.id)
        )
        model = result.scalar_one_or_none()
        if model:
            model.source_type = anchor.source_type
            model.source_id = anchor.source_id
            model.source_url = anchor.source_url
            model.quote_text = anchor.quote_text
            model.locator = anchor.locator
            model.status = (
                anchor.status.value if isinstance(anchor.status, AnchorStatus) else anchor.status
            )
            await self._session.flush()
            anchor.updated_at = model.updated_at
        return anchor

    async def delete_anchor(self, anchor_id: UUID) -> bool:
        """Delete an anchor."""
        result = await self._session.execute(
            select(SourceAnchorModel).where(SourceAnchorModel.id == anchor_id)
        )
        model = result.scalar_one_or_none()
        if model:
            await self._session.delete(model)
            await self._session.flush()
            return True
        return False

    def _anchor_model_to_entity(self, model: SourceAnchorModel) -> SourceAnchor:
        """Convert model to entity."""
        return SourceAnchor(
            id=model.id,
            project_id=model.project_id,
            source_type=model.source_type,
            source_id=model.source_id,
            source_url=model.source_url,
            quote_text=model.quote_text,
            locator=model.locator or {},
            status=AnchorStatus(model.status) if model.status else AnchorStatus.VALID,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    # =========================================================================
    # Claim Nodes
    # =========================================================================

    async def create_claim(self, claim: ClaimNode) -> ClaimNode:
        """Create a new claim node."""
        model = ClaimNodeModel(
            id=claim.id,
            project_id=claim.project_id,
            canvas_node_id=claim.canvas_node_id,
            title=claim.title,
            statement=claim.statement,
            confidence=claim.confidence,
            status=claim.status.value if isinstance(claim.status, ClaimStatus) else claim.status,
            evidence_anchor_ids=claim.evidence_anchor_ids,
            counter_evidence_anchor_ids=claim.counter_evidence_anchor_ids,
            assumptions=claim.assumptions,
            tags=claim.tags,
            created_from=claim.created_from.value
            if isinstance(claim.created_from, CreatedFrom)
            else claim.created_from,
        )
        self._session.add(model)
        await self._session.flush()
        claim.created_at = model.created_at
        claim.updated_at = model.updated_at
        return claim

    async def get_claim(self, claim_id: UUID) -> Optional[ClaimNode]:
        """Get a claim by ID."""
        result = await self._session.execute(
            select(ClaimNodeModel).where(ClaimNodeModel.id == claim_id)
        )
        model = result.scalar_one_or_none()
        return self._claim_model_to_entity(model) if model else None

    async def get_claim_by_canvas_node(
        self, project_id: UUID, canvas_node_id: str
    ) -> Optional[ClaimNode]:
        """Get a claim by its canvas node ID."""
        result = await self._session.execute(
            select(ClaimNodeModel).where(
                ClaimNodeModel.project_id == project_id,
                ClaimNodeModel.canvas_node_id == canvas_node_id,
            )
        )
        model = result.scalar_one_or_none()
        return self._claim_model_to_entity(model) if model else None

    async def get_claims_by_project(self, project_id: UUID) -> List[ClaimNode]:
        """Get all claims for a project."""
        result = await self._session.execute(
            select(ClaimNodeModel)
            .where(ClaimNodeModel.project_id == project_id)
            .order_by(desc(ClaimNodeModel.updated_at))
        )
        models = result.scalars().all()
        return [self._claim_model_to_entity(m) for m in models]

    async def update_claim(self, claim: ClaimNode) -> ClaimNode:
        """Update an existing claim."""
        result = await self._session.execute(
            select(ClaimNodeModel).where(ClaimNodeModel.id == claim.id)
        )
        model = result.scalar_one_or_none()
        if model:
            model.title = claim.title
            model.statement = claim.statement
            model.confidence = claim.confidence
            model.status = (
                claim.status.value if isinstance(claim.status, ClaimStatus) else claim.status
            )
            model.evidence_anchor_ids = claim.evidence_anchor_ids
            model.counter_evidence_anchor_ids = claim.counter_evidence_anchor_ids
            model.assumptions = claim.assumptions
            model.tags = claim.tags
            await self._session.flush()
            claim.updated_at = model.updated_at
        return claim

    async def delete_claim(self, claim_id: UUID) -> bool:
        """Delete a claim."""
        result = await self._session.execute(
            select(ClaimNodeModel).where(ClaimNodeModel.id == claim_id)
        )
        model = result.scalar_one_or_none()
        if model:
            await self._session.delete(model)
            await self._session.flush()
            return True
        return False

    def _claim_model_to_entity(self, model: ClaimNodeModel) -> ClaimNode:
        """Convert model to entity."""
        return ClaimNode(
            id=model.id,
            project_id=model.project_id,
            canvas_node_id=model.canvas_node_id,
            title=model.title,
            statement=model.statement,
            confidence=model.confidence,
            status=ClaimStatus(model.status) if model.status else ClaimStatus.TENTATIVE,
            evidence_anchor_ids=model.evidence_anchor_ids or [],
            counter_evidence_anchor_ids=model.counter_evidence_anchor_ids or [],
            assumptions=model.assumptions or [],
            tags=model.tags or [],
            created_from=CreatedFrom(model.created_from)
            if model.created_from
            else CreatedFrom.DRAG,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    # =========================================================================
    # Question Nodes
    # =========================================================================

    async def create_question(self, question: QuestionNode) -> QuestionNode:
        """Create a new question node."""
        model = QuestionNodeModel(
            id=question.id,
            project_id=question.project_id,
            canvas_node_id=question.canvas_node_id,
            question_text=question.question_text,
            status=question.status.value
            if isinstance(question.status, QuestionStatus)
            else question.status,
            related_claim_ids=question.related_claim_ids,
            related_concept_ids=question.related_concept_ids,
            priority=question.priority.value
            if isinstance(question.priority, QuestionPriority)
            else question.priority,
            tags=question.tags,
            created_from=question.created_from.value
            if isinstance(question.created_from, CreatedFrom)
            else question.created_from,
        )
        self._session.add(model)
        await self._session.flush()
        question.created_at = model.created_at
        question.updated_at = model.updated_at
        return question

    async def get_question(self, question_id: UUID) -> Optional[QuestionNode]:
        """Get a question by ID."""
        result = await self._session.execute(
            select(QuestionNodeModel).where(QuestionNodeModel.id == question_id)
        )
        model = result.scalar_one_or_none()
        return self._question_model_to_entity(model) if model else None

    async def get_questions_by_project(
        self, project_id: UUID, status: Optional[str] = None
    ) -> List[QuestionNode]:
        """Get all questions for a project, optionally filtered by status."""
        query = select(QuestionNodeModel).where(QuestionNodeModel.project_id == project_id)
        if status:
            query = query.where(QuestionNodeModel.status == status)
        query = query.order_by(desc(QuestionNodeModel.updated_at))

        result = await self._session.execute(query)
        models = result.scalars().all()
        return [self._question_model_to_entity(m) for m in models]

    async def update_question(self, question: QuestionNode) -> QuestionNode:
        """Update an existing question."""
        result = await self._session.execute(
            select(QuestionNodeModel).where(QuestionNodeModel.id == question.id)
        )
        model = result.scalar_one_or_none()
        if model:
            model.question_text = question.question_text
            model.status = (
                question.status.value
                if isinstance(question.status, QuestionStatus)
                else question.status
            )
            model.related_claim_ids = question.related_claim_ids
            model.related_concept_ids = question.related_concept_ids
            model.priority = (
                question.priority.value
                if isinstance(question.priority, QuestionPriority)
                else question.priority
            )
            model.tags = question.tags
            await self._session.flush()
            question.updated_at = model.updated_at
        return question

    async def delete_question(self, question_id: UUID) -> bool:
        """Delete a question."""
        result = await self._session.execute(
            select(QuestionNodeModel).where(QuestionNodeModel.id == question_id)
        )
        model = result.scalar_one_or_none()
        if model:
            await self._session.delete(model)
            await self._session.flush()
            return True
        return False

    def _question_model_to_entity(self, model: QuestionNodeModel) -> QuestionNode:
        """Convert model to entity."""
        return QuestionNode(
            id=model.id,
            project_id=model.project_id,
            canvas_node_id=model.canvas_node_id,
            question_text=model.question_text,
            status=QuestionStatus(model.status) if model.status else QuestionStatus.OPEN,
            related_claim_ids=model.related_claim_ids or [],
            related_concept_ids=model.related_concept_ids or [],
            priority=QuestionPriority(model.priority)
            if model.priority
            else QuestionPriority.MEDIUM,
            tags=model.tags or [],
            created_from=CreatedFrom(model.created_from)
            if model.created_from
            else CreatedFrom.DRAG,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    # =========================================================================
    # Concept Nodes
    # =========================================================================

    async def create_concept(self, concept: ConceptNode) -> ConceptNode:
        """Create a new concept node."""
        definitions_data = [
            {"text": d.text, "source_anchor_id": d.source_anchor_id} for d in concept.definitions
        ]
        model = ConceptNodeModel(
            id=concept.id,
            project_id=concept.project_id,
            canvas_node_id=concept.canvas_node_id,
            name=concept.name,
            definitions=definitions_data,
            synonyms=concept.synonyms,
            related_concept_ids=concept.related_concept_ids,
            tags=concept.tags,
            created_from=concept.created_from.value
            if isinstance(concept.created_from, CreatedFrom)
            else concept.created_from,
        )
        self._session.add(model)
        await self._session.flush()
        concept.created_at = model.created_at
        concept.updated_at = model.updated_at
        return concept

    async def get_concept(self, concept_id: UUID) -> Optional[ConceptNode]:
        """Get a concept by ID."""
        result = await self._session.execute(
            select(ConceptNodeModel).where(ConceptNodeModel.id == concept_id)
        )
        model = result.scalar_one_or_none()
        return self._concept_model_to_entity(model) if model else None

    async def get_concepts_by_project(self, project_id: UUID) -> List[ConceptNode]:
        """Get all concepts for a project."""
        result = await self._session.execute(
            select(ConceptNodeModel)
            .where(ConceptNodeModel.project_id == project_id)
            .order_by(desc(ConceptNodeModel.updated_at))
        )
        models = result.scalars().all()
        return [self._concept_model_to_entity(m) for m in models]

    async def update_concept(self, concept: ConceptNode) -> ConceptNode:
        """Update an existing concept."""
        result = await self._session.execute(
            select(ConceptNodeModel).where(ConceptNodeModel.id == concept.id)
        )
        model = result.scalar_one_or_none()
        if model:
            definitions_data = [
                {"text": d.text, "source_anchor_id": d.source_anchor_id}
                for d in concept.definitions
            ]
            model.name = concept.name
            model.definitions = definitions_data
            model.synonyms = concept.synonyms
            model.related_concept_ids = concept.related_concept_ids
            model.tags = concept.tags
            await self._session.flush()
            concept.updated_at = model.updated_at
        return concept

    async def delete_concept(self, concept_id: UUID) -> bool:
        """Delete a concept."""
        result = await self._session.execute(
            select(ConceptNodeModel).where(ConceptNodeModel.id == concept_id)
        )
        model = result.scalar_one_or_none()
        if model:
            await self._session.delete(model)
            await self._session.flush()
            return True
        return False

    def _concept_model_to_entity(self, model: ConceptNodeModel) -> ConceptNode:
        """Convert model to entity."""
        definitions = [
            ConceptDefinition(
                text=d.get("text", ""),
                source_anchor_id=d.get("source_anchor_id"),
            )
            for d in (model.definitions or [])
        ]
        return ConceptNode(
            id=model.id,
            project_id=model.project_id,
            canvas_node_id=model.canvas_node_id,
            name=model.name,
            definitions=definitions,
            synonyms=model.synonyms or [],
            related_concept_ids=model.related_concept_ids or [],
            tags=model.tags or [],
            created_from=CreatedFrom(model.created_from)
            if model.created_from
            else CreatedFrom.DRAG,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    # =========================================================================
    # Thinking Path Events
    # =========================================================================

    async def create_event(self, event: ThinkingPathEvent) -> ThinkingPathEvent:
        """Record a new thinking path event."""
        model = ThinkingPathEventModel(
            id=event.id,
            project_id=event.project_id,
            event_type=event.event_type.value
            if isinstance(event.event_type, ThinkingPathEventType)
            else event.event_type,
            node_id=event.node_id,
            node_type=event.node_type,
            event_data=event.event_data,
            checkpoint_id=event.checkpoint_id,
        )
        self._session.add(model)
        await self._session.flush()
        event.created_at = model.created_at
        return event

    async def get_events_by_project(
        self, project_id: UUID, limit: int = 50, offset: int = 0
    ) -> List[ThinkingPathEvent]:
        """Get recent events for a project."""
        result = await self._session.execute(
            select(ThinkingPathEventModel)
            .where(ThinkingPathEventModel.project_id == project_id)
            .order_by(desc(ThinkingPathEventModel.created_at))
            .limit(limit)
            .offset(offset)
        )
        models = result.scalars().all()
        return [self._event_model_to_entity(m) for m in models]

    async def get_events_by_node(self, project_id: UUID, node_id: str) -> List[ThinkingPathEvent]:
        """Get all events for a specific node."""
        result = await self._session.execute(
            select(ThinkingPathEventModel)
            .where(
                ThinkingPathEventModel.project_id == project_id,
                ThinkingPathEventModel.node_id == node_id,
            )
            .order_by(desc(ThinkingPathEventModel.created_at))
        )
        models = result.scalars().all()
        return [self._event_model_to_entity(m) for m in models]

    def _event_model_to_entity(self, model: ThinkingPathEventModel) -> ThinkingPathEvent:
        """Convert model to entity."""
        return ThinkingPathEvent(
            id=model.id,
            project_id=model.project_id,
            event_type=ThinkingPathEventType(model.event_type)
            if model.event_type
            else ThinkingPathEventType.CREATE_NODE,
            node_id=model.node_id,
            node_type=model.node_type,
            event_data=model.event_data or {},
            checkpoint_id=model.checkpoint_id,
            created_at=model.created_at,
        )

    # =========================================================================
    # Checkpoints
    # =========================================================================

    async def create_checkpoint(self, checkpoint: ThinkingPathCheckpoint) -> ThinkingPathCheckpoint:
        """Create a new checkpoint."""
        model = ThinkingPathCheckpointModel(
            id=checkpoint.id,
            project_id=checkpoint.project_id,
            title=checkpoint.title,
            description=checkpoint.description,
            canvas_summary=checkpoint.canvas_summary,
            created_method=checkpoint.created_method.value
            if isinstance(checkpoint.created_method, CheckpointMethod)
            else checkpoint.created_method,
        )
        self._session.add(model)
        await self._session.flush()
        checkpoint.created_at = model.created_at
        return checkpoint

    async def get_checkpoint(self, checkpoint_id: UUID) -> Optional[ThinkingPathCheckpoint]:
        """Get a checkpoint by ID."""
        result = await self._session.execute(
            select(ThinkingPathCheckpointModel).where(
                ThinkingPathCheckpointModel.id == checkpoint_id
            )
        )
        model = result.scalar_one_or_none()
        return self._checkpoint_model_to_entity(model) if model else None

    async def get_checkpoints_by_project(self, project_id: UUID) -> List[ThinkingPathCheckpoint]:
        """Get all checkpoints for a project."""
        result = await self._session.execute(
            select(ThinkingPathCheckpointModel)
            .where(ThinkingPathCheckpointModel.project_id == project_id)
            .order_by(desc(ThinkingPathCheckpointModel.created_at))
        )
        models = result.scalars().all()
        return [self._checkpoint_model_to_entity(m) for m in models]

    async def get_latest_checkpoint(self, project_id: UUID) -> Optional[ThinkingPathCheckpoint]:
        """Get the most recent checkpoint for a project."""
        result = await self._session.execute(
            select(ThinkingPathCheckpointModel)
            .where(ThinkingPathCheckpointModel.project_id == project_id)
            .order_by(desc(ThinkingPathCheckpointModel.created_at))
            .limit(1)
        )
        model = result.scalar_one_or_none()
        return self._checkpoint_model_to_entity(model) if model else None

    async def delete_checkpoint(self, checkpoint_id: UUID) -> bool:
        """Delete a checkpoint."""
        result = await self._session.execute(
            select(ThinkingPathCheckpointModel).where(
                ThinkingPathCheckpointModel.id == checkpoint_id
            )
        )
        model = result.scalar_one_or_none()
        if model:
            await self._session.delete(model)
            await self._session.flush()
            return True
        return False

    def _checkpoint_model_to_entity(
        self, model: ThinkingPathCheckpointModel
    ) -> ThinkingPathCheckpoint:
        """Convert model to entity."""
        return ThinkingPathCheckpoint(
            id=model.id,
            project_id=model.project_id,
            title=model.title,
            description=model.description,
            canvas_summary=model.canvas_summary or {},
            created_method=CheckpointMethod(model.created_method)
            if model.created_method
            else CheckpointMethod.MANUAL,
            created_at=model.created_at,
        )

    # =========================================================================
    # Resume Mode
    # =========================================================================

    async def get_resume_summary(self, project_id: UUID) -> ResumeModeSummary:
        """
        Get the resume mode summary for a project.

        MVP Strategy for top clusters:
        - Group claims by tags
        - If no tags, group by recent updates
        """
        # Get all claims
        claims = await self.get_claims_by_project(project_id)

        # Get open questions
        open_questions = await self.get_questions_by_project(project_id, status="open")

        # Get concepts
        concepts = await self.get_concepts_by_project(project_id)

        # Get recent events (last 7 days or 20 events, whichever is less)
        recent_events = await self.get_events_by_project(project_id, limit=20)

        # Get latest checkpoint
        latest_checkpoint = await self.get_latest_checkpoint(project_id)

        # Build top clusters (MVP: group by tags, max 3 clusters)
        top_clusters = self._build_clusters(claims)

        return ResumeModeSummary(
            project_id=project_id,
            top_clusters=top_clusters[:3],  # Max 3 clusters
            open_questions=open_questions[:5],  # Max 5 open questions
            recent_changes=recent_events[:10],  # Max 10 recent changes
            last_checkpoint=latest_checkpoint,
            total_claims=len(claims),
            total_questions=len(open_questions),
            total_concepts=len(concepts),
        )

    def _build_clusters(self, claims: List[ClaimNode]) -> List[dict]:
        """
        Build clusters from claims (MVP: tag-based grouping).

        Returns list of clusters:
        [
            {
                "name": "cluster_name",
                "claim_ids": ["id1", "id2"],
                "claim_count": 2
            }
        ]
        """
        # Group by tags
        tag_groups: dict = {}
        untagged_claims = []

        for claim in claims:
            if claim.tags:
                for tag in claim.tags:
                    if tag not in tag_groups:
                        tag_groups[tag] = []
                    tag_groups[tag].append(str(claim.id))
            else:
                untagged_claims.append(str(claim.id))

        # Convert to cluster format
        clusters = []
        for tag, claim_ids in sorted(tag_groups.items(), key=lambda x: len(x[1]), reverse=True):
            clusters.append(
                {
                    "name": tag,
                    "claimIds": claim_ids,
                    "claimCount": len(claim_ids),
                }
            )

        # Add "Recent" cluster for untagged or if no tags
        if untagged_claims or not clusters:
            recent_claims = [str(c.id) for c in claims[:5]]
            clusters.insert(
                0,
                {
                    "name": "Recent",
                    "claimIds": recent_claims,
                    "claimCount": len(recent_claims),
                },
            )

        return clusters

















