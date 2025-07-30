"""
Repository for job run database operations.
"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc
from database.models import JobRun
from .base import BaseRepository

class JobRunRepository(BaseRepository[JobRun]):
    """Repository for job run operations"""
    
    def __init__(self, session: Session):
        super().__init__(session, JobRun)
    
    def get_model_class(self):
        return JobRun
    
    def get_runs_by_job_id(self, job_id: str, skip: int = 0, 
                          limit: int = 50, status_filter: Optional[str] = None) -> List[JobRun]:
        """Get job runs for a specific cronjob"""
        query = self.session.query(JobRun).filter(JobRun.job_id == job_id)
        
        if status_filter:
            query = query.filter(JobRun.status == status_filter)
        
        return query.order_by(desc(JobRun.started_at)).offset(skip).limit(limit).all()
    
    def get_latest_run_by_job_id(self, job_id: str) -> Optional[JobRun]:
        """Get the latest job run for a specific cronjob"""
        return self.session.query(JobRun).filter(
            JobRun.job_id == job_id
        ).order_by(desc(JobRun.started_at)).first()
    
    def get_runs_by_status(self, status: str, skip: int = 0, limit: int = 100) -> List[JobRun]:
        """Get job runs by status"""
        return self.session.query(JobRun).filter(
            JobRun.status == status
        ).order_by(desc(JobRun.started_at)).offset(skip).limit(limit).all()
    
    def get_running_jobs_count(self) -> int:
        """Get count of currently running jobs"""
        return self.session.query(JobRun).filter(JobRun.status == 'running').count()
    
    def get_job_statistics(self, job_id: str) -> dict:
        """Get statistics for a specific job"""
        total_runs = self.session.query(JobRun).filter(JobRun.job_id == job_id).count()
        successful_runs = self.session.query(JobRun).filter(
            JobRun.job_id == job_id,
            JobRun.status == 'completed'
        ).count()
        failed_runs = self.session.query(JobRun).filter(
            JobRun.job_id == job_id,
            JobRun.status == 'failed'
        ).count()
        
        return {
            "total_runs": total_runs,
            "successful_runs": successful_runs,
            "failed_runs": failed_runs,
            "success_rate": (successful_runs / total_runs * 100) if total_runs > 0 else 0
        }
    
    def update_run_status(self, run_id: str, status: str, 
                         completed_at: Optional[datetime] = None,
                         error_message: Optional[str] = None) -> Optional[JobRun]:
        """Update job run status"""
        run = self.get_by_id(run_id)
        if not run:
            return None
        
        run.status = status
        if completed_at:
            run.completed_at = completed_at
        if error_message:
            run.error_message = error_message
        
        self.session.commit()
        self.session.refresh(run)
        return run
    
    def get_by_task_id(self, task_id: str) -> Optional[JobRun]:
        """Get job run by Celery task ID"""
        return self.session.query(JobRun).filter(JobRun.task_id == task_id).first()
    
    def update_progress(self, run_id: str, progress: int, current_step: str, 
                       metadata: Optional[dict] = None) -> Optional[JobRun]:
        """Update job run progress"""
        run = self.get_by_id(run_id)
        if not run:
            return None
        
        run.progress_percentage = progress
        run.current_step = current_step
        
        if metadata:
            # Merge with existing execution_log
            if run.execution_log:
                run.execution_log.update(metadata)
            else:
                run.execution_log = metadata
        
        self.session.commit()
        self.session.refresh(run)
        return run
    
    def complete_job_run(self, run_id: str, status: str, **kwargs) -> Optional[JobRun]:
        """Complete a job run with final results"""
        run = self.get_by_id(run_id)
        if not run:
            return None
        
        run.status = status
        run.completed_at = datetime.utcnow()
        run.progress_percentage = 100 if status == 'completed' else run.progress_percentage
        
        # Update metrics
        for key, value in kwargs.items():
            if hasattr(run, key):
                setattr(run, key, value)
        
        self.session.commit()
        self.session.refresh(run)
        return run
    
    def cleanup_old_runs(self, days: int = 30) -> dict:
        """Cleanup job runs older than specified days"""
        from datetime import timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Count records to be deleted
        old_runs = self.session.query(JobRun).filter(
            JobRun.started_at < cutoff_date,
            JobRun.status.in_(['completed', 'failed', 'cancelled'])
        )
        
        count = old_runs.count()
        
        # Delete old runs
        old_runs.delete(synchronize_session=False)
        self.session.commit()
        
        return {
            'deleted_runs': count,
            'cutoff_date': cutoff_date.isoformat()
        }