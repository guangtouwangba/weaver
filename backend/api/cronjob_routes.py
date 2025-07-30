"""
FastAPI routes for cronjob management with vector DB and embedding support
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field, validator, model_validator
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
    
    @model_validator(mode='after')
    def validate_schedule(self):
        cron_expr = self.cron_expression
        interval_hours = self.interval_hours
        
        # Convert empty strings to None
        if cron_expr == "":
            cron_expr = None
        if interval_hours == "":
            interval_hours = None
        
        if not cron_expr and not interval_hours:
            raise ValueError('Either cron_expression or interval_hours must be provided')
        if cron_expr and interval_hours:
            raise ValueError('Only one of cron_expression or interval_hours should be provided')
        
        return self

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
    
    @model_validator(mode='before')
    @classmethod
    def validate_to_json(cls, data):
        # Convert UUID to string if needed
        if isinstance(data, dict) and 'id' in data:
            if hasattr(data['id'], 'hex'):
                data['id'] = str(data['id'])
        elif hasattr(data, 'id') and hasattr(data.id, 'hex'):
            data.id = str(data.id)
        return data
    
    @model_validator(mode='after')
    def validate_id_string(self):
        # Ensure id is a string
        if hasattr(self.id, 'hex'):
            self.id = str(self.id)
        return self

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
    
    @model_validator(mode='before')
    @classmethod
    def validate_to_json(cls, data):
        # Convert UUID to string if needed
        if isinstance(data, dict) and 'job_run_id' in data:
            if hasattr(data['job_run_id'], 'hex'):
                data['job_run_id'] = str(data['job_run_id'])
        elif hasattr(data, 'job_run_id') and hasattr(data.job_run_id, 'hex'):
            data.job_run_id = str(data.job_run_id)
        return data

# Dependency for getting cronjob service
def get_cronjob_service():
    from database.database import get_database
    db = get_database()
    return CronJobService, db

# Routes
@router.get("/", response_model=List[CronJobResponse])
async def list_cronjobs(
    skip: int = 0,
    limit: int = 100,
    enabled_only: bool = False
):
    """List all cronjobs"""
    try:
        from database.database import get_database
        db = get_database()
        
        with db.get_session() as session:
            query = session.query(CronJob)
            
            if enabled_only:
                query = query.filter(CronJob.enabled == True)
            
            jobs = query.offset(skip).limit(limit).all()
            return [
                CronJobResponse(
                    id=str(job.id),
                    name=job.name,
                    keywords=job.keywords,
                    cron_expression=job.cron_expression,
                    interval_hours=job.interval_hours,
                    enabled=job.enabled,
                    max_papers_per_run=job.max_papers_per_run,
                    embedding_provider=job.embedding_provider,
                    embedding_model=job.embedding_model,
                    vector_db_provider=job.vector_db_provider,
                    vector_db_config=job.vector_db_config,
                    created_at=job.created_at,
                    updated_at=job.updated_at
                ) for job in jobs
            ]
        
    except Exception as e:
        logger.error(f"Error listing cronjobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=CronJobResponse, status_code=201)
async def create_cronjob(job_data: CronJobCreate):
    """Create a new cronjob"""
    try:
        from database.database import get_database
        db = get_database()
        
        with db.get_session() as session:
            service = CronJobService(session)
            
            # Check if a job with the same name already exists
            existing_job = session.query(CronJob).filter(CronJob.name == job_data.name).first()
            if existing_job:
                raise HTTPException(
                    status_code=409,
                    detail=f"A cronjob with name '{job_data.name}' already exists"
                )
            
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
            job = service.create_job(job_data.model_dump())
            return CronJobResponse(
                id=str(job.id),
                name=job.name,
                keywords=job.keywords,
                cron_expression=job.cron_expression,
                interval_hours=job.interval_hours,
                enabled=job.enabled,
                max_papers_per_run=job.max_papers_per_run,
                embedding_provider=job.embedding_provider,
                embedding_model=job.embedding_model,
                vector_db_provider=job.vector_db_provider,
                vector_db_config=job.vector_db_config,
                created_at=job.created_at,
                updated_at=job.updated_at
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating cronjob: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{job_id}", response_model=CronJobResponse)
async def get_cronjob(job_id: str):
    """Get a specific cronjob"""
    try:
        from database.database import get_database
        db = get_database()
        
        with db.get_session() as session:
            job = session.query(CronJob).filter(CronJob.id == job_id).first()
            if not job:
                raise HTTPException(status_code=404, detail="Cronjob not found")
            
            return CronJobResponse(
                id=str(job.id),
                name=job.name,
                keywords=job.keywords,
                cron_expression=job.cron_expression,
                interval_hours=job.interval_hours,
                enabled=job.enabled,
                max_papers_per_run=job.max_papers_per_run,
                embedding_provider=job.embedding_provider,
                embedding_model=job.embedding_model,
                vector_db_provider=job.vector_db_provider,
                vector_db_config=job.vector_db_config,
                created_at=job.created_at,
                updated_at=job.updated_at
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting cronjob {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{job_id}", response_model=CronJobResponse)
async def update_cronjob(job_id: str, job_data: CronJobUpdate):
    """Update a cronjob"""
    try:
        from database.database import get_database
        db = get_database()
        
        with db.get_session() as session:
            service = CronJobService(session)
            
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
            job = service.update_job(job_id, job_data.model_dump(exclude_unset=True))
            if not job:
                raise HTTPException(status_code=404, detail="Cronjob not found")
            
            return CronJobResponse(
                id=str(job.id),
                name=job.name,
                keywords=job.keywords,
                cron_expression=job.cron_expression,
                interval_hours=job.interval_hours,
                enabled=job.enabled,
                max_papers_per_run=job.max_papers_per_run,
                embedding_provider=job.embedding_provider,
                embedding_model=job.embedding_model,
                vector_db_provider=job.vector_db_provider,
                vector_db_config=job.vector_db_config,
                created_at=job.created_at,
                updated_at=job.updated_at
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating cronjob {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{job_id}")
async def delete_cronjob(job_id: str):
    """Delete a cronjob"""
    try:
        from database.database import get_database
        db = get_database()
        
        with db.get_session() as session:
            service = CronJobService(session)
            success = service.delete_job(job_id)
            if not success:
                raise HTTPException(status_code=404, detail="Cronjob not found")
            
            return {"message": "Cronjob deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting cronjob {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{job_id}/toggle", response_model=CronJobResponse)
async def toggle_cronjob(job_id: str):
    """Toggle cronjob enabled/disabled status"""
    try:
        from database.database import get_database
        db = get_database()
        
        with db.get_session() as session:
            # Check if job exists
            job = session.query(CronJob).filter(CronJob.id == job_id).first()
            if not job:
                raise HTTPException(status_code=404, detail="Cronjob not found")
            
            # Toggle enabled status
            job.enabled = not job.enabled
            session.commit()
            session.refresh(job)
            
            # Convert to response format
            return CronJobResponse.model_validate(job)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling cronjob {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{job_id}/trigger")
async def trigger_cronjob(
    job_id: str,
    request: JobTriggerRequest,
    background_tasks: BackgroundTasks
):
    """Manually trigger a cronjob execution"""
    try:
        from database.database import get_database
        db = get_database()
        
        with db.get_session() as session:
            service = CronJobService(session)
            # Start job execution in background
            job_run_id = service.trigger_job(job_id, background_tasks, request.force_reprocess)
            
            from fastapi.responses import JSONResponse
            return JSONResponse(
                content={
                    "job_run_id": str(job_run_id),
                    "status": "started",
                    "message": "Job execution started in background"
                }
            )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error triggering cronjob {job_id}: {e}")
        # Return a simple dict instead of raising exception
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }

@router.get("/{job_id}/runs", response_model=List[JobRunResponse])
async def list_job_runs(
    job_id: str,
    skip: int = 0,
    limit: int = 50,
    status_filter: Optional[str] = None
):
    """List job runs for a specific cronjob"""
    try:
        from database.database import get_database
        db = get_database()
        
        with db.get_session() as session:
            # Verify job exists
            job = session.query(CronJob).filter(CronJob.id == job_id).first()
            if not job:
                raise HTTPException(status_code=404, detail="Cronjob not found")
            
            # Query job runs
            query = session.query(JobRun).filter(JobRun.job_id == job_id)
            
            if status_filter:
                query = query.filter(JobRun.status == status_filter)
            
            runs = query.order_by(JobRun.started_at.desc()).offset(skip).limit(limit).all()
            return [JobRunResponse.model_validate(run) for run in runs]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing job runs for {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{job_id}/status")
async def get_job_status(job_id: str):
    """Get current status of a cronjob"""
    try:
        from database.database import get_database
        db = get_database()
        
        with db.get_session() as session:
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
                "latest_run": JobRunResponse.model_validate(latest_run) if latest_run else None,
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
async def get_job_run(run_id: str):
    """Get details of a specific job run"""
    try:
        from database.database import get_database
        db = get_database()
        
        with db.get_session() as session:
            run = session.query(JobRun).filter(JobRun.id == run_id).first()
            if not run:
                raise HTTPException(status_code=404, detail="Job run not found")
            
            return JobRunResponse.model_validate(run)
        
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