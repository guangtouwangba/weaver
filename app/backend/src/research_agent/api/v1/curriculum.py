"""Curriculum API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.api.deps import get_db, get_llm_service
from research_agent.application.dto.curriculum import (
    CurriculumResponse,
    CurriculumStepDTO,
    SaveCurriculumRequest,
)
from research_agent.application.use_cases.curriculum.generate_curriculum import (
    GenerateCurriculumInput,
    GenerateCurriculumUseCase,
)
from research_agent.application.use_cases.curriculum.get_curriculum import (
    GetCurriculumInput,
    GetCurriculumUseCase,
)
from research_agent.application.use_cases.curriculum.save_curriculum import (
    SaveCurriculumInput,
    SaveCurriculumUseCase,
)
from research_agent.domain.entities.curriculum import CurriculumStep
from research_agent.infrastructure.database.repositories.sqlalchemy_chunk_repo import (
    SQLAlchemyChunkRepository,
)
from research_agent.infrastructure.database.repositories.sqlalchemy_curriculum_repo import (
    SQLAlchemyCurriculumRepository,
)
from research_agent.infrastructure.database.repositories.sqlalchemy_document_repo import (
    SQLAlchemyDocumentRepository,
)
from research_agent.infrastructure.llm.openrouter import OpenRouterLLMService
from research_agent.shared.exceptions import NotFoundError

router = APIRouter()


def get_curriculum_repo(session: AsyncSession = Depends(get_db)) -> SQLAlchemyCurriculumRepository:
    """Get curriculum repository."""
    return SQLAlchemyCurriculumRepository(session)


def get_document_repo(session: AsyncSession = Depends(get_db)) -> SQLAlchemyDocumentRepository:
    """Get document repository."""
    return SQLAlchemyDocumentRepository(session)


def get_chunk_repo(session: AsyncSession = Depends(get_db)) -> SQLAlchemyChunkRepository:
    """Get chunk repository."""
    return SQLAlchemyChunkRepository(session)


@router.post("/generate", response_model=CurriculumResponse)
async def generate_curriculum(
    project_id: UUID,
    document_repo: SQLAlchemyDocumentRepository = Depends(get_document_repo),
    chunk_repo: SQLAlchemyChunkRepository = Depends(get_chunk_repo),
    curriculum_repo: SQLAlchemyCurriculumRepository = Depends(get_curriculum_repo),
    llm_service: OpenRouterLLMService = Depends(get_llm_service),
) -> CurriculumResponse:
    """Generate a new curriculum for a project using AI."""
    try:
        # Generate curriculum
        generate_use_case = GenerateCurriculumUseCase(
            document_repo=document_repo,
            chunk_repo=chunk_repo,
            llm_service=llm_service,
        )
        
        result = await generate_use_case.execute(GenerateCurriculumInput(project_id=project_id))
        
        # Auto-save the generated curriculum
        save_use_case = SaveCurriculumUseCase(curriculum_repo)
        saved_result = await save_use_case.execute(
            SaveCurriculumInput(project_id=project_id, steps=result.steps)
        )
        
        curriculum = saved_result.curriculum
        
        # Convert to DTO
        return CurriculumResponse(
            id=curriculum.id,
            projectId=curriculum.project_id,
            steps=[
                CurriculumStepDTO(
                    id=step.id,
                    title=step.title,
                    source=step.source,
                    sourceType=step.source_type,
                    pageRange=step.page_range,
                    duration=step.duration,
                )
                for step in curriculum.steps
            ],
            totalDuration=curriculum.total_duration,
            createdAt=curriculum.created_at,
            updatedAt=curriculum.updated_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate curriculum: {str(e)}")


@router.put("", response_model=CurriculumResponse)
async def save_curriculum(
    project_id: UUID,
    data: SaveCurriculumRequest,
    curriculum_repo: SQLAlchemyCurriculumRepository = Depends(get_curriculum_repo),
) -> CurriculumResponse:
    """Save or update a curriculum for a project."""
    try:
        # Convert DTOs to domain entities
        steps = [
            CurriculumStep(
                id=step.id,
                title=step.title,
                source=step.source,
                source_type=step.source_type,
                page_range=step.page_range,
                duration=step.duration,
            )
            for step in data.steps
        ]
        
        use_case = SaveCurriculumUseCase(curriculum_repo)
        result = await use_case.execute(SaveCurriculumInput(project_id=project_id, steps=steps))
        
        curriculum = result.curriculum
        
        return CurriculumResponse(
            id=curriculum.id,
            projectId=curriculum.project_id,
            steps=[
                CurriculumStepDTO(
                    id=step.id,
                    title=step.title,
                    source=step.source,
                    sourceType=step.source_type,
                    pageRange=step.page_range,
                    duration=step.duration,
                )
                for step in curriculum.steps
            ],
            totalDuration=curriculum.total_duration,
            createdAt=curriculum.created_at,
            updatedAt=curriculum.updated_at,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save curriculum: {str(e)}")


@router.get("", response_model=CurriculumResponse)
async def get_curriculum(
    project_id: UUID,
    curriculum_repo: SQLAlchemyCurriculumRepository = Depends(get_curriculum_repo),
) -> CurriculumResponse:
    """Get curriculum for a project."""
    try:
        use_case = GetCurriculumUseCase(curriculum_repo)
        result = await use_case.execute(GetCurriculumInput(project_id=project_id))
        
        curriculum = result.curriculum
        
        return CurriculumResponse(
            id=curriculum.id,
            projectId=curriculum.project_id,
            steps=[
                CurriculumStepDTO(
                    id=step.id,
                    title=step.title,
                    source=step.source,
                    sourceType=step.source_type,
                    pageRange=step.page_range,
                    duration=step.duration,
                )
                for step in curriculum.steps
            ],
            totalDuration=curriculum.total_duration,
            createdAt=curriculum.created_at,
            updatedAt=curriculum.updated_at,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get curriculum: {str(e)}")

