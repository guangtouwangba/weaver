#!/usr/bin/env python3
"""
Standalone job scheduler for cronjob system
This service runs continuously and triggers scheduled jobs by calling the API
"""
import asyncio
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any
import requests
from croniter import croniter

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database import init_database, get_session
from database.models import CronJob, JobRun

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class JobScheduler:
    """Handles scheduling and triggering of cronjobs"""
    
    def __init__(self):
        self.api_base_url = os.getenv('API_BASE_URL', 'http://localhost:8000')
        self.scheduler_interval = int(os.getenv('SCHEDULER_INTERVAL', 60))  # seconds
        self.running = False
        
        # Initialize database
        self.db_manager = init_database()
        
        logger.info(f"Job scheduler initialized:")
        logger.info(f"  API Base URL: {self.api_base_url}")
        logger.info(f"  Check interval: {self.scheduler_interval}s")
    
    async def start(self):
        """Start the scheduler loop"""
        logger.info("🚀 Starting job scheduler...")
        self.running = True
        
        while self.running:
            try:
                await self.check_and_trigger_jobs()
                await asyncio.sleep(self.scheduler_interval)
                
            except KeyboardInterrupt:
                logger.info("Received interrupt signal, shutting down...")
                self.running = False
                break
                
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                await asyncio.sleep(self.scheduler_interval)
    
    async def check_and_trigger_jobs(self):
        """Check for jobs that need to be triggered"""
        try:
            with get_session() as session:
                # Get all enabled jobs
                jobs = session.query(CronJob).filter(CronJob.enabled == True).all()
                
                if not jobs:
                    logger.debug("No enabled jobs found")
                    return
                
                logger.debug(f"Checking {len(jobs)} enabled jobs...")
                
                for job in jobs:
                    if await self.should_trigger_job(job, session):
                        await self.trigger_job(job)
                        
        except Exception as e:
            logger.error(f"Error checking jobs: {e}")
    
    async def should_trigger_job(self, job: CronJob, session) -> bool:
        """Determine if a job should be triggered"""
        try:
            now = datetime.utcnow()
            
            # Get the last successful run
            last_run = session.query(JobRun).filter(
                JobRun.job_id == job.id
            ).order_by(JobRun.started_at.desc()).first()
            
            # If job has never run, trigger it
            if not last_run:
                logger.info(f"Job '{job.name}' has never run, triggering...")
                return True
            
            # Check if there's already a running job
            running_job = session.query(JobRun).filter(
                JobRun.job_id == job.id,
                JobRun.status.in_(['pending', 'running'])
            ).first()
            
            if running_job:
                logger.debug(f"Job '{job.name}' is already running, skipping...")
                return False
            
            # Check cron expression
            if job.cron_expression:
                return self.should_trigger_cron_job(job, last_run.started_at, now)
            
            # Check interval-based scheduling
            elif job.interval_hours:
                return self.should_trigger_interval_job(job, last_run.started_at, now)
            
            else:
                logger.warning(f"Job '{job.name}' has no scheduling configuration")
                return False
                
        except Exception as e:
            logger.error(f"Error checking if job {job.name} should trigger: {e}")
            return False
    
    def should_trigger_cron_job(self, job: CronJob, last_run_time: datetime, now: datetime) -> bool:
        """Check if cron-based job should be triggered"""
        try:
            cron = croniter(job.cron_expression, last_run_time)
            next_run = cron.get_next(datetime)
            
            if now >= next_run:
                logger.info(f"Cron job '{job.name}' is due (next run: {next_run})")
                return True
            
            logger.debug(f"Cron job '{job.name}' not due yet (next run: {next_run})")
            return False
            
        except Exception as e:
            logger.error(f"Error parsing cron expression for job {job.name}: {e}")
            return False
    
    def should_trigger_interval_job(self, job: CronJob, last_run_time: datetime, now: datetime) -> bool:
        """Check if interval-based job should be triggered"""
        try:
            next_run = last_run_time + timedelta(hours=job.interval_hours)
            
            if now >= next_run:
                logger.info(f"Interval job '{job.name}' is due (interval: {job.interval_hours}h)")
                return True
            
            logger.debug(f"Interval job '{job.name}' not due yet (next run: {next_run})")
            return False
            
        except Exception as e:
            logger.error(f"Error calculating interval for job {job.name}: {e}")
            return False
    
    async def trigger_job(self, job: CronJob):
        """Trigger a job by calling the API"""
        try:
            trigger_url = f"{self.api_base_url}/api/cronjobs/{job.id}/trigger"
            
            payload = {
                "force_reprocess": False
            }
            
            logger.info(f"Triggering job: {job.name}")
            
            response = requests.post(
                trigger_url,
                json=payload,
                timeout=30,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Successfully triggered job '{job.name}' (run ID: {result.get('job_run_id')})")
            else:
                logger.error(f"❌ Failed to trigger job '{job.name}': {response.status_code} - {response.text}")
                
        except requests.RequestException as e:
            logger.error(f"❌ Network error triggering job '{job.name}': {e}")
        except Exception as e:
            logger.error(f"❌ Unexpected error triggering job '{job.name}': {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        try:
            # Check database connection
            with get_session() as session:
                job_count = session.query(CronJob).count()
            
            # Check API connectivity
            health_url = f"{self.api_base_url}/health"
            response = requests.get(health_url, timeout=10)
            api_healthy = response.status_code == 200
            
            return {
                'status': 'healthy' if api_healthy else 'degraded',
                'scheduler_running': self.running,
                'database_jobs': job_count,
                'api_connectivity': api_healthy,
                'last_check': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'last_check': datetime.utcnow().isoformat()
            }
    
    def stop(self):
        """Stop the scheduler"""
        logger.info("Stopping job scheduler...")
        self.running = False

async def main():
    """Main entry point"""
    scheduler = JobScheduler()
    
    try:
        # Test database connection
        logger.info("Testing database connection...")
        with get_session() as session:
            job_count = session.query(CronJob).count()
            logger.info(f"Database connected. Found {job_count} jobs.")
        
        # Test API connectivity
        logger.info("Testing API connectivity...")
        try:
            health_url = f"{scheduler.api_base_url}/health"
            response = requests.get(health_url, timeout=10)
            if response.status_code == 200:
                logger.info("✅ API connectivity test passed")
            else:
                logger.warning(f"⚠️ API returned status {response.status_code}")
        except Exception as e:
            logger.warning(f"⚠️ API connectivity test failed: {e}")
        
        # Start scheduler
        await scheduler.start()
        
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error(f"Scheduler failed: {e}")
        sys.exit(1)
    finally:
        scheduler.stop()
        logger.info("Job scheduler stopped")

if __name__ == '__main__':
    # Install croniter if not available
    try:
        import croniter
    except ImportError:
        logger.error("croniter package is required. Install with: pip install croniter")
        sys.exit(1)
    
    # Run the scheduler
    asyncio.run(main())