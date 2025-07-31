"""
Cronjob controller for handling HTTP request/response logic.
"""
import logging
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, BackgroundTasks

from models.schemas.cronjob import (
    CronJobCreate, CronJobUpdate, CronJobResponse, 
    JobRunResponse, JobTriggerRequest, JobTriggerResponse
)
from services.cronjob_service import CronJobService
from core.exceptions import NotFoundError, ValidationError, ServiceError

logger = logging.getLogger(__name__)

class CronJobController:
    """Controller for cronjob operations"""
    
    def __init__(self, cronjob_service: CronJobService):
        self.cronjob_service = cronjob_service
    
    async def list_cronjobs(self, skip: int = 0, limit: int = 100, 
                           enabled_only: bool = False) -> List[CronJobResponse]:
        """List all cronjobs"""
        try:
            jobs = self.cronjob_service.list_jobs(skip, limit, enabled_only)
            return [self._job_to_response(job) for job in jobs]
        except Exception as e:
            logger.error(f"Error listing cronjobs: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def create_cronjob(self, job_data: CronJobCreate) -> CronJobResponse:
        """Create a new cronjob"""
        try:
            job = self.cronjob_service.create_job(job_data.model_dump())
            return self._job_to_response(job)
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except ServiceError as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_cronjob(self, job_id: str) -> CronJobResponse:
        """Get a specific cronjob"""
        try:
            job = self.cronjob_service.get_job(job_id)
            return self._job_to_response(job)
        except NotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except ServiceError as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    async def update_cronjob(self, job_id: str, job_data: CronJobUpdate) -> CronJobResponse:
        """Update a cronjob"""
        try:
            job = self.cronjob_service.update_job(job_id, job_data.model_dump(exclude_unset=True))
            return self._job_to_response(job)
        except NotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except ServiceError as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    async def delete_cronjob(self, job_id: str) -> Dict[str, str]:
        """Delete a cronjob"""
        try:
            self.cronjob_service.delete_job(job_id)
            return {"message": "Cronjob deleted successfully"}
        except NotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except ServiceError as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    async def toggle_cronjob(self, job_id: str) -> CronJobResponse:
        """Toggle cronjob enabled/disabled status"""
        try:
            job = self.cronjob_service.toggle_job(job_id)
            return self._job_to_response(job)
        except NotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except ServiceError as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    async def trigger_cronjob(self, job_id: str, request: JobTriggerRequest, 
                             background_tasks: BackgroundTasks) -> JobTriggerResponse:
        """Manually trigger a cronjob execution"""
        try:
            job_run_id = self.cronjob_service.trigger_job(
                job_id, 
                background_tasks, 
                request.force_reprocess
            )
            
            return JobTriggerResponse(
                job_run_id=job_run_id,
                status="started",
                message="Job execution started in background"
            )
        except NotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except ServiceError as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    async def list_job_runs(self, job_id: str, skip: int = 0, limit: int = 50, 
                           status_filter: Optional[str] = None) -> List[JobRunResponse]:
        """List job runs for a specific cronjob"""
        try:
            runs = self.cronjob_service.get_job_runs(job_id, skip, limit, status_filter)
            result = []
            for run in runs:
                run_dict = {
                    'id': str(run.id),
                    'job_id': str(run.job_id),
                    'task_id': run.task_id,
                    'status': run.status,
                    'started_at': run.started_at,
                    'completed_at': run.completed_at,
                    'progress_percentage': run.progress_percentage,
                    'current_step': run.current_step,
                    'manual_trigger': run.manual_trigger,
                    'user_params': run.user_params,
                    'papers_found': run.papers_found,
                    'papers_processed': run.papers_processed,
                    'papers_skipped': run.papers_skipped,
                    'papers_embedded': run.papers_embedded,
                    'embedding_errors': run.embedding_errors,
                    'vector_db_errors': run.vector_db_errors,
                    'error_message': run.error_message,
                    'execution_log': run.execution_log
                }
                result.append(JobRunResponse.model_validate(run_dict))
            return result
        except NotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except ServiceError as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get current status of a cronjob"""
        try:
            status = self.cronjob_service.get_job_status(job_id)
            # Convert JobRun to response format if present
            if status.get('latest_run'):
                latest_run = status['latest_run']
                logger.debug(f"Latest run object: {latest_run}")
                logger.debug(f"Latest run id type: {type(latest_run.id)}")
                logger.debug(f"Latest run job_id type: {type(latest_run.job_id)}")
                
                # Convert UUID fields to strings before validation
                latest_run_dict = {
                    'id': str(latest_run.id),
                    'job_id': str(latest_run.job_id),
                    'task_id': latest_run.task_id,
                    'status': latest_run.status,
                    'started_at': latest_run.started_at,
                    'completed_at': latest_run.completed_at,
                    'progress_percentage': latest_run.progress_percentage,
                    'current_step': latest_run.current_step,
                    'manual_trigger': latest_run.manual_trigger,
                    'user_params': latest_run.user_params,
                    'papers_found': latest_run.papers_found,
                    'papers_processed': latest_run.papers_processed,
                    'papers_skipped': latest_run.papers_skipped,
                    'papers_embedded': latest_run.papers_embedded,
                    'embedding_errors': latest_run.embedding_errors,
                    'vector_db_errors': latest_run.vector_db_errors,
                    'error_message': latest_run.error_message,
                    'execution_log': latest_run.execution_log
                }
                logger.debug(f"Latest run dict: {latest_run_dict}")
                status['latest_run'] = JobRunResponse.model_validate(latest_run_dict)
            return status
        except NotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except ServiceError as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_job_run(self, run_id: str) -> JobRunResponse:
        """Get details of a specific job run"""
        try:
            run = self.cronjob_service.get_job_run(run_id)
            run_dict = {
                'id': str(run.id),
                'job_id': str(run.job_id),
                'task_id': run.task_id,
                'status': run.status,
                'started_at': run.started_at,
                'completed_at': run.completed_at,
                'progress_percentage': run.progress_percentage,
                'current_step': run.current_step,
                'manual_trigger': run.manual_trigger,
                'user_params': run.user_params,
                'papers_found': run.papers_found,
                'papers_processed': run.papers_processed,
                'papers_skipped': run.papers_skipped,
                'papers_embedded': run.papers_embedded,
                'embedding_errors': run.embedding_errors,
                'vector_db_errors': run.vector_db_errors,
                'error_message': run.error_message,
                'execution_log': run.execution_log
            }
            return JobRunResponse.model_validate(run_dict)
        except NotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except ServiceError as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    def _job_to_response(self, job) -> CronJobResponse:
        """Convert job model to response schema"""
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
    
    # History-related methods
    async def list_all_job_runs(
        self, 
        skip: int = 0, 
        limit: int = 100,
        status_filter: Optional[str] = None,
        job_id_filter: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[JobRunResponse]:
        """List job runs across all cronjobs with filtering"""
        try:
            runs = self.cronjob_service.get_all_job_runs(
                skip, limit, status_filter, job_id_filter, start_date, end_date
            )
            result = []
            for run in runs:
                run_dict = {
                    'id': str(run.id),
                    'job_id': str(run.job_id),
                    'task_id': run.task_id,
                    'status': run.status,
                    'started_at': run.started_at,
                    'completed_at': run.completed_at,
                    'progress_percentage': run.progress_percentage,
                    'current_step': run.current_step,
                    'manual_trigger': run.manual_trigger,
                    'user_params': run.user_params,
                    'papers_found': run.papers_found,
                    'papers_processed': run.papers_processed,
                    'papers_skipped': run.papers_skipped,
                    'papers_embedded': run.papers_embedded,
                    'embedding_errors': run.embedding_errors,
                    'vector_db_errors': run.vector_db_errors,
                    'error_message': run.error_message,
                    'execution_log': run.execution_log
                }
                result.append(JobRunResponse.model_validate(run_dict))
            return result
        except ServiceError as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_history_stats(self, days: int = 30) -> Dict[str, Any]:
        """Get historical statistics and trends"""
        try:
            return self.cronjob_service.get_history_statistics(days)
        except ServiceError as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    async def export_history(
        self,
        format: str = "csv",
        status_filter: Optional[str] = None,
        job_id_filter: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ):
        """Export job run history in various formats"""
        try:
            return self.cronjob_service.export_job_run_history(
                format, status_filter, job_id_filter, start_date, end_date
            )
        except ServiceError as e:
            raise HTTPException(status_code=500, detail=str(e))
    
