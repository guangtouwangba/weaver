"""Generate curriculum use case."""

import json
from dataclasses import dataclass
from typing import List
from uuid import UUID, uuid4

from research_agent.domain.entities.curriculum import Curriculum, CurriculumStep
from research_agent.domain.repositories.chunk_repo import ChunkRepository
from research_agent.domain.repositories.document_repo import DocumentRepository
from research_agent.infrastructure.llm.base import ChatMessage, LLMService
from research_agent.infrastructure.llm.prompts.curriculum_prompt import (
    SYSTEM_PROMPT,
    build_curriculum_prompt,
)
from research_agent.shared.utils.logger import logger


@dataclass
class GenerateCurriculumInput:
    """Input for generate curriculum use case."""
    
    project_id: UUID


@dataclass
class GenerateCurriculumOutput:
    """Output for generate curriculum use case."""
    
    steps: List[CurriculumStep]
    total_duration: int


class GenerateCurriculumUseCase:
    """Use case for generating a learning curriculum from project documents."""

    def __init__(
        self,
        document_repo: DocumentRepository,
        chunk_repo: ChunkRepository,
        llm_service: LLMService,
    ):
        self._document_repo = document_repo
        self._chunk_repo = chunk_repo
        self._llm_service = llm_service

    async def execute(self, input_data: GenerateCurriculumInput) -> GenerateCurriculumOutput:
        """Generate curriculum for a project.
        
        Strategy:
        1. Fetch all documents for the project
        2. For each document, get the first 2-3 chunks (intro/TOC)
        3. Build LLM prompt with document context
        4. Call LLM to generate curriculum steps
        5. Parse and return steps
        """
        logger.info(f"Generating curriculum for project {input_data.project_id}")
        
        # Fetch documents
        documents = await self._document_repo.find_by_project(input_data.project_id)
        
        if not documents:
            logger.warning(f"No documents found for project {input_data.project_id}")
            return GenerateCurriculumOutput(steps=[], total_duration=0)
        
        logger.info(f"Found {len(documents)} documents")
        
        # Build context from document introductions
        doc_contexts = []
        for doc in documents:
            # Get first 3 chunks of each document (representing intro/TOC)
            chunks = await self._chunk_repo.find_by_document(doc.id)
            intro_chunks = chunks[:3] if chunks else []
            
            intro_content = "\n\n".join([chunk.content for chunk in intro_chunks])
            
            doc_contexts.append({
                "id": str(doc.id),
                "title": doc.original_filename,
                "intro_content": intro_content[:2000],  # Limit to 2000 chars per doc
                "page_count": doc.page_count or "?",
            })
        
        # Build prompt
        user_prompt = build_curriculum_prompt(doc_contexts)
        
        # Call LLM
        messages = [
            ChatMessage(role="system", content=SYSTEM_PROMPT),
            ChatMessage(role="user", content=user_prompt),
        ]
        
        logger.info("Calling LLM to generate curriculum")
        response = await self._llm_service.chat(messages)
        
        # Parse response
        try:
            # Extract JSON from response (LLM might wrap it in markdown code blocks)
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:]  # Remove ```json
            if content.startswith("```"):
                content = content[3:]  # Remove ```
            if content.endswith("```"):
                content = content[:-3]  # Remove trailing ```
            
            content = content.strip()
            
            steps_data = json.loads(content)
            
            if not isinstance(steps_data, list):
                raise ValueError("LLM response is not a JSON array")
            
            # Convert to domain entities
            steps = []
            total_duration = 0
            
            for i, step_data in enumerate(steps_data):
                step = CurriculumStep(
                    id=str(i + 1),  # Simple sequential ID
                    title=step_data.get("title", f"Step {i + 1}"),
                    source=step_data.get("source", "Unknown"),
                    source_type=step_data.get("sourceType", "document"),
                    page_range=step_data.get("pageRange"),
                    duration=step_data.get("duration", 10),
                )
                steps.append(step)
                total_duration += step.duration
            
            logger.info(f"Generated curriculum with {len(steps)} steps, total {total_duration} min")
            
            return GenerateCurriculumOutput(steps=steps, total_duration=total_duration)
            
        except Exception as e:
            logger.error(f"Failed to parse LLM response: {e}", exc_info=True)
            logger.error(f"LLM response: {response.content}")
            raise ValueError(f"Failed to parse curriculum from LLM response: {e}")

