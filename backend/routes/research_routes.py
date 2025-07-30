"""
Research routes - thin delegation layer to controllers.
"""
import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends

from models.schemas.research import ChatRequest, ChatResponse
from models.schemas.common import HealthResponse
from controllers.research_controller import ResearchController
from services.research_service import ResearchService
from core.dependencies import get_research_service, get_orchestrator

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(tags=["research"])

def get_research_controller(
    research_service: ResearchService = Depends(get_research_service)
) -> ResearchController:
    """Dependency for getting research controller"""
    orchestrator = get_orchestrator()
    return ResearchController(research_service, orchestrator)

# Routes
@router.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint"""
    return {
        "message": "Research Agent RAG API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@router.get("/health", response_model=HealthResponse)
async def health_check(
    controller: ResearchController = Depends(get_research_controller)
):
    """Health check endpoint for load balancers and monitoring"""
    return await controller.health_check()

@router.get("/config", response_model=Dict[str, Any])
async def get_config(
    controller: ResearchController = Depends(get_research_controller)
):
    """Get current system configuration (non-sensitive data)"""
    return await controller.get_config()

@router.post("/chat", response_model=ChatResponse)
async def chat_with_papers(
    request: ChatRequest,
    controller: ResearchController = Depends(get_research_controller)
):
    """
    Main chat endpoint for research paper analysis
    
    This endpoint processes research queries through multi-agent iterative discussion
    and returns comprehensive analysis with Chinese final conclusions.
    """
    return await controller.chat_with_papers(request)

@router.get("/stats", response_model=Dict[str, Any])
async def get_database_stats(
    controller: ResearchController = Depends(get_research_controller)
):
    """Get database statistics"""
    return await controller.get_database_stats()