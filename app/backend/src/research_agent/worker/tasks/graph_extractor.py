"""Graph extraction task using LLM to extract entities and relations."""

import json
import re
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.config import get_settings

settings = get_settings()
from research_agent.domain.entities.graph import (
    Entity,
    EntityType,
    KnowledgeGraph,
    Relation,
    RelationType,
)
from research_agent.infrastructure.database.models import (
    DocumentChunkModel,
    EntityModel,
    RelationModel,
)
from research_agent.infrastructure.llm.base import ChatMessage
from research_agent.infrastructure.llm.openrouter import OpenRouterLLMService
from research_agent.shared.utils.logger import logger
from research_agent.worker.tasks.base import BaseTask

# Prompt for entity and relation extraction
# Note: Double braces {{ }} are used to escape them for .format()
EXTRACTION_PROMPT = """You are a knowledge graph extraction expert. Analyze the following text and extract entities and their relationships.

## Instructions:
1. Extract important entities (people, organizations, concepts, technologies, products, events, locations, topics)
2. Identify relationships between entities
3. Provide brief descriptions for entities

## Output Format (JSON):
```json
{{
  "entities": [
    {{
      "name": "Entity Name",
      "type": "concept|person|organization|technology|product|event|location|topic|other",
      "description": "Brief description of the entity"
    }}
  ],
  "relations": [
    {{
      "source": "Source Entity Name",
      "target": "Target Entity Name",
      "type": "related_to|part_of|created_by|uses|belongs_to|mentioned_in|compared_to|depends_on|influences|similar_to|contrasts_with|implements|derived_from|other",
      "description": "Brief description of the relationship"
    }}
  ]
}}
```

## Text to analyze:
{text}

## Important:
- Only output valid JSON, no additional text
- Entity names should be concise but descriptive
- Focus on the most important entities and relationships
- Avoid duplicates
"""


class GraphExtractorTask(BaseTask):
    """Task for extracting knowledge graph from document chunks."""

    @property
    def task_type(self) -> str:
        return "extract_graph"

    async def execute(self, payload: Dict[str, Any], session: AsyncSession) -> None:
        """
        Extract entities and relations from document chunks.

        Payload:
            document_id: UUID of the document
            project_id: UUID of the project
        """
        document_id = UUID(payload["document_id"])
        project_id = UUID(payload["project_id"])

        logger.info(f"Starting graph extraction for document {document_id}")

        # Get document chunks
        chunks = await self._get_chunks(session, document_id)

        if not chunks:
            logger.warning(f"No chunks found for document {document_id}")
            return

        # Initialize LLM service
        if not settings.openrouter_api_key:
            logger.warning("OPENROUTER_API_KEY not set - skipping graph extraction")
            return

        llm = OpenRouterLLMService(
            api_key=settings.openrouter_api_key,
            model=settings.llm_model,
        )
        logger.info(f"Using LLM model: {settings.llm_model}")

        # Extract graph from chunks
        graph = KnowledgeGraph()

        # Process chunks in batches to avoid context limits
        batch_size = 3
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            combined_text = "\n\n---\n\n".join([c.content for c in batch])

            # Limit text length
            if len(combined_text) > 8000:
                combined_text = combined_text[:8000] + "..."

            try:
                entities, relations = await self._extract_from_text(llm, combined_text)

                # Add to graph with deduplication
                for entity in entities:
                    entity.project_id = project_id
                    entity.document_id = document_id
                    graph.merge_entity(entity)

                for relation in relations:
                    relation.project_id = project_id
                    graph.add_relation(relation)

            except Exception as e:
                logger.error(f"Failed to extract from chunk batch {i}: {e}", exc_info=True)
                continue

        logger.info(
            f"Extracted {len(graph.entities)} entities and {len(graph.relations)} relations"
        )

        # Save to database
        await self._save_graph(session, graph, project_id, document_id)

        logger.info(f"Graph extraction completed for document {document_id}")

    async def _get_chunks(
        self,
        session: AsyncSession,
        document_id: UUID,
    ) -> List[DocumentChunkModel]:
        """Get document chunks."""
        stmt = (
            select(DocumentChunkModel)
            .where(DocumentChunkModel.document_id == document_id)
            .order_by(DocumentChunkModel.chunk_index)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def _extract_from_text(
        self,
        llm: OpenRouterLLMService,
        text: str,
    ) -> Tuple[List[Entity], List[Relation]]:
        """Extract entities and relations from text using LLM."""
        prompt = EXTRACTION_PROMPT.format(text=text)

        messages = [ChatMessage(role="user", content=prompt)]

        response = await llm.chat(messages)

        # Parse JSON response
        entities, relations = self._parse_extraction_response(response.content)

        return entities, relations

    def _parse_extraction_response(
        self,
        response: str,
    ) -> Tuple[List[Entity], List[Relation]]:
        """Parse LLM response into entities and relations."""
        entities = []
        relations = []

        # Try to extract JSON from response
        json_match = re.search(r"```json\s*(.*?)\s*```", response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find raw JSON
            json_str = response.strip()
            # Remove any leading/trailing non-JSON content
            start = json_str.find("{")
            end = json_str.rfind("}")
            if start != -1 and end != -1:
                json_str = json_str[start : end + 1]

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response: {e}")
            return entities, relations

        # Parse entities
        for e in data.get("entities", []):
            entity_type = self._map_entity_type(e.get("type", "other"))
            entity = Entity(
                name=e.get("name", "Unknown"),
                entity_type=entity_type,
                description=e.get("description"),
            )
            entities.append(entity)

        # Parse relations
        entity_map = {e.name.lower(): e for e in entities}

        for r in data.get("relations", []):
            source_name = r.get("source", "").lower()
            target_name = r.get("target", "").lower()

            source_entity = entity_map.get(source_name)
            target_entity = entity_map.get(target_name)

            if source_entity and target_entity:
                relation_type = self._map_relation_type(r.get("type", "related_to"))
                relation = Relation(
                    source_entity_id=source_entity.id,
                    target_entity_id=target_entity.id,
                    relation_type=relation_type,
                    description=r.get("description"),
                )
                relations.append(relation)

        return entities, relations

    def _map_entity_type(self, type_str: str) -> EntityType:
        """Map string to EntityType enum."""
        type_map = {
            "person": EntityType.PERSON,
            "organization": EntityType.ORGANIZATION,
            "concept": EntityType.CONCEPT,
            "technology": EntityType.TECHNOLOGY,
            "product": EntityType.PRODUCT,
            "event": EntityType.EVENT,
            "location": EntityType.LOCATION,
            "document": EntityType.DOCUMENT,
            "topic": EntityType.TOPIC,
        }
        return type_map.get(type_str.lower(), EntityType.OTHER)

    def _map_relation_type(self, type_str: str) -> RelationType:
        """Map string to RelationType enum."""
        type_map = {
            "related_to": RelationType.RELATED_TO,
            "part_of": RelationType.PART_OF,
            "created_by": RelationType.CREATED_BY,
            "uses": RelationType.USES,
            "belongs_to": RelationType.BELONGS_TO,
            "mentioned_in": RelationType.MENTIONED_IN,
            "compared_to": RelationType.COMPARED_TO,
            "depends_on": RelationType.DEPENDS_ON,
            "influences": RelationType.INFLUENCES,
            "similar_to": RelationType.SIMILAR_TO,
            "contrasts_with": RelationType.CONTRASTS_WITH,
            "implements": RelationType.IMPLEMENTS,
            "derived_from": RelationType.DERIVED_FROM,
        }
        return type_map.get(type_str.lower(), RelationType.OTHER)

    async def _save_graph(
        self,
        session: AsyncSession,
        graph: KnowledgeGraph,
        project_id: UUID,
        document_id: UUID,
    ) -> None:
        """Save extracted graph to database."""
        # Create entity models
        entity_id_map = {}  # Map entity to its model ID

        for entity in graph.entities:
            model = EntityModel(
                id=entity.id,
                project_id=project_id,
                document_id=document_id,
                name=entity.name,
                entity_type=entity.entity_type.value,
                description=entity.description,
                entity_metadata=entity.metadata,
            )
            session.add(model)
            entity_id_map[entity.id] = model.id

        await session.flush()

        # Create relation models
        for relation in graph.relations:
            if (
                relation.source_entity_id in entity_id_map
                and relation.target_entity_id in entity_id_map
            ):
                model = RelationModel(
                    id=relation.id,
                    project_id=project_id,
                    source_entity_id=relation.source_entity_id,
                    target_entity_id=relation.target_entity_id,
                    relation_type=relation.relation_type.value,
                    description=relation.description,
                    weight=relation.weight,
                    relation_metadata=relation.metadata,
                )
                session.add(model)

        await session.flush()
        logger.info(
            f"Saved {len(graph.entities)} entities and {len(graph.relations)} relations to database"
        )
