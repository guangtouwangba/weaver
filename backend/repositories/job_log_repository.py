"""
Job Log Repository - Data access layer for job logs and metrics
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc

from database.models import JobLog, JobStatusHistory, JobMetrics, JobRun
from repositories.base import BaseRepository

logger = logging.getLogger(__name__)

class JobLogRepository(BaseRepository[JobLog]):
    """Repository for job log operations"""
    
    def __init__(self, db_session: Session):
        super().__init__(db_session, JobLog)
        self.db_session = db_session
    
    def get_model_class(self):
        """Get the model class for this repository"""
        return JobLog
    
    def create_log(self, job_run_id: str, level: str, message: str, **kwargs) -> JobLog:
        """Create a new log entry"""
        try:
            log_entry = JobLog(
                job_run_id=job_run_id,
                level=level.upper(),
                message=message,
                details=kwargs.get('details'),
                step=kwargs.get('step'),
                paper_id=kwargs.get('paper_id'),
                error_code=kwargs.get('error_code'),
                duration_ms=kwargs.get('duration_ms'),
                logger_name=kwargs.get('logger_name', 'job_logger')
            )
            
            self.db_session.add(log_entry)
            self.db_session.commit()
            return log_entry
            
        except Exception as e:
            logger.error(f"Error creating log entry: {e}")
            self.db_session.rollback()
            raise
    
    def get_logs_by_job_run(self, job_run_id: str, 
                           level: Optional[str] = None,
                           step: Optional[str] = None,
                           limit: int = 100,
                           offset: int = 0) -> List[JobLog]:
        """Get logs for a specific job run"""
        try:
            query = self.db_session.query(JobLog).filter(JobLog.job_run_id == job_run_id)
            
            if level:
                query = query.filter(JobLog.level == level.upper())
            if step:
                query = query.filter(JobLog.step == step)
            
            return query.order_by(desc(JobLog.timestamp)).offset(offset).limit(limit).all()
            
        except Exception as e:
            logger.error(f"Error getting logs for job run {job_run_id}: {e}")
            return []
    
    def get_logs_by_job(self, job_id: str,
                        level: Optional[str] = None,
                        step: Optional[str] = None,
                        start_date: Optional[datetime] = None,
                        end_date: Optional[datetime] = None,
                        limit: int = 100,
                        offset: int = 0) -> List[JobLog]:
        """Get logs for all runs of a specific job"""
        try:
            # Join with job_runs to filter by job_id
            query = self.db_session.query(JobLog).join(JobRun).filter(JobRun.job_id == job_id)
            
            if level:
                query = query.filter(JobLog.level == level.upper())
            if step:
                query = query.filter(JobLog.step == step)
            if start_date:
                query = query.filter(JobLog.timestamp >= start_date)
            if end_date:
                query = query.filter(JobLog.timestamp <= end_date)
            
            return query.order_by(desc(JobLog.timestamp)).offset(offset).limit(limit).all()
            
        except Exception as e:
            logger.error(f"Error getting logs for job {job_id}: {e}")
            return []
    
    def get_error_logs(self, job_run_id: Optional[str] = None,
                      job_id: Optional[str] = None,
                      days: int = 7) -> List[JobLog]:
        """Get error logs for recent runs"""
        try:
            start_date = datetime.now() - timedelta(days=days)
            query = self.db_session.query(JobLog).filter(
                and_(
                    JobLog.level.in_(['ERROR', 'CRITICAL']),
                    JobLog.timestamp >= start_date
                )
            )
            
            if job_run_id:
                query = query.filter(JobLog.job_run_id == job_run_id)
            elif job_id:
                query = query.join(JobRun).filter(JobRun.job_id == job_id)
            
            return query.order_by(desc(JobLog.timestamp)).all()
            
        except Exception as e:
            logger.error(f"Error getting error logs: {e}")
            return []
    
    def get_log_statistics(self, job_run_id: Optional[str] = None,
                          job_id: Optional[str] = None,
                          days: int = 30) -> Dict[str, Any]:
        """Get log statistics"""
        try:
            start_date = datetime.now() - timedelta(days=days)
            query = self.db_session.query(JobLog).filter(JobLog.timestamp >= start_date)
            
            if job_run_id:
                query = query.filter(JobLog.job_run_id == job_run_id)
            elif job_id:
                query = query.join(JobRun).filter(JobRun.job_id == job_id)
            
            # Get level counts
            level_counts = {}
            for level in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
                count = query.filter(JobLog.level == level).count()
                level_counts[level] = count
            
            # Get step counts
            step_counts = {}
            steps = query.with_entities(JobLog.step).distinct().all()
            for step, in steps:
                if step:
                    count = query.filter(JobLog.step == step).count()
                    step_counts[step] = count
            
            return {
                'total_logs': query.count(),
                'level_counts': level_counts,
                'step_counts': step_counts,
                'period_days': days
            }
            
        except Exception as e:
            logger.error(f"Error getting log statistics: {e}")
            return {}

class JobStatusHistoryRepository(BaseRepository[JobStatusHistory]):
    """Repository for job status history operations"""
    
    def __init__(self, db_session: Session):
        super().__init__(db_session, JobStatusHistory)
        self.db_session = db_session
    
    def get_model_class(self):
        """Get the model class for this repository"""
        return JobStatusHistory
    
    def create_status_history(self, job_run_id: str, to_status: str,
                            from_status: Optional[str] = None,
                            reason: Optional[str] = None,
                            details: Optional[Dict] = None) -> JobStatusHistory:
        """Create a new status history entry"""
        try:
            status_history = JobStatusHistory(
                job_run_id=job_run_id,
                from_status=from_status,
                to_status=to_status,
                reason=reason,
                details=details
            )
            
            self.db_session.add(status_history)
            self.db_session.commit()
            return status_history
            
        except Exception as e:
            logger.error(f"Error creating status history: {e}")
            self.db_session.rollback()
            raise
    
    def get_status_history(self, job_run_id: str) -> List[JobStatusHistory]:
        """Get status history for a job run"""
        try:
            return self.db_session.query(JobStatusHistory)\
                .filter(JobStatusHistory.job_run_id == job_run_id)\
                .order_by(asc(JobStatusHistory.timestamp)).all()
                
        except Exception as e:
            logger.error(f"Error getting status history for job run {job_run_id}: {e}")
            return []
    
    def get_latest_status(self, job_run_id: str) -> Optional[JobStatusHistory]:
        """Get the latest status for a job run"""
        try:
            return self.db_session.query(JobStatusHistory)\
                .filter(JobStatusHistory.job_run_id == job_run_id)\
                .order_by(desc(JobStatusHistory.timestamp)).first()
                
        except Exception as e:
            logger.error(f"Error getting latest status for job run {job_run_id}: {e}")
            return None

class JobMetricsRepository(BaseRepository[JobMetrics]):
    """Repository for job metrics operations"""
    
    def __init__(self, db_session: Session):
        super().__init__(db_session, JobMetrics)
        self.db_session = db_session
    
    def get_model_class(self):
        """Get the model class for this repository"""
        return JobMetrics
    
    def create_metric(self, job_run_id: str, metric_name: str, metric_value: int,
                     metric_type: str = 'counter', labels: Optional[Dict] = None) -> JobMetrics:
        """Create a new metric entry"""
        try:
            metric = JobMetrics(
                job_run_id=job_run_id,
                metric_name=metric_name,
                metric_value=metric_value,
                metric_type=metric_type,
                labels=labels
            )
            
            self.db_session.add(metric)
            self.db_session.commit()
            return metric
            
        except Exception as e:
            logger.error(f"Error creating metric: {e}")
            self.db_session.rollback()
            raise
    
    def get_metrics(self, job_run_id: str,
                   metric_name: Optional[str] = None,
                   metric_type: Optional[str] = None) -> List[JobMetrics]:
        """Get metrics for a job run"""
        try:
            query = self.db_session.query(JobMetrics).filter(JobMetrics.job_run_id == job_run_id)
            
            if metric_name:
                query = query.filter(JobMetrics.metric_name == metric_name)
            if metric_type:
                query = query.filter(JobMetrics.metric_type == metric_type)
            
            return query.order_by(asc(JobMetrics.timestamp)).all()
            
        except Exception as e:
            logger.error(f"Error getting metrics for job run {job_run_id}: {e}")
            return []
    
    def get_metric_summary(self, job_run_id: str) -> Dict[str, Any]:
        """Get metric summary for a job run"""
        try:
            metrics = self.get_metrics(job_run_id)
            summary = {}
            
            for metric in metrics:
                if metric.metric_name not in summary:
                    summary[metric.metric_name] = {
                        'total': 0,
                        'latest': 0,
                        'type': metric.metric_type
                    }
                
                summary[metric.metric_name]['total'] += metric.metric_value
                summary[metric.metric_name]['latest'] = metric.metric_value
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting metric summary for job run {job_run_id}: {e}")
            return {}
    
    def get_metrics_by_job(self, job_id: str,
                          metric_name: Optional[str] = None,
                          days: int = 30) -> List[JobMetrics]:
        """Get metrics for all runs of a specific job"""
        try:
            start_date = datetime.now() - timedelta(days=days)
            query = self.db_session.query(JobMetrics).join(JobRun).filter(
                and_(
                    JobRun.job_id == job_id,
                    JobMetrics.timestamp >= start_date
                )
            )
            
            if metric_name:
                query = query.filter(JobMetrics.metric_name == metric_name)
            
            return query.order_by(desc(JobMetrics.timestamp)).all()
            
        except Exception as e:
            logger.error(f"Error getting metrics for job {job_id}: {e}")
            return [] 