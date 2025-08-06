#!/usr/bin/env python3
"""
Hybrid Job Scheduler
Multi-threaded scheduler with:
- Thread 1: Continuously pulls and executes jobs from database
- Thread 2: Creates jobs based on cron schedules
"""

import os
import sys
import logging
import argparse
import signal
import time
import uuid
from typing import List, Dict, Any
from datetime import datetime
import yaml
from dotenv import load_dotenv

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from database.database_adapter import create_database_manager
from jobs.job_executor_thread import JobExecutorThread
from jobs.job_creator_thread import JobCreatorThread, CronJobDefinition
from jobs.lock_cleaner_thread import LockCleanerThread
from utils.logging_config import setup_clean_logging

def load_config(config_path: str = "config.yaml"):
    """Load main configuration"""
    import re
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Substitute environment variables
            def replace_env_var(match):
                var_name = match.group(1)
                return os.environ.get(var_name, match.group(0))
            
            content = re.sub(r'\$\{([^}]+)\}', replace_env_var, content)
            return yaml.safe_load(content)
    except Exception as e:
        print(f"Error loading config: {e}")
        sys.exit(1)

def load_job_schedules(schedules_path: str = "job_schedules.yaml") -> tuple:
    """Load job schedule definitions"""
    try:
        with open(schedules_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        # Parse cron job definitions
        cron_definitions = []
        for job_def in data.get('job_schedules', []):
            try:
                cron_def = CronJobDefinition(
                    name=job_def['name'],
                    job_type=job_def['job_type'],
                    cron_expression=job_def['cron_expression'],
                    config=job_def.get('config', {}),
                    description=job_def.get('description', ''),
                    max_retries=job_def.get('max_retries', 3),
                    enabled=job_def.get('enabled', True)
                )
                cron_definitions.append(cron_def)
            except Exception as e:
                print(f"Error parsing job definition '{job_def.get('name', 'unknown')}': {e}")
        
        scheduler_settings = data.get('scheduler_settings', {})
        
        return cron_definitions, scheduler_settings
        
    except FileNotFoundError:
        print(f"Job schedules file not found: {schedules_path}")
        print("Creating default job schedules...")
        return [], {}
    except Exception as e:
        print(f"Error loading job schedules: {e}")
        return [], {}

class HybridJobScheduler:
    """Main hybrid job scheduler with multiple threads"""
    
    def __init__(self, config: Dict[str, Any], cron_definitions: List[CronJobDefinition], 
                 scheduler_settings: Dict[str, Any]):
        self.config = config
        self.scheduler_settings = scheduler_settings
        
        # Generate instance ID
        instance_prefix = scheduler_settings.get('instance_prefix', 'hybrid-scheduler')
        self.instance_id = f"{instance_prefix}-{str(uuid.uuid4())[:8]}"
        
        # Create database manager
        self.db_manager = create_database_manager(config)
        
        # Get settings
        job_check_interval = scheduler_settings.get('job_check_interval', 30)
        cron_check_interval = scheduler_settings.get('cron_check_interval', 60)
        
        # Create threads
        self.executor_thread = JobExecutorThread(
            self.db_manager, 
            self.instance_id,
            job_check_interval
        )
        
        self.creator_thread = JobCreatorThread(
            self.db_manager,
            cron_definitions,
            cron_check_interval
        )
        
        # Create lock cleaner thread
        lock_clean_interval = scheduler_settings.get('lock_clean_interval', 300)  # 5 minutes default
        self.lock_cleaner = LockCleanerThread(
            self.db_manager,
            lock_clean_interval
        )
        
        self.running = False
        self.logger = logging.getLogger(__name__)
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.logger.info(f"HybridJobScheduler initialized - Instance: {self.instance_id}")
        self.logger.info(f"Database: {type(self.db_manager.adapter).__name__}")
        self.logger.info(f"Cron definitions: {len(cron_definitions)}")
        self.logger.info(f"Job check interval: {job_check_interval}s")
        self.logger.info(f"Cron check interval: {cron_check_interval}s")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.stop()
    
    def start(self):
        """Start both executor and creator threads"""
        if self.running:
            self.logger.warning("Hybrid scheduler is already running")
            return
        
        self.logger.info("🚀 Starting Hybrid Job Scheduler...")
        self.running = True
        
        try:
            # Start all threads
            self.executor_thread.start()
            self.creator_thread.start()
            self.lock_cleaner.start()
            
            self.logger.info("✅ Hybrid Job Scheduler started")
            self.logger.info(f"   Instance: {self.instance_id}")
            self.logger.info(f"   Threads: {'✅' if self.executor_thread.is_healthy() else '❌'} executor, {'✅' if self.creator_thread.is_healthy() else '❌'} creator, {'✅' if self.lock_cleaner.is_healthy() else '❌'} cleaner")
            
            # Print initial statistics
            self._print_status()
            
        except Exception as e:
            self.logger.error(f"Failed to start hybrid scheduler: {e}")
            self.stop()
            raise
    
    def stop(self):
        """Stop both threads gracefully"""
        if not self.running:
            return
        
        self.logger.info("🛑 Stopping Hybrid Job Scheduler...")
        self.running = False
        
        # Stop all threads
        self.creator_thread.stop()
        self.lock_cleaner.stop()
        self.executor_thread.stop()
        
        self.logger.info("✅ Hybrid Job Scheduler stopped")
    
    def run_forever(self):
        """Run the scheduler until interrupted"""
        try:
            while self.running:
                time.sleep(60)  # Check every minute
                
                # Health check
                if not self.executor_thread.is_healthy():
                    self.logger.error("❌ Executor thread is not healthy!")
                
                if not self.creator_thread.is_healthy():
                    self.logger.error("❌ Creator thread is not healthy!")
                
                if not self.lock_cleaner.is_healthy():
                    self.logger.error("❌ Lock cleaner thread is not healthy!")
                
        except KeyboardInterrupt:
            self.logger.info("Received keyboard interrupt")
        finally:
            self.stop()
    
    def _print_status(self):
        """Print current status"""
        try:
            # Get job statistics
            job_stats = self.executor_thread.get_job_statistics()
            
            # Get thread status
            executor_status = self.executor_thread.get_status()
            creator_status = self.creator_thread.get_status()
            
            self.logger.info("📊 Status Summary:")
            self.logger.info(f"   Jobs: {job_stats.get('total_jobs', 0)} total, {job_stats.get('waiting_jobs', 0)} waiting")
            self.logger.info(f"   Executor: {executor_status.get('statistics', {}).get('jobs_executed', 0)} executed")
            self.logger.info(f"   Creator: {creator_status.get('statistics', {}).get('jobs_created', 0)} created")
            
        except Exception as e:
            self.logger.error(f"Error getting status: {e}")
    
    def get_full_status(self) -> Dict[str, Any]:
        """Get comprehensive status information"""
        return {
            'instance_id': self.instance_id,
            'running': self.running,
            'start_time': datetime.utcnow().isoformat(),
            'database_type': type(self.db_manager.adapter).__name__,
            'executor_thread': self.executor_thread.get_status(),
            'creator_thread': self.creator_thread.get_status(),
            'job_statistics': self.executor_thread.get_job_statistics()
        }

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Hybrid Job Scheduler")
    parser.add_argument('--config', default='config.yaml', help='Main configuration file')
    parser.add_argument('--schedules', default='job_schedules.yaml', help='Job schedules configuration file')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    parser.add_argument('--daemon', action='store_true', help='Run as daemon')
    parser.add_argument('--status', action='store_true', help='Show status and exit')
    
    args = parser.parse_args()
    
    # Setup logging
    if args.verbose:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO
        
    setup_clean_logging(log_level, 'hybrid_scheduler.log')
    
    logger = logging.getLogger(__name__)
    
    try:
        # Load environment variables
        load_dotenv()
        
        # Load configurations
        if not os.path.exists(args.config):
            logger.error(f"❌ Configuration file not found: {args.config}")
            sys.exit(1)
        
        config = load_config(args.config)
        cron_definitions, scheduler_settings = load_job_schedules(args.schedules)
        
        if not cron_definitions:
            logger.warning("⚠️ No cron job definitions found")
        
        # Auto-detect database provider
        if not config.get('database', {}).get('provider'):
            if os.getenv('SUPABASE_URL'):
                config.setdefault('database', {})['provider'] = 'supabase'
                logger.info("🔍 Detected Supabase credentials, using Supabase")
            else:
                config.setdefault('database', {})['provider'] = 'sqlite'
                logger.info("🔍 Using SQLite database")
        
        # Create and start scheduler
        scheduler = HybridJobScheduler(config, cron_definitions, scheduler_settings)
        
        if args.status:
            # Just show status and exit
            status = scheduler.get_full_status()
            print(yaml.dump(status, default_flow_style=False))
            return
        
        # Start scheduler
        scheduler.start()
        
        if args.daemon:
            logger.info("Running in daemon mode...")
            scheduler.run_forever()
        else:
            logger.info("Running in interactive mode (Ctrl+C to stop)...")
            try:
                scheduler.run_forever()
            except KeyboardInterrupt:
                logger.info("Received keyboard interrupt")
    
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        if args.verbose:
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main()