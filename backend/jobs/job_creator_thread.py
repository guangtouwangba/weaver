#!/usr/bin/env python3
"""
Job Creator Thread
Creates jobs based on cron schedules defined in configuration
"""

import os
import sys
import logging
import threading
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

try:
    from croniter import croniter
    CRONITER_AVAILABLE = True
except ImportError:
    CRONITER_AVAILABLE = False

# Add backend path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database.database_adapter import DatabaseManager
from database.cloud_job_models import CloudJob, CloudJobType, CloudJobStatus

logger = logging.getLogger(__name__)

class CronJobDefinition:
    """Definition of a cron-based job creation rule"""
    
    def __init__(self, name: str, job_type: str, cron_expression: str, config: Dict[str, Any], 
                 description: str = "", max_retries: int = 3, enabled: bool = True):
        if not CRONITER_AVAILABLE:
            raise ImportError("croniter library is required. Install with: pip install croniter")
        
        self.name = name
        self.job_type = job_type
        self.cron_expression = cron_expression
        self.config = config
        self.description = description
        self.max_retries = max_retries
        self.enabled = enabled
        self.last_created = None
        
        # Validate cron expression
        try:
            croniter(cron_expression)
        except Exception as e:
            raise ValueError(f"Invalid cron expression '{cron_expression}': {e}")
        
        logger.debug(f"CronJobDefinition created: {name} - {cron_expression}")
    
    def should_create_job(self, current_time: datetime) -> bool:
        """Check if a job should be created based on cron schedule"""
        if not self.enabled:
            return False
        
        cron = croniter(self.cron_expression, current_time)
        next_run = cron.get_prev(datetime)
        
        # If this is the first check or if we've passed the next scheduled time
        if self.last_created is None:
            # For first run, only create if we're very close to the scheduled time (within 5 minutes)
            if abs((current_time - next_run).total_seconds()) <= 300:
                return True
        else:
            # Create if the next scheduled time is after our last creation
            if next_run > self.last_created:
                return True
        
        return False
    
    def create_job_instance(self) -> CloudJob:
        """Create a CloudJob instance from this definition"""
        # Generate unique name with timestamp
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_name = f"{self.name}_{timestamp}"
        
        job = CloudJob(
            name=unique_name,
            job_type=CloudJobType(self.job_type),
            config=self.config.copy(),
            description=f"{self.description} (Auto-created by cron: {self.cron_expression})",
            max_retries=self.max_retries,
            status=CloudJobStatus.WAITING
        )
        
        self.last_created = datetime.utcnow()
        return job

class JobCreatorThread:
    """Creates jobs based on cron schedules in a separate thread"""
    
    def __init__(self, db_manager: DatabaseManager, cron_definitions: List[CronJobDefinition], 
                 check_interval: int = 60):
        self.db_manager = db_manager
        self.cron_definitions = cron_definitions
        self.check_interval = check_interval  # seconds between cron checks
        
        self.running = False
        self.thread: Optional[threading.Thread] = None
        
        # Statistics
        self.stats = {
            'jobs_created': 0,
            'creation_errors': 0,
            'last_check_time': None,
            'thread_start_time': None,
            'active_cron_rules': len([d for d in cron_definitions if d.enabled])
        }
        
        logger.info(f"JobCreatorThread initialized - {len(cron_definitions)} cron rules, check interval: {check_interval}s")
    
    def start(self):
        """Start the job creator thread"""
        if self.running:
            logger.warning("Job creator thread is already running")
            return
        
        logger.info("Starting job creator thread...")
        self.running = True
        self.stats['thread_start_time'] = datetime.utcnow()
        
        self.thread = threading.Thread(target=self._creator_loop, daemon=False)
        self.thread.start()
        
        logger.info("Job creator thread started")
    
    def stop(self):
        """Stop the job creator thread"""
        if not self.running:
            return
        
        logger.info("Stopping job creator thread...")
        self.running = False
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=30)
        
        logger.info("Job creator thread stopped")
    
    def _creator_loop(self):
        """Main creator loop - checks cron schedules and creates jobs"""
        logger.info(f"Job creator loop started - checking every {self.check_interval}s")
        
        while self.running:
            try:
                current_time = datetime.utcnow()
                self.stats['last_check_time'] = current_time
                
                jobs_created_this_cycle = 0
                
                # Check each cron definition
                for cron_def in self.cron_definitions:
                    if not self.running:
                        break
                    
                    try:
                        if cron_def.should_create_job(current_time):
                            job = cron_def.create_job_instance()
                            
                            if self._create_job_in_database(job):
                                jobs_created_this_cycle += 1
                                self.stats['jobs_created'] += 1
                                logger.info(f"📅 Created scheduled job: {job.name} ({job.job_type.value})")
                            else:
                                self.stats['creation_errors'] += 1
                                logger.error(f"Failed to create job: {job.name}")
                    
                    except Exception as e:
                        self.stats['creation_errors'] += 1
                        logger.error(f"Error processing cron definition '{cron_def.name}': {e}")
                
                if jobs_created_this_cycle > 0:
                    logger.info(f"Created {jobs_created_this_cycle} jobs this cycle")
                
                # Wait for next check
                if self.running:
                    time.sleep(self.check_interval)
                    
            except Exception as e:
                logger.error(f"Error in job creator loop: {e}")
                if self.running:
                    time.sleep(self.check_interval)
        
        logger.info("Job creator loop finished")
    
    def _create_job_in_database(self, job: CloudJob) -> bool:
        """Create a job in the database"""
        try:
            if hasattr(self.db_manager.adapter, 'client') and hasattr(self.db_manager.adapter.client, 'client'):
                # Supabase
                self.db_manager.adapter.client.client.table('cloud_jobs').insert(job.to_dict()).execute()
            else:
                # SQLite
                import sqlite3
                conn = sqlite3.connect(self.db_manager.adapter.db_path)
                cursor = conn.cursor()
                
                data = job.to_dict()
                cursor.execute("""
                    INSERT INTO cloud_jobs 
                    (job_id, name, job_type, config, status, description, max_retries, current_retries, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    data['job_id'], data['name'], data['job_type'], data['config'], 
                    data['status'], data['description'], data['max_retries'], 
                    data['current_retries'], data['created_at']
                ))
                
                conn.commit()
                cursor.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create job in database: {e}")
            return False
    
    def add_cron_definition(self, cron_def: CronJobDefinition):
        """Add a new cron definition (can be called while running)"""
        self.cron_definitions.append(cron_def)
        self.stats['active_cron_rules'] = len([d for d in self.cron_definitions if d.enabled])
        logger.info(f"Added cron definition: {cron_def.name}")
    
    def remove_cron_definition(self, name: str) -> bool:
        """Remove a cron definition by name"""
        for i, cron_def in enumerate(self.cron_definitions):
            if cron_def.name == name:
                del self.cron_definitions[i]
                self.stats['active_cron_rules'] = len([d for d in self.cron_definitions if d.enabled])
                logger.info(f"Removed cron definition: {name}")
                return True
        return False
    
    def enable_cron_definition(self, name: str) -> bool:
        """Enable a cron definition"""
        for cron_def in self.cron_definitions:
            if cron_def.name == name:
                cron_def.enabled = True
                self.stats['active_cron_rules'] = len([d for d in self.cron_definitions if d.enabled])
                logger.info(f"Enabled cron definition: {name}")
                return True
        return False
    
    def disable_cron_definition(self, name: str) -> bool:
        """Disable a cron definition"""
        for cron_def in self.cron_definitions:
            if cron_def.name == name:
                cron_def.enabled = False
                self.stats['active_cron_rules'] = len([d for d in self.cron_definitions if d.enabled])
                logger.info(f"Disabled cron definition: {name}")
                return True
        return False
    
    def get_status(self) -> dict:
        """Get current status of the creator thread"""
        return {
            'running': self.running,
            'check_interval': self.check_interval,
            'thread_alive': self.thread.is_alive() if self.thread else False,
            'cron_definitions': [
                {
                    'name': d.name,
                    'job_type': d.job_type,
                    'cron_expression': d.cron_expression,
                    'enabled': d.enabled,
                    'last_created': d.last_created.isoformat() if d.last_created else None
                }
                for d in self.cron_definitions
            ],
            'statistics': self.stats.copy()
        }
    
    def is_healthy(self) -> bool:
        """Check if the creator thread is healthy"""
        return (
            self.running and 
            self.thread is not None and 
            self.thread.is_alive()
        )