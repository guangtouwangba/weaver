"""
Research routes - thin delegation layer to controllers.
"""
import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends, WebSocket

from models.schemas.research import (
    ChatRequest, ChatResponse, AnalysisRequest, AnalysisResponse, 
    QuickAnalysisRequest, QuickAnalysisResponse, AnalysisProgress
)
from models.schemas.common import HealthResponse
from controllers.research_controller import ResearchController
from services.research_service import ResearchService
from core.dependencies import get_research_service, get_orchestrator
from utils.analysis_websocket_manager import analysis_connection_manager

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

@router.post("/analysis/start", response_model=AnalysisResponse)
async def start_analysis(
    request: AnalysisRequest,
    controller: ResearchController = Depends(get_research_controller)
):
    """
    Start a new research analysis with real-time progress tracking
    
    This endpoint initiates a comprehensive research analysis that includes:
    - Paper retrieval from vector database and ArXiv
    - Multi-agent collaborative analysis
    - Real-time progress updates via WebSocket
    """
    return await controller.start_analysis(request)

@router.get("/analysis/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis_status(
    analysis_id: str,
    controller: ResearchController = Depends(get_research_controller)
):
    """Get the current status and progress of an analysis"""
    return await controller.get_analysis_status(analysis_id)

@router.post("/analysis/quick", response_model=QuickAnalysisResponse)
async def quick_analysis(
    request: QuickAnalysisRequest,
    controller: ResearchController = Depends(get_research_controller)
):
    """
    Perform a quick paper search and relevance analysis
    
    This endpoint provides fast preliminary results for the frontend's
    "开始分析" feature before initiating full analysis.
    """
    return await controller.quick_analysis(request)

@router.websocket("/analysis/{analysis_id}/ws")
async def analysis_websocket(websocket: WebSocket, analysis_id: str):
    """
    WebSocket endpoint for real-time analysis progress updates
    
    Clients can connect to this endpoint to receive real-time updates
    about the progress of their analysis including:
    - Step progress updates
    - Papers found notifications  
    - Agent insights as they're generated
    - Analysis completion status
    """
    await analysis_connection_manager.handle_websocket_connection(websocket, analysis_id)