"""
Cronjob routes - thin delegation layer to controllers.
"""
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends

from models.schemas.cronjob import (
    CronJobCreate, CronJobUpdate, CronJobResponse,
    JobRunResponse, JobTriggerRequest, JobTriggerResponse
)
from controllers.cronjob_controller import CronJobController
from services.cronjob_service import CronJobService
from core.dependencies import get_cronjob_service
from database.config_manager import get_config_manager

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/cronjobs", tags=["cronjobs"])

def get_cronjob_controller(
    cronjob_service: CronJobService = Depends(get_cronjob_service)
) -> CronJobController:
    """Dependency for getting cronjob controller"""
    return CronJobController(cronjob_service)

# Routes
@router.get("/", response_model=List[CronJobResponse])
async def list_cronjobs(
    skip: int = 0,
    limit: int = 100,
    enabled_only: bool = False,
    controller: CronJobController = Depends(get_cronjob_controller)
):
    """List all cronjobs"""
    return await controller.list_cronjobs(skip, limit, enabled_only)

# Global history endpoints (must be before /{job_id} routes)
@router.get("/history/runs", response_model=List[JobRunResponse])
async def list_all_job_runs(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = None,
    job_id_filter: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    controller: CronJobController = Depends(get_cronjob_controller)
):
    """List job runs across all cronjobs with filtering options"""
    return await controller.list_all_job_runs(
        skip, limit, status_filter, job_id_filter, start_date, end_date
    )

@router.get("/history/stats")
async def get_history_stats(
    days: int = 30,
    controller: CronJobController = Depends(get_cronjob_controller)
):
    """Get historical statistics and trends"""
    return await controller.get_history_stats(days)

@router.get("/history/export")
async def export_history(
    format: str = "csv",
    status_filter: Optional[str] = None,
    job_id_filter: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    controller: CronJobController = Depends(get_cronjob_controller)
):
    """Export job run history in various formats"""
    from fastapi.responses import Response
    
    export_data = await controller.export_history(
        format, status_filter, job_id_filter, start_date, end_date
    )
    
    return Response(
        content=export_data["content"],
        media_type=export_data["content_type"],
        headers={"Content-Disposition": f"attachment; filename={export_data['filename']}"}
    )

@router.post("/", response_model=CronJobResponse, status_code=201)
async def create_cronjob(
    job_data: CronJobCreate,
    controller: CronJobController = Depends(get_cronjob_controller)
):
    """Create a new cronjob"""
    return await controller.create_cronjob(job_data)

@router.get("/{job_id}", response_model=CronJobResponse)
async def get_cronjob(
    job_id: str,
    controller: CronJobController = Depends(get_cronjob_controller)
):
    """Get a specific cronjob"""
    return await controller.get_cronjob(job_id)

@router.put("/{job_id}", response_model=CronJobResponse)
async def update_cronjob(
    job_id: str,
    job_data: CronJobUpdate,
    controller: CronJobController = Depends(get_cronjob_controller)
):
    """Update a cronjob"""
    return await controller.update_cronjob(job_id, job_data)

@router.delete("/{job_id}")
async def delete_cronjob(
    job_id: str,
    controller: CronJobController = Depends(get_cronjob_controller)
):
    """Delete a cronjob"""
    return await controller.delete_cronjob(job_id)

@router.patch("/{job_id}/toggle", response_model=CronJobResponse)
async def toggle_cronjob(
    job_id: str,
    controller: CronJobController = Depends(get_cronjob_controller)
):
    """Toggle cronjob enabled/disabled status"""
    return await controller.toggle_cronjob(job_id)

@router.post("/{job_id}/trigger", response_model=JobTriggerResponse)
async def trigger_cronjob(
    job_id: str,
    request: JobTriggerRequest,
    background_tasks: BackgroundTasks,
    controller: CronJobController = Depends(get_cronjob_controller)
):
    """Manually trigger a cronjob execution"""
    return await controller.trigger_cronjob(job_id, request, background_tasks)

@router.get("/{job_id}/runs", response_model=List[JobRunResponse])
async def list_job_runs(
    job_id: str,
    skip: int = 0,
    limit: int = 50,
    status_filter: Optional[str] = None,
    controller: CronJobController = Depends(get_cronjob_controller)
):
    """List job runs for a specific cronjob"""
    return await controller.list_job_runs(job_id, skip, limit, status_filter)

@router.get("/{job_id}/status")
async def get_job_status(
    job_id: str,
    controller: CronJobController = Depends(get_cronjob_controller)
):
    """Get current status of a cronjob"""
    return await controller.get_job_status(job_id)

@router.get("/runs/{run_id}", response_model=JobRunResponse)
async def get_job_run(
    run_id: str,
    controller: CronJobController = Depends(get_cronjob_controller)
):
    """Get details of a specific job run"""
    return await controller.get_job_run(run_id)


@router.get("/providers/available")
async def get_available_providers():
    """Get available vector database and embedding providers"""
    try:
        config_manager = get_config_manager()
        providers = config_manager.get_available_providers()
        
        return {
            "vector_databases": providers['vector_db'],
            "embedding_models": providers['embedding']
        }
        
    except Exception as e:
        logger.error(f"Error getting available providers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test-configuration")
async def test_configuration(
    config_type: str,
    provider: str,
    config: Dict[str, Any]
):
    """Test a provider configuration"""
    try:
        config_manager = get_config_manager()
        
        if config_type == "vector_db":
            from database.vector_db import VectorDBFactory
            instance = VectorDBFactory.create(provider, config)
            result = instance.health_check()
        elif config_type == "embedding":
            from database.embeddings import EmbeddingModelFactory
            model_name = config.pop('model_name', 'default')
            instance = EmbeddingModelFactory.create(provider, model_name, config)
            result = instance.health_check()
        else:
            raise HTTPException(status_code=400, detail=f"Unknown config type: {config_type}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error testing configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))

