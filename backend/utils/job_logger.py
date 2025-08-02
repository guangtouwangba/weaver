"""
Job Logger - Structured logging system for job runs with database and Elasticsearch storage
"""
import logging
import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from contextlib import contextmanager
from sqlalchemy.orm import Session

from database.models import JobLog, JobStatusHistory, JobMetrics, JobRun
from core.dependencies import get_db_session
from utils.elasticsearch_logger import ElasticsearchLoggerFactory

logger = logging.getLogger(__name__)

class JobLogger:
    """Structured logger for job runs with database and Elasticsearch storage"""
    
    def __init__(self, job_run_id: str, db_session: Optional[Session] = None, 
                 es_logger: Optional['ElasticsearchLogger'] = None):
        self.job_run_id = job_run_id
        self.db_session = db_session or get_db_session()
        self.es_logger = es_logger
        self.current_step = None
        self.start_time = time.time()
        
        # Get job information for Elasticsearch
        self.job_info = self._get_job_info()
        
    def _get_job_info(self) -> Dict[str, str]:
        """Get job information for logging"""
        try:
            job_run = self.db_session.query(JobRun).filter(JobRun.id == self.job_run_id).first()
            if job_run:
                # Get job name
                from database.models import CronJob
                job = self.db_session.query(CronJob).filter(CronJob.id == job_run.job_id).first()
                return {
                    'job_id': str(job_run.job_id),
                    'job_name': job.name if job else 'Unknown'
                }
        except Exception as e:
            logger.error(f"Failed to get job info: {e}")
        
        return {'job_id': 'unknown', 'job_name': 'Unknown'}
    
    def log(self, level: str, message: str, **kwargs):
        """Log a message with structured data to both database and Elasticsearch"""
        try:
            # Create log entry for database
            log_entry = JobLog(
                job_run_id=self.job_run_id,
                level=level.upper(),
                message=message,
                details=kwargs.get('details'),
                step=self.current_step,
                paper_id=kwargs.get('paper_id'),
                error_code=kwargs.get('error_code'),
                duration_ms=kwargs.get('duration_ms'),
                logger_name=kwargs.get('logger_name', 'job_logger')
            )
            
            # Save to database
            self.db_session.add(log_entry)
            self.db_session.commit()
            
            # Log to Elasticsearch if available
            if self.es_logger:
                try:
                    self.es_logger.log_job_event(
                        job_run_id=self.job_run_id,
                        job_id=self.job_info['job_id'],
                        job_name=self.job_info['job_name'],
                        level=level,
                        message=message,
                        step=self.current_step,
                        paper_id=kwargs.get('paper_id'),
                        error_code=kwargs.get('error_code'),
                        duration_ms=kwargs.get('duration_ms'),
                        logger_name=kwargs.get('logger_name', 'job_logger'),
                        details=kwargs.get('details')
                    )
                except Exception as e:
                    logger.error(f"Failed to log to Elasticsearch: {e}")
            
            # Also log to standard logging system
            logger = logging.getLogger(kwargs.get('logger_name', 'job_logger'))
            log_method = getattr(logger, level.lower(), logger.info)
            log_method(f"[JobRun:{self.job_run_id}] {message}")
            
        except Exception as e:
            # Fallback to standard logging if database logging fails
            logger = logging.getLogger('job_logger')
            logger.error(f"Failed to log to database: {e}")
            logger.info(f"[JobRun:{self.job_run_id}] {message}")
    
    def info(self, message: str, **kwargs):
        """Log info level message"""
        self.log('INFO', message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning level message"""
        self.log('WARNING', message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error level message"""
        self.log('ERROR', message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug level message"""
        self.log('DEBUG', message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical level message"""
        self.log('CRITICAL', message, **kwargs)
    
    def set_step(self, step: str):
        """Set current execution step"""
        self.current_step = step
        self.info(f"Starting step: {step}")
    
    def record_metric(self, metric_name: str, metric_value: int, 
                     metric_type: str = 'counter', labels: Optional[Dict] = None):
        """Record a metric for the job run to both database and Elasticsearch"""
        try:
            # Save to database
            metric = JobMetrics(
                job_run_id=self.job_run_id,
                metric_name=metric_name,
                metric_value=metric_value,
                metric_type=metric_type,
                labels=labels
            )
            
            self.db_session.add(metric)
            self.db_session.commit()
            
            # Log to Elasticsearch if available
            if self.es_logger:
                try:
                    self.es_logger.log_metric(
                        job_run_id=self.job_run_id,
                        job_id=self.job_info['job_id'],
                        metric_name=metric_name,
                        metric_value=metric_value,
                        metric_type=metric_type,
                        labels=labels
                    )
                except Exception as e:
                    logger.error(f"Failed to log metric to Elasticsearch: {e}")
            
        except Exception as e:
            logger = logging.getLogger('job_logger')
            logger.error(f"Failed to record metric: {e}")
    
    def update_status(self, new_status: str, reason: Optional[str] = None, 
                     details: Optional[Dict] = None):
        """Update job run status and record in both database and Elasticsearch"""
        try:
            # Get current status
            job_run = self.db_session.query(JobRun).filter(JobRun.id == self.job_run_id).first()
            if not job_run:
                raise ValueError(f"JobRun {self.job_run_id} not found")
            
            from_status = job_run.status
            job_run.status = new_status
            
            # Record status change in database
            status_history = JobStatusHistory(
                job_run_id=self.job_run_id,
                from_status=from_status,
                to_status=new_status,
                reason=reason,
                details=details
            )
            
            self.db_session.add(status_history)
            self.db_session.commit()
            
            # Log to Elasticsearch if available
            if self.es_logger:
                try:
                    self.es_logger.log_status_change(
                        job_run_id=self.job_run_id,
                        job_id=self.job_info['job_id'],
                        from_status=from_status,
                        to_status=new_status,
                        reason=reason,
                        details=details
                    )
                except Exception as e:
                    logger.error(f"Failed to log status change to Elasticsearch: {e}")
            
            self.info(f"Status changed from {from_status} to {new_status}", 
                     details={'reason': reason, 'details': details})
            
        except Exception as e:
            logger = logging.getLogger('job_logger')
            logger.error(f"Failed to update status: {e}")
    
    @contextmanager
    def timed_step(self, step_name: str):
        """Context manager for timing execution steps"""
        start_time = time.time()
        self.set_step(step_name)
        
        try:
            yield
        finally:
            duration_ms = int((time.time() - start_time) * 1000)
            self.info(f"Completed step: {step_name}", duration_ms=duration_ms)
    
    @contextmanager
    def paper_context(self, paper_id: str):
        """Context manager for paper-specific operations"""
        original_step = self.current_step
        self.current_step = f"{original_step} - Paper: {paper_id}"
        
        try:
            yield
        finally:
            self.current_step = original_step
    
    def get_logs(self, level: Optional[str] = None, step: Optional[str] = None, 
                 limit: int = 100) -> List[JobLog]:
        """Retrieve logs for this job run from database"""
        query = self.db_session.query(JobLog).filter(JobLog.job_run_id == self.job_run_id)
        
        if level:
            query = query.filter(JobLog.level == level.upper())
        if step:
            query = query.filter(JobLog.step == step)
        
        return query.order_by(JobLog.timestamp.desc()).limit(limit).all()
    
    def get_logs_from_elasticsearch(self, level: Optional[str] = None, step: Optional[str] = None,
                                   limit: int = 100) -> List[Dict]:
        """Retrieve logs from Elasticsearch"""
        if not self.es_logger:
            return []
        
        try:
            return self.es_logger.search_logs(
                job_run_id=self.job_run_id,
                level=level,
                step=step,
                size=limit
            )
        except Exception as e:
            logger.error(f"Failed to get logs from Elasticsearch: {e}")
            return []
    
    def get_status_history(self) -> List[JobStatusHistory]:
        """Retrieve status history for this job run from database"""
        return self.db_session.query(JobStatusHistory)\
            .filter(JobStatusHistory.job_run_id == self.job_run_id)\
            .order_by(JobStatusHistory.timestamp.asc()).all()
    
    def get_metrics(self, metric_name: Optional[str] = None) -> List[JobMetrics]:
        """Retrieve metrics for this job run from database"""
        query = self.db_session.query(JobMetrics)\
            .filter(JobMetrics.job_run_id == self.job_run_id)
        
        if metric_name:
            query = query.filter(JobMetrics.metric_name == metric_name)
        
        return query.order_by(JobMetrics.timestamp.asc()).all()
    
    def get_log_statistics_from_elasticsearch(self) -> Dict:
        """Get log statistics from Elasticsearch"""
        if not self.es_logger:
            return {}
        
        try:
            return self.es_logger.get_log_statistics(job_run_id=self.job_run_id)
        except Exception as e:
            logger.error(f"Failed to get log statistics from Elasticsearch: {e}")
            return {}
    
    def close(self):
        """Close the logger and release resources"""
        if self.db_session:
            self.db_session.close()
        if self.es_logger:
            self.es_logger.close()

class JobLoggerFactory:
    """Factory for creating job loggers"""
    
    @staticmethod
    def create_logger(job_run_id: str, db_session: Optional[Session] = None,
                     es_hosts: Optional[List[str]] = None,
                     es_username: Optional[str] = None,
                     es_password: Optional[str] = None) -> JobLogger:
        """Create a new job logger instance with optional Elasticsearch integration"""
        es_logger = None
        
        # Create Elasticsearch logger if hosts are provided
        if es_hosts:
            try:
                from utils.elasticsearch_logger import ElasticsearchLoggerFactory
                es_logger = ElasticsearchLoggerFactory.create_logger(
                    hosts=es_hosts,
                    username=es_username,
                    password=es_password
                )
            except Exception as e:
                logger.warning(f"Failed to create Elasticsearch logger: {e}")
        
        return JobLogger(job_run_id, db_session, es_logger)
    
    @staticmethod
    def create_logger_for_job_run(job_run: JobRun, db_session: Optional[Session] = None,
                                 es_hosts: Optional[List[str]] = None,
                                 es_username: Optional[str] = None,
                                 es_password: Optional[str] = None) -> JobLogger:
        """Create a logger for an existing job run with optional Elasticsearch integration"""
        return JobLoggerFactory.create_logger(
            str(job_run.id), 
            db_session, 
            es_hosts, 
            es_username, 
            es_password
        ) 