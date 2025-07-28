"""
FastAPI routes for cronjob management with vector DB and embedding support
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session

from database.database import get_session
from database.models import CronJob, JobRun, Paper
from database.config_manager import get_config_manager
from api.cronjob_service import CronJobService

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/cronjobs", tags=["cronjobs"])

# Pydantic models for API
class CronJobCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    keywords: List[str] = Field(..., min_items=1)
    cron_expression: Optional[str] = None
    interval_hours: Optional[int] = None
    enabled: bool = True
    max_papers_per_run: int = Field(50, ge=1, le=1000)
    embedding_provider: str = Field("openai", description="Embedding provider")
    embedding_model: str = Field("text-embedding-3-small", description="Embedding model")
    vector_db_provider: str = Field("chroma", description="Vector database provider")
    vector_db_config: Optional[Dict[str, Any]] = None
    
    @validator('cron_expression', 'interval_hours')
    def validate_schedule(cls, v, values):
        cron_expr = values.get('cron_expression') if 'cron_expression' in values else v
        interval_hours = values.get('interval_hours') if 'interval_hours' in values else v
        
        if not cron_expr and not interval_hours:
            raise ValueError('Either cron_expression or interval_hours must be provided')
        if cron_expr and interval_hours:
            raise ValueError('Only one of cron_expression or interval_hours should be provided')
        
        return v

class CronJobUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    keywords: Optional[List[str]] = Field(None, min_items=1)
    cron_expression: Optional[str] = None
    interval_hours: Optional[int] = None
    enabled: Optional[bool] = None
    max_papers_per_run: Optional[int] = Field(None, ge=1, le=1000)
    embedding_provider: Optional[str] = None
    embedding_model: Optional[str] = None
    vector_db_provider: Optional[str] = None
    vector_db_config: Optional[Dict[str, Any]] = None

class CronJobResponse(BaseModel):
    id: str
    name: str
    keywords: List[str]
    cron_expression: Optional[str]
    interval_hours: Optional[int]
    enabled: bool
    max_papers_per_run: int
    embedding_provider: str
    embedding_model: str
    vector_db_provider: str
    vector_db_config: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class JobRunResponse(BaseModel):
    id: str
    job_id: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    papers_found: int
    papers_processed: int
    papers_skipped: int
    papers_embedded: int
    embedding_errors: int
    vector_db_errors: int
    error_message: Optional[str]
    execution_log: Optional[Dict[str, Any]]
    
    class Config:
        from_attributes = True

class JobTriggerRequest(BaseModel):
    force_reprocess: bool = Field(False, description="Force reprocessing of existing papers")

class JobTriggerResponse(BaseModel):
    job_run_id: str
    status: str
    message: str

# Dependency for getting cronjob service
def get_cronjob_service(session: Session = Depends(get_session)) -> CronJobService:
    return CronJobService(session)

# Routes
@router.get("/", response_model=List[CronJobResponse])
async def list_cronjobs(
    skip: int = 0,
    limit: int = 100,
    enabled_only: bool = False,
    session: Session = Depends(get_session)
):
    """List all cronjobs"""
    try:
        query = session.query(CronJob)
        
        if enabled_only:
            query = query.filter(CronJob.enabled == True)
        
        jobs = query.offset(skip).limit(limit).all()
        return [CronJobResponse.from_orm(job) for job in jobs]
        
    except Exception as e:
        logger.error(f"Error listing cronjobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=CronJobResponse, status_code=201)
async def create_cronjob(
    job_data: CronJobCreate,
    service: CronJobService = Depends(get_cronjob_service)
):
    """Create a new cronjob"""
    try:
        # Validate providers
        config_manager = get_config_manager()
        available_providers = config_manager.get_available_providers()
        
        if job_data.embedding_provider not in available_providers['embedding']:
            raise HTTPException(
                status_code=400,
                detail=f"Embedding provider '{job_data.embedding_provider}' not available"
            )
        
        if job_data.vector_db_provider not in available_providers['vector_db']:
            raise HTTPException(
                status_code=400,
                detail=f"Vector DB provider '{job_data.vector_db_provider}' not available"
            )
        
        # Create job
        job = service.create_job(job_data.dict())
        return CronJobResponse.from_orm(job)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating cronjob: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{job_id}", response_model=CronJobResponse)
async def get_cronjob(
    job_id: str,
    session: Session = Depends(get_session)
):
    """Get a specific cronjob"""
    try:
        job = session.query(CronJob).filter(CronJob.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Cronjob not found")
        
        return CronJobResponse.from_orm(job)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting cronjob {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{job_id}", response_model=CronJobResponse)
async def update_cronjob(
    job_id: str,
    job_data: CronJobUpdate,
    service: CronJobService = Depends(get_cronjob_service)
):
    """Update a cronjob"""
    try:
        # Validate providers if specified
        if job_data.embedding_provider or job_data.vector_db_provider:
            config_manager = get_config_manager()
            available_providers = config_manager.get_available_providers()
            
            if job_data.embedding_provider and job_data.embedding_provider not in available_providers['embedding']:
                raise HTTPException(
                    status_code=400,
                    detail=f"Embedding provider '{job_data.embedding_provider}' not available"
                )
            
            if job_data.vector_db_provider and job_data.vector_db_provider not in available_providers['vector_db']:
                raise HTTPException(
                    status_code=400,
                    detail=f"Vector DB provider '{job_data.vector_db_provider}' not available"
                )
        
        # Update job
        job = service.update_job(job_id, job_data.dict(exclude_unset=True))
        if not job:
            raise HTTPException(status_code=404, detail="Cronjob not found")
        
        return CronJobResponse.from_orm(job)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating cronjob {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{job_id}")
async def delete_cronjob(
    job_id: str,
    service: CronJobService = Depends(get_cronjob_service)
):
    """Delete a cronjob"""
    try:
        success = service.delete_job(job_id)
        if not success:
            raise HTTPException(status_code=404, detail="Cronjob not found")
        
        return {"message": "Cronjob deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting cronjob {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{job_id}/trigger", response_model=JobTriggerResponse)
async def trigger_cronjob(
    job_id: str,
    request: JobTriggerRequest,
    background_tasks: BackgroundTasks,
    service: CronJobService = Depends(get_cronjob_service)
):
    """Manually trigger a cronjob execution"""
    try:
        # Start job execution in background
        job_run_id = service.trigger_job(job_id, background_tasks, request.force_reprocess)
        
        return JobTriggerResponse(
            job_run_id=job_run_id,
            status="started",
            message="Job execution started in background"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error triggering cronjob {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{job_id}/runs", response_model=List[JobRunResponse])
async def list_job_runs(
    job_id: str,
    skip: int = 0,
    limit: int = 50,
    status_filter: Optional[str] = None,
    session: Session = Depends(get_session)
):
    """List job runs for a specific cronjob"""
    try:
        # Verify job exists
        job = session.query(CronJob).filter(CronJob.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Cronjob not found")
        
        # Query job runs
        query = session.query(JobRun).filter(JobRun.job_id == job_id)
        
        if status_filter:
            query = query.filter(JobRun.status == status_filter)
        
        runs = query.order_by(JobRun.started_at.desc()).offset(skip).limit(limit).all()
        return [JobRunResponse.from_orm(run) for run in runs]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing job runs for {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{job_id}/status")
async def get_job_status(
    job_id: str,
    session: Session = Depends(get_session)
):
    """Get current status of a cronjob"""
    try:
        # Get job
        job = session.query(CronJob).filter(CronJob.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Cronjob not found")
        
        # Get latest job run
        latest_run = session.query(JobRun).filter(
            JobRun.job_id == job_id
        ).order_by(JobRun.started_at.desc()).first()
        
        # Get job run statistics
        total_runs = session.query(JobRun).filter(JobRun.job_id == job_id).count()
        successful_runs = session.query(JobRun).filter(
            JobRun.job_id == job_id,
            JobRun.status == 'completed'
        ).count()
        failed_runs = session.query(JobRun).filter(
            JobRun.job_id == job_id,
            JobRun.status == 'failed'
        ).count()
        
        return {
            "job_id": job_id,
            "job_name": job.name,
            "enabled": job.enabled,
            "latest_run": JobRunResponse.from_orm(latest_run) if latest_run else None,
            "statistics": {
                "total_runs": total_runs,
                "successful_runs": successful_runs,
                "failed_runs": failed_runs,
                "success_rate": (successful_runs / total_runs * 100) if total_runs > 0 else 0
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job status for {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/runs/{run_id}", response_model=JobRunResponse)
async def get_job_run(
    run_id: str,
    session: Session = Depends(get_session)
):
    """Get details of a specific job run"""
    try:
        run = session.query(JobRun).filter(JobRun.id == run_id).first()
        if not run:
            raise HTTPException(status_code=404, detail="Job run not found")
        
        return JobRunResponse.from_orm(run)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job run {run_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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