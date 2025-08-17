"""
FastAPI routes for topic statistics and analytics.

This module provides specialized endpoints for topic statistics,
metrics, and analytical data with optimized performance.
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, Path
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, timedelta

# File service imports
from api.unified_file_service import get_unified_file_stats_for_topic

# Application layer imports
from application.topic import TopicController, create_topic_controller

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/topics", tags=["topic-statistics"])

# Pydantic models
class TopicStatsResponse(BaseModel):
    """Comprehensive topic statistics response."""
    model_config = ConfigDict(from_attributes=True)
    
    # Basic counts
    total_files: int = Field(..., description="Total number of files")
    total_conversations: int = Field(..., description="Total number of conversations")
    total_size_bytes: int = Field(..., description="Total file size in bytes")
    total_size_mb: float = Field(..., description="Total file size in MB")
    
    # File processing metrics
    processed_files: int = Field(..., description="Successfully processed files")
    failed_files: int = Field(..., description="Failed processing files")
    pending_files: int = Field(..., description="Files pending processing")
    processing_success_rate: float = Field(..., description="Processing success rate (0-1)")
    
    # System breakdown
    legacy_files: int = Field(..., description="Files from legacy system")
    new_files: int = Field(..., description="Files from new system")
    
    # File type distribution
    file_types: Dict[str, int] = Field(default_factory=dict, description="File type counts")
    
    # Activity metrics
    recent_uploads_24h: int = Field(..., description="Files uploaded in last 24 hours")
    recent_uploads_7d: int = Field(..., description="Files uploaded in last 7 days")
    last_activity: Optional[datetime] = Field(None, description="Last file upload or modification")
    
    # Performance metrics
    avg_file_size_mb: float = Field(..., description="Average file size in MB")
    total_downloads: int = Field(..., description="Total download count")
    
    # Topic-specific metrics
    core_concepts: int = Field(..., description="Number of core concepts discovered")
    concept_relationships: int = Field(..., description="Number of concept relationships")
    missing_materials: int = Field(..., description="Number of missing materials identified")

class TopicHealthResponse(BaseModel):
    """Topic health and performance metrics."""
    
    # Overall health
    health_score: float = Field(..., description="Overall health score (0-100)")
    status: str = Field(..., description="Health status")
    
    # Performance indicators
    file_processing_health: float = Field(..., description="File processing health (0-100)")
    content_completeness: float = Field(..., description="Content completeness score (0-100)")
    activity_level: str = Field(..., description="Activity level (low/medium/high)")
    
    # Issues and recommendations
    issues: list[str] = Field(default_factory=list, description="Identified issues")
    recommendations: list[str] = Field(default_factory=list, description="Improvement recommendations")
    
    # Timestamps
    last_check: datetime = Field(..., description="Last health check timestamp")

# Dependency injection
async def get_topic_controller() -> TopicController:
    """Get topic controller instance."""
    try:
        return await create_topic_controller()
    except Exception as e:
        logger.error(f"Failed to create topic controller: {e}")
        raise HTTPException(status_code=500, detail="Failed to initialize topic service")

# API Routes

@router.get("/{topic_id}/stats", response_model=TopicStatsResponse)
async def get_topic_stats(
    topic_id: int = Path(..., description="Topic ID"),
    controller: TopicController = Depends(get_topic_controller)
) -> TopicStatsResponse:
    """
    Get comprehensive statistics for a topic.
    
    Returns detailed metrics including:
    - **File counts and sizes** by type and system
    - **Processing status** and success rates  
    - **Activity metrics** and trends
    - **Content analysis** results
    
    This endpoint is optimized for dashboard widgets and overview displays.
    Performance: ~50-100ms for typical topics.
    """
    try:
        logger.info(f"Getting comprehensive stats for topic {topic_id}")
        
        # Get topic basic info
        topic = await controller.get_topic(topic_id, False, False)
        if not topic:
            raise HTTPException(status_code=404, detail=f"Topic {topic_id} not found")
        
        # Get file statistics
        file_stats = await get_unified_file_stats_for_topic(topic_id)
        
        # Calculate activity metrics (simplified for now)
        # In a real implementation, you'd query activity logs
        recent_uploads_24h = 0  # TODO: Implement activity tracking
        recent_uploads_7d = 0   # TODO: Implement activity tracking
        last_activity = None    # TODO: Get from activity logs
        
        # Calculate health scores
        total_files = file_stats.get('total_files', 0)
        processed_files = file_stats.get('processed_files', 0)
        failed_files = file_stats.get('failed_files', 0)
        
        processing_success_rate = 0.0
        if total_files > 0:
            processing_success_rate = processed_files / total_files
        
        return TopicStatsResponse(
            # Basic counts
            total_files=total_files,
            total_conversations=topic.total_conversations,
            total_size_bytes=file_stats.get('total_size_bytes', 0),
            total_size_mb=file_stats.get('total_size_mb', 0.0),
            
            # Processing metrics
            processed_files=processed_files,
            failed_files=failed_files,
            pending_files=total_files - processed_files - failed_files,
            processing_success_rate=processing_success_rate,
            
            # System breakdown
            legacy_files=file_stats.get('legacy_files', 0),
            new_files=file_stats.get('new_files', 0),
            
            # File types (extract from system breakdown)
            file_types={},  # TODO: Implement file type analysis
            
            # Activity metrics
            recent_uploads_24h=recent_uploads_24h,
            recent_uploads_7d=recent_uploads_7d,
            last_activity=last_activity,
            
            # Performance metrics
            avg_file_size_mb=file_stats.get('avg_file_size_mb', 0.0),
            total_downloads=file_stats.get('total_downloads', 0),
            
            # Topic-specific metrics
            core_concepts=topic.core_concepts_discovered,
            concept_relationships=topic.concept_relationships,
            missing_materials=topic.missing_materials_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting stats for topic {topic_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get topic stats: {str(e)}")


@router.get("/{topic_id}/health", response_model=TopicHealthResponse)
async def get_topic_health(
    topic_id: int = Path(..., description="Topic ID"),
    controller: TopicController = Depends(get_topic_controller)
) -> TopicHealthResponse:
    """
    Get topic health assessment and recommendations.
    
    Analyzes various aspects of topic health:
    - **File processing** success rates
    - **Content completeness** assessment
    - **Activity patterns** and engagement
    - **Performance indicators**
    
    Returns actionable recommendations for improvement.
    """
    try:
        logger.info(f"Performing health check for topic {topic_id}")
        
        # Get topic and file stats
        topic = await controller.get_topic(topic_id, False, False)
        if not topic:
            raise HTTPException(status_code=404, detail=f"Topic {topic_id} not found")
        
        file_stats = await get_unified_file_stats_for_topic(topic_id)
        
        # Calculate health metrics
        total_files = file_stats.get('total_files', 0)
        processed_files = file_stats.get('processed_files', 0)
        failed_files = file_stats.get('failed_files', 0)
        
        # File processing health (0-100)
        file_processing_health = 100.0
        if total_files > 0:
            file_processing_health = (processed_files / total_files) * 100
        
        # Content completeness (based on concepts discovered)
        content_completeness = min(topic.core_concepts_discovered * 10, 100)  # Simplified
        
        # Overall health score (weighted average)
        health_score = (file_processing_health * 0.6 + content_completeness * 0.4)
        
        # Determine status
        if health_score >= 90:
            status = "excellent"
        elif health_score >= 75:
            status = "good"
        elif health_score >= 50:
            status = "fair"
        else:
            status = "poor"
        
        # Activity level assessment
        activity_level = "low"  # TODO: Implement based on recent uploads
        
        # Identify issues and recommendations
        issues = []
        recommendations = []
        
        if failed_files > 0:
            issues.append(f"{failed_files} files failed to process")
            recommendations.append("Review and reprocess failed files")
        
        if total_files == 0:
            issues.append("No files uploaded")
            recommendations.append("Upload relevant documents to improve content analysis")
        
        if topic.core_concepts_discovered < 3:
            issues.append("Low concept discovery")
            recommendations.append("Upload more diverse content to discover additional concepts")
        
        if file_processing_health < 80:
            recommendations.append("Check file formats and processing pipeline health")
        
        return TopicHealthResponse(
            health_score=health_score,
            status=status,
            file_processing_health=file_processing_health,
            content_completeness=content_completeness,
            activity_level=activity_level,
            issues=issues,
            recommendations=recommendations,
            last_check=datetime.now()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting health for topic {topic_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get topic health: {str(e)}")


@router.get("/{topic_id}/summary", response_model=Dict[str, Any])
async def get_topic_summary(
    topic_id: int = Path(..., description="Topic ID"),
    controller: TopicController = Depends(get_topic_controller)
) -> Dict[str, Any]:
    """
    Get a quick summary of topic information.
    
    Optimized for dashboard cards and quick overviews.
    Returns only essential metrics with minimal latency.
    """
    try:
        logger.info(f"Getting summary for topic {topic_id}")
        
        # Get basic topic info
        topic = await controller.get_topic(topic_id, False, False)
        if not topic:
            raise HTTPException(status_code=404, detail=f"Topic {topic_id} not found")
        
        # Get basic file stats (just counts)
        file_stats = await get_unified_file_stats_for_topic(topic_id)
        
        return {
            "id": topic.id,
            "name": topic.name,
            "status": topic.status,
            "files": file_stats.get('total_files', 0),
            "conversations": topic.total_conversations,
            "concepts": topic.core_concepts_discovered,
            "size_mb": round(file_stats.get('total_size_mb', 0.0), 1),
            "last_updated": topic.updated_at,
            "created_at": topic.created_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting summary for topic {topic_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get topic summary: {str(e)}")

# Health check for stats service
@router.get("/{topic_id}/stats/health", include_in_schema=False)
async def topic_stats_health_check(topic_id: int):
    """Health check endpoint for topic statistics service."""
    try:
        # Quick validation
        file_stats = await get_unified_file_stats_for_topic(topic_id)
        return {
            "status": "healthy",
            "service": "topic_stats_api", 
            "timestamp": datetime.now().isoformat(),
            "test_topic_id": topic_id,
            "file_count": file_stats.get('total_files', 0)
        }
    except Exception as e:
        logger.error(f"Topic stats health check failed: {e}")
        raise HTTPException(status_code=503, detail="Topic stats service unavailable")