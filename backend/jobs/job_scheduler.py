#!/usr/bin/env python3
"""
Database-driven Job Scheduler
Persistent job scheduling system that survives service restarts
"""

import os
import sys
import logging
import threading
import time
import signal
import traceback
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta
import uuid

# Add backend path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database.database_adapter import DatabaseManager
from database.job_models import Job, JobExecution, JobStatus, JobType, ExecutionStatus
from jobs.job_manager import JobManager

logger = logging.getLogger(__name__)

class JobExecutor:
    """Handles execution of individual jobs"""
    
    def __init__(self, job_manager: JobManager):
        self.job_manager = job_manager
        self.job_handlers: Dict[str, Callable] = {}
        self.register_default_handlers()
    
    def register_default_handlers(self):
        """Register default job handlers"""
        self.job_handlers['paper_fetch'] = self._handle_paper_fetch
        self.job_handlers['maintenance'] = self._handle_maintenance
        self.job_handlers['custom'] = self._handle_custom
    
    def register_handler(self, job_type: str, handler: Callable):
        """Register a custom job handler"""
        self.job_handlers[job_type] = handler
        logger.info(f"Registered handler for job type: {job_type}")
    
    def execute_job(self, job: Job) -> JobExecution:
        """Execute a job and return the execution record"""
        execution = JobExecution(job_id=job.job_id)
        
        try:
            # Create execution record
            self.job_manager.create_execution(execution)
            
            # Mark as started
            execution.mark_started()
            self.job_manager.update_execution(execution)
            
            logger.info(f"Starting job execution: {job.name} ({execution.execution_id})")
            
            # Get handler for job type
            handler = self.job_handlers.get(job.job_type.value if isinstance(job.job_type, JobType) else job.job_type)
            if not handler:
                raise ValueError(f"No handler registered for job type: {job.job_type}")
            
            # Execute the job with timeout
            result = self._execute_with_timeout(handler, job, job.timeout_seconds)
            
            # Mark as completed
            execution.mark_completed(result)
            self.job_manager.update_execution(execution)
            
            # Update job's last execution time
            self.job_manager.update_job_last_execution(job.job_id, execution.started_at)
            
            logger.info(f"Job completed successfully: {job.name} ({execution.execution_id})")
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Job failed: {job.name} ({execution.execution_id}) - {error_msg}")
            
            # Mark as failed
            execution.mark_failed(error_msg)
            self.job_manager.update_execution(execution)
            
            # Handle retries
            if execution.retry_attempt < job.retry_count:
                self._schedule_retry(job, execution)
        
        return execution
    
    def _execute_with_timeout(self, handler: Callable, job: Job, timeout_seconds: int) -> Dict[str, Any]:
        """Execute handler with timeout"""
        result = {}
        exception = None
        
        def target():
            nonlocal result, exception
            try:
                result = handler(job)
            except Exception as e:
                exception = e
        
        thread = threading.Thread(target=target)
        thread.daemon = True
        thread.start()
        thread.join(timeout_seconds)
        
        if thread.is_alive():
            # Timeout occurred
            raise TimeoutError(f"Job execution timed out after {timeout_seconds} seconds")
        
        if exception:
            raise exception
        
        return result
    
    def _schedule_retry(self, job: Job, failed_execution: JobExecution):
        """Schedule a retry for a failed job"""
        try:
            retry_execution = JobExecution(
                job_id=job.job_id,
                retry_attempt=failed_execution.retry_attempt + 1
            )
            
            # Schedule retry after delay
            retry_time = datetime.utcnow() + timedelta(seconds=job.retry_delay_seconds)
            
            # Update job's next execution time for retry
            job.next_execution = retry_time
            self.job_manager.update_job(job)
            
            logger.info(f"Scheduled retry {retry_execution.retry_attempt}/{job.retry_count} for job {job.name} at {retry_time}")
            
        except Exception as e:
            logger.error(f"Failed to schedule retry for job {job.job_id}: {e}")
    
    # Default job handlers
    
    def _handle_paper_fetch(self, job: Job) -> Dict[str, Any]:
        """Handle paper fetching job"""
        try:
            # Import here to avoid circular imports
            from simple_paper_fetcher import SimplePaperFetcher
            
            # Get configuration from job config
            config_path = job.config.get('config_path', 'config.yaml')
            
            # Create fetcher and run
            fetcher = SimplePaperFetcher(config_path)
            result = fetcher.run_once()
            
            return {
                'success': result.get('success', False),
                'new_papers': result.get('new_papers', 0),
                'duration_seconds': result.get('duration_seconds', 0),
                'statistics': result.get('statistics', {}),
                'error': result.get('error')
            }
            
        except Exception as e:
            logger.error(f"Paper fetch job failed: {e}")
            raise
    
    def _handle_maintenance(self, job: Job) -> Dict[str, Any]:
        """Handle maintenance job"""
        try:
            # Example maintenance tasks
            cleanup_days = job.config.get('cleanup_days', 30)
            cutoff_date = datetime.utcnow() - timedelta(days=cleanup_days)
            
            # Clean up old job executions
            cleaned_count = self._cleanup_old_executions(cutoff_date)
            
            return {
                'success': True,
                'cleaned_executions': cleaned_count,
                'cutoff_date': cutoff_date.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Maintenance job failed: {e}")
            raise
    
    def _handle_custom(self, job: Job) -> Dict[str, Any]:
        """Handle custom job - placeholder for user-defined jobs"""
        try:
            # Custom jobs should register their own handlers
            # This is a fallback that just logs the job config
            logger.info(f"Custom job executed with config: {job.config}")
            
            return {
                'success': True,
                'message': 'Custom job executed successfully',
                'config': job.config
            }
            
        except Exception as e:
            logger.error(f"Custom job failed: {e}")
            raise
    
    def _cleanup_old_executions(self, cutoff_date: datetime) -> int:
        """Clean up old job executions"""
        try:
            # This would need to be implemented based on the database adapter
            # For now, return 0
            logger.info(f"Would clean up executions older than {cutoff_date}")
            return 0
        except Exception as e:
            logger.error(f"Failed to cleanup old executions: {e}")
            return 0

class DatabaseJobScheduler:
    """Database-driven job scheduler"""
    
    def __init__(self, db_manager: DatabaseManager, check_interval: int = 60):
        self.db_manager = db_manager
        self.job_manager = JobManager(db_manager)
        self.job_executor = JobExecutor(self.job_manager)
        self.check_interval = check_interval
        
        self.running = False
        self.scheduler_thread: Optional[threading.Thread] = None
        self.worker_threads: Dict[str, threading.Thread] = {}
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("Database job scheduler initialized")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.stop()
    
    def start(self):
        """Start the job scheduler"""
        if self.running:
            logger.warning("Scheduler is already running")
            return
        
        logger.info("Starting database job scheduler...")
        self.running = True
        
        # Start the main scheduler thread
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=False)
        self.scheduler_thread.start()
        
        logger.info("Database job scheduler started")
    
    def stop(self):
        """Stop the job scheduler"""
        if not self.running:
            return
        
        logger.info("Stopping job scheduler...")
        self.running = False
        
        # Wait for scheduler thread to finish
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=30)
        
        # Wait for worker threads to finish
        for thread_id, thread in list(self.worker_threads.items()):
            if thread.is_alive():
                logger.info(f"Waiting for worker thread {thread_id} to finish...")
                thread.join(timeout=30)
        
        self.worker_threads.clear()
        logger.info("Job scheduler stopped")
    
    def _scheduler_loop(self):
        """Main scheduler loop"""
        logger.info(f"Scheduler loop started (check interval: {self.check_interval}s)")
        
        while self.running:
            try:
                # Get jobs that are due for execution
                due_jobs = self.job_manager.get_due_jobs()
                
                if due_jobs:
                    logger.info(f"Found {len(due_jobs)} jobs due for execution")
                    
                    for job in due_jobs:
                        if not self.running:
                            break
                        
                        # Check if job is already running
                        if job.job_id in self.worker_threads:
                            if self.worker_threads[job.job_id].is_alive():
                                logger.debug(f"Job {job.name} is already running, skipping")
                                continue
                            else:
                                # Clean up finished thread
                                del self.worker_threads[job.job_id]
                        
                        # Start job execution in a separate thread
                        self._start_job_execution(job)
                
                # Clean up finished worker threads
                self._cleanup_finished_threads()
                
                # Sleep until next check
                time.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                logger.error(traceback.format_exc())
                time.sleep(self.check_interval)
        
        logger.info("Scheduler loop stopped")
    
    def _start_job_execution(self, job: Job):
        """Start job execution in a separate thread"""
        def execute_job():
            try:
                logger.info(f"Executing job: {job.name} ({job.job_id})")
                execution = self.job_executor.execute_job(job)
                
                if execution.status == ExecutionStatus.SUCCESS:
                    logger.info(f"Job completed: {job.name} - {execution.result}")
                else:
                    logger.error(f"Job failed: {job.name} - {execution.error_message}")
                    
            except Exception as e:
                logger.error(f"Unexpected error executing job {job.name}: {e}")
                logger.error(traceback.format_exc())
            finally:
                # Remove from worker threads when done
                self.worker_threads.pop(job.job_id, None)
        
        # Start worker thread
        worker_thread = threading.Thread(target=execute_job, daemon=True)
        worker_thread.start()
        
        self.worker_threads[job.job_id] = worker_thread
        logger.info(f"Started worker thread for job: {job.name}")
    
    def _cleanup_finished_threads(self):
        """Clean up finished worker threads"""
        finished_threads = []
        for job_id, thread in self.worker_threads.items():
            if not thread.is_alive():
                finished_threads.append(job_id)
        
        for job_id in finished_threads:
            del self.worker_threads[job_id]
    
    def register_job_handler(self, job_type: str, handler: Callable):
        """Register a custom job handler"""
        self.job_executor.register_handler(job_type, handler)
    
    def create_job(self, name: str, job_type: str, schedule_expression: str, config: Dict[str, Any], **kwargs) -> Optional[str]:
        """Create a new job"""
        try:
            job_type_enum = JobType(job_type) if job_type in [t.value for t in JobType] else JobType.CUSTOM
            
            job = Job(
                name=name,
                job_type=job_type_enum,
                schedule_expression=schedule_expression,
                config=config,
                **kwargs
            )
            
            if self.job_manager.create_job(job):
                logger.info(f"Created job: {name} ({job.job_id})")
                return job.job_id
            else:
                logger.error(f"Failed to create job: {name}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating job {name}: {e}")
            return None
    
    def get_status(self) -> Dict[str, Any]:
        """Get scheduler status"""
        return {
            'running': self.running,
            'active_workers': len(self.worker_threads),
            'check_interval': self.check_interval,
            'statistics': self.job_manager.get_job_statistics()
        }
    
    def list_jobs(self, **kwargs) -> list:
        """List jobs"""
        return self.job_manager.list_jobs(**kwargs)
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get a job by ID"""
        return self.job_manager.get_job(job_id)
    
    def pause_job(self, job_id: str) -> bool:
        """Pause a job"""
        job = self.job_manager.get_job(job_id)
        if job:
            job.status = JobStatus.PAUSED
            return self.job_manager.update_job(job)
        return False
    
    def resume_job(self, job_id: str) -> bool:
        """Resume a paused job"""
        job = self.job_manager.get_job(job_id)
        if job:
            job.status = JobStatus.ACTIVE
            return self.job_manager.update_job(job)
        return False
    
    def delete_job(self, job_id: str) -> bool:
        """Delete a job"""
        return self.job_manager.delete_job(job_id)
    
    def trigger_job(self, job_id: str) -> bool:
        """Trigger immediate execution of a job"""
        try:
            job = self.job_manager.get_job(job_id)
            if not job:
                logger.error(f"Job not found: {job_id}")
                return False
            
            # Set next execution to now
            job.next_execution = datetime.utcnow()
            if self.job_manager.update_job(job):
                logger.info(f"Triggered immediate execution for job: {job.name}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to trigger job {job_id}: {e}")
            return False