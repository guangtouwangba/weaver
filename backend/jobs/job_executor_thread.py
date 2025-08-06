#!/usr/bin/env python3
"""
Job Executor Thread
Continuously pulls and executes jobs from database
"""

import os
import sys
import logging
import threading
import time
from typing import Optional
from datetime import datetime

# Add backend path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database.database_adapter import DatabaseManager
from jobs.job_picker import CloudJobPicker
from jobs.simple_job_executor import SimpleJobExecutor
from database.cloud_job_models import CloudJob

logger = logging.getLogger(__name__)

class JobExecutorThread:
    """Continuously executes jobs from database in a separate thread"""
    
    def __init__(self, db_manager: DatabaseManager, instance_id: str, check_interval: int = 30):
        self.db_manager = db_manager
        self.instance_id = instance_id
        self.check_interval = check_interval  # seconds between job checks
        
        self.job_picker = CloudJobPicker(db_manager, instance_id)
        self.job_executor = SimpleJobExecutor(db_manager, instance_id)
        
        self.running = False
        self.thread: Optional[threading.Thread] = None
        
        # Statistics
        self.stats = {
            'jobs_executed': 0,
            'jobs_succeeded': 0,
            'jobs_failed': 0,
            'last_job_time': None,
            'thread_start_time': None
        }
        
        logger.info(f"JobExecutorThread initialized - Instance: {instance_id}, Check interval: {check_interval}s")
    
    def start(self):
        """Start the job executor thread"""
        if self.running:
            logger.warning("Job executor thread is already running")
            return
        
        logger.info("Starting job executor thread...")
        self.running = True
        self.stats['thread_start_time'] = datetime.utcnow()
        
        self.thread = threading.Thread(target=self._executor_loop, daemon=False)
        self.thread.start()
        
        logger.info("Job executor thread started")
    
    def stop(self):
        """Stop the job executor thread"""
        if not self.running:
            return
        
        logger.info("Stopping job executor thread...")
        self.running = False
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=30)
        
        logger.info("Job executor thread stopped")
    
    def _executor_loop(self):
        """Main executor loop - continuously looks for and executes jobs"""
        logger.info(f"Job executor loop started - checking every {self.check_interval}s")
        
        consecutive_no_jobs = 0
        max_no_jobs_before_longer_wait = 5
        
        while self.running:
            try:
                # Proactively clean up expired locks every few cycles
                if self.stats['jobs_executed'] % 5 == 0:  # Every 5th cycle
                    self.job_picker._release_expired_locks()
                
                # Look for available job
                job = self.job_picker.get_next_job()
                
                if job:
                    consecutive_no_jobs = 0
                    self._execute_job(job)
                else:
                    consecutive_no_jobs += 1
                    
                    # If no jobs for a while, wait longer to reduce database load
                    if consecutive_no_jobs >= max_no_jobs_before_longer_wait:
                        wait_time = min(self.check_interval * 2, 300)  # Max 5 minutes
                        logger.debug(f"No jobs found for {consecutive_no_jobs} cycles, waiting {wait_time}s")
                        time.sleep(wait_time)
                        consecutive_no_jobs = 0
                        continue
                
                # Regular interval wait
                if self.running:
                    time.sleep(self.check_interval)
                    
            except Exception as e:
                logger.error(f"Error in job executor loop: {e}")
                if self.running:
                    time.sleep(self.check_interval)
        
        logger.info("Job executor loop finished")
    
    def _execute_job(self, job: CloudJob):
        """Execute a single job and handle results"""
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"🎯 Executing job: {job.name} ({job.job_type.value}) - ID: {job.job_id}")
            
            # Execute the job
            result = self.job_executor.execute_job(job)
            
            # Update statistics
            self.stats['jobs_executed'] += 1
            self.stats['last_job_time'] = start_time
            
            success = result.get('success', False)
            if success:
                self.stats['jobs_succeeded'] += 1
                logger.info(f"✅ Job completed successfully: {job.name}")
                logger.info(f"   Duration: {result.get('duration_seconds', 0):.2f}s")
                if result.get('result'):
                    logger.info(f"   Result: {result['result']}")
            else:
                self.stats['jobs_failed'] += 1
                logger.error(f"❌ Job failed: {job.name}")
                logger.error(f"   Error: {result.get('error', 'Unknown error')}")
            
            # Complete job (update status and release lock)
            self.job_picker.complete_job(
                job,
                success,
                result.get('result'),
                result.get('error')
            )
            
        except Exception as e:
            logger.error(f"💥 Fatal error executing job {job.job_id}: {e}")
            self.stats['jobs_failed'] += 1
            
            # Try to complete job as failed
            try:
                self.job_picker.complete_job(job, False, None, str(e))
            except Exception as completion_error:
                logger.error(f"Failed to complete failed job: {completion_error}")
    
    def get_status(self) -> dict:
        """Get current status of the executor thread"""
        return {
            'running': self.running,
            'instance_id': self.instance_id,
            'check_interval': self.check_interval,
            'thread_alive': self.thread.is_alive() if self.thread else False,
            'statistics': self.stats.copy()
        }
    
    def get_job_statistics(self) -> dict:
        """Get database job statistics"""
        try:
            return self.job_picker.get_job_statistics()
        except Exception as e:
            logger.error(f"Failed to get job statistics: {e}")
            return {}
    
    def is_healthy(self) -> bool:
        """Check if the executor thread is healthy"""
        return (
            self.running and 
            self.thread is not None and 
            self.thread.is_alive()
        )