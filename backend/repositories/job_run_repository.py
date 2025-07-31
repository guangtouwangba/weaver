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
    
    # History-related methods
    def get_all_runs(self, skip: int = 0, limit: int = 100,
                     status_filter: Optional[str] = None,
                     job_id_filter: Optional[str] = None,
                     start_date: Optional[datetime] = None,
                     end_date: Optional[datetime] = None) -> List[JobRun]:
        """Get all job runs with filtering options"""
        query = self.session.query(JobRun)
        
        if status_filter:
            query = query.filter(JobRun.status == status_filter)
        
        if job_id_filter:
            query = query.filter(JobRun.job_id == job_id_filter)
        
        if start_date:
            query = query.filter(JobRun.started_at >= start_date)
        
        if end_date:
            query = query.filter(JobRun.started_at <= end_date)
        
        return query.order_by(desc(JobRun.started_at)).offset(skip).limit(limit).all()
    
    def get_runs_count(self, status_filter: Optional[str] = None,
                       job_id_filter: Optional[str] = None,
                       start_date: Optional[datetime] = None,
                       end_date: Optional[datetime] = None) -> int:
        """Get count of job runs with filtering"""
        query = self.session.query(JobRun)
        
        if status_filter:
            query = query.filter(JobRun.status == status_filter)
        
        if job_id_filter:
            query = query.filter(JobRun.job_id == job_id_filter)
        
        if start_date:
            query = query.filter(JobRun.started_at >= start_date)
        
        if end_date:
            query = query.filter(JobRun.started_at <= end_date)
        
        return query.count()
    
    def get_global_statistics(self, days: Optional[int] = None) -> dict:
        """Get global statistics across all jobs"""
        from datetime import timedelta
        
        query = self.session.query(JobRun)
        
        if days:
            start_date = datetime.utcnow() - timedelta(days=days)
            query = query.filter(JobRun.started_at >= start_date)
        
        # Basic counts
        total_runs = query.count()
        successful_runs = query.filter(JobRun.status == 'completed').count()
        failed_runs = query.filter(JobRun.status == 'failed').count()
        running_runs = query.filter(JobRun.status == 'running').count()
        cancelled_runs = query.filter(JobRun.status == 'cancelled').count()
        
        # Paper statistics - removed unused paper_stats
        
        # Calculate aggregates
        total_papers_found = sum(run.papers_found or 0 for run in query.all())
        total_papers_processed = sum(run.papers_processed or 0 for run in query.all())
        total_papers_embedded = sum(run.papers_embedded or 0 for run in query.all())
        total_embedding_errors = sum(run.embedding_errors or 0 for run in query.all())
        total_vector_errors = sum(run.vector_db_errors or 0 for run in query.all())
        
        return {
            "period_days": days,
            "total_runs": total_runs,
            "successful_runs": successful_runs,
            "failed_runs": failed_runs,
            "running_runs": running_runs,
            "cancelled_runs": cancelled_runs,
            "success_rate": (successful_runs / total_runs * 100) if total_runs > 0 else 0,
            "paper_statistics": {
                "total_found": total_papers_found,
                "total_processed": total_papers_processed,
                "total_embedded": total_papers_embedded,
                "processing_rate": (total_papers_processed / total_papers_found * 100) if total_papers_found > 0 else 0,
                "embedding_rate": (total_papers_embedded / total_papers_processed * 100) if total_papers_processed > 0 else 0,
                "total_embedding_errors": total_embedding_errors,
                "total_vector_errors": total_vector_errors
            }
        }
    
    def get_daily_stats(self, days: int = 30) -> List[dict]:
        """Get daily statistics for trend analysis"""
        from datetime import timedelta
        from sqlalchemy import func, cast, Date
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get all runs within the date range
        runs = self.session.query(JobRun).filter(
            JobRun.started_at >= start_date
        ).all()
        
        # Group by date manually in Python
        daily_data = {}
        for run in runs:
            date_key = run.started_at.date().isoformat()
            if date_key not in daily_data:
                daily_data[date_key] = {
                    "date": date_key,
                    "total_runs": 0,
                    "successful_runs": 0,
                    "failed_runs": 0,
                    "papers_found": 0,
                    "papers_processed": 0
                }
            
            daily_data[date_key]["total_runs"] += 1
            if run.status == 'completed':
                daily_data[date_key]["successful_runs"] += 1
            elif run.status == 'failed':
                daily_data[date_key]["failed_runs"] += 1
            
            if run.papers_found:
                daily_data[date_key]["papers_found"] += run.papers_found
            if run.papers_processed:
                daily_data[date_key]["papers_processed"] += run.papers_processed
        
        # Calculate success rates and return sorted by date
        result = []
        for date_key in sorted(daily_data.keys()):
            stats = daily_data[date_key]
            stats["success_rate"] = (stats["successful_runs"] / stats["total_runs"] * 100) if stats["total_runs"] > 0 else 0
            result.append(stats)
        
        return result