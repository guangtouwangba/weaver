#!/usr/bin/env python3
"""
Database-driven Job Scheduler Main Entry Point
Persistent job scheduling system that survives service restarts
"""

import os
import sys
import time
import logging
import argparse
from datetime import datetime
from dotenv import load_dotenv

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from database.database_adapter import create_database_manager
from jobs.job_scheduler import DatabaseJobScheduler
from database.job_models import JobType
from simple_paper_fetcher import SimplePaperFetcher

def load_config(config_path: str = "config.yaml"):
    """Load configuration from YAML file with environment variable substitution"""
    import yaml
    import re
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Substitute environment variables in the format ${VAR_NAME}
            def replace_env_var(match):
                var_name = match.group(1)
                return os.environ.get(var_name, match.group(0))
            
            content = re.sub(r'\$\{([^}]+)\}', replace_env_var, content)
            return yaml.safe_load(content)
    except Exception as e:
        print(f"Error loading config: {e}")
        sys.exit(1)

def setup_logging(log_level: str = "INFO"):
    """Setup logging configuration"""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('job_scheduler.log')
        ]
    )

def create_default_jobs(scheduler: DatabaseJobScheduler, config: dict):
    """Create default jobs based on configuration"""
    logger = logging.getLogger(__name__)
    
    try:
        # Check if we already have jobs
        existing_jobs = scheduler.list_jobs()
        if existing_jobs:
            logger.info(f"Found {len(existing_jobs)} existing jobs, skipping default job creation")
            return
        
        # Create default paper fetch job
        scheduler_config = config.get('scheduler', {})
        search_config = config.get('search', {})
        
        paper_fetch_config = {
            'config_path': 'config.yaml',
            'max_papers': search_config.get('max_papers_per_run', 100),
            'keywords': search_config.get('keywords', []),
            'categories': search_config.get('categories', [])
        }
        
        # Create job with schedule from config
        interval_hours = scheduler_config.get('interval_hours', 2)
        cron_expression = f"0 */{interval_hours} * * *"  # Every N hours
        
        job_id = scheduler.create_job(
            name="Automatic Paper Fetch",
            job_type="paper_fetch",
            schedule_expression=cron_expression,
            config=paper_fetch_config,
            description=f"Automatically fetch papers every {interval_hours} hours"
        )
        
        if job_id:
            logger.info(f"Created default paper fetch job: {job_id}")
        
        # Create maintenance job
        maintenance_config = {
            'cleanup_days': 30,
            'cleanup_executions': True
        }
        
        maintenance_job_id = scheduler.create_job(
            name="Weekly Maintenance",
            job_type="maintenance", 
            schedule_expression="0 2 * * 0",  # Every Sunday at 2 AM
            config=maintenance_config,
            description="Weekly cleanup and maintenance tasks"
        )
        
        if maintenance_job_id:
            logger.info(f"Created maintenance job: {maintenance_job_id}")
            
    except Exception as e:
        logger.error(f"Failed to create default jobs: {e}")

def list_jobs(scheduler: DatabaseJobScheduler):
    """List all jobs"""
    jobs = scheduler.list_jobs()
    
    if not jobs:
        print("No jobs found.")
        return
    
    print(f"\nFound {len(jobs)} jobs:")
    print("-" * 100)
    print(f"{'ID':<36} {'Name':<25} {'Type':<15} {'Status':<10} {'Schedule':<15} {'Next Run':<20}")
    print("-" * 100)
    
    for job in jobs:
        next_run = job.next_execution.strftime('%Y-%m-%d %H:%M') if job.next_execution else 'Not scheduled'
        print(f"{job.job_id:<36} {job.name:<25} {job.job_type.value if hasattr(job.job_type, 'value') else job.job_type:<15} {job.status.value if hasattr(job.status, 'value') else job.status:<10} {job.schedule_expression:<15} {next_run:<20}")

def show_job_details(scheduler: DatabaseJobScheduler, job_id: str):
    """Show detailed information about a job"""
    job = scheduler.get_job(job_id)
    if not job:
        print(f"Job not found: {job_id}")
        return
    
    print(f"\nJob Details:")
    print(f"  ID: {job.job_id}")
    print(f"  Name: {job.name}")
    print(f"  Type: {job.job_type.value if hasattr(job.job_type, 'value') else job.job_type}")
    print(f"  Status: {job.status.value if hasattr(job.status, 'value') else job.status}")
    print(f"  Schedule: {job.schedule_expression}")
    print(f"  Description: {job.description}")
    print(f"  Created: {job.created_at}")
    print(f"  Updated: {job.updated_at}")
    print(f"  Last Execution: {job.last_execution or 'Never'}")
    print(f"  Next Execution: {job.next_execution or 'Not scheduled'}")
    print(f"  Timeout: {job.timeout_seconds}s")
    print(f"  Retry Count: {job.retry_count}")
    print(f"  Config: {job.config}")
    
    # Show recent executions
    executions = scheduler.job_manager.get_job_executions(job_id, limit=5)
    if executions:
        print(f"\nRecent Executions:")
        print(f"  {'Execution ID':<36} {'Status':<10} {'Started':<20} {'Duration':<10} {'Result'}")
        print(f"  {'-'*36} {'-'*10} {'-'*20} {'-'*10} {'-'*20}")
        for exec in executions:
            duration = f"{exec.duration_seconds:.1f}s" if exec.duration_seconds else "N/A"
            started = exec.started_at.strftime('%Y-%m-%d %H:%M:%S') if exec.started_at else "N/A"
            result = str(exec.result).get('success', 'N/A') if exec.result else exec.error_message or "N/A"
            print(f"  {exec.execution_id:<36} {exec.status.value if hasattr(exec.status, 'value') else exec.status:<10} {started:<20} {duration:<10} {str(result)[:20]}")

def show_status(scheduler: DatabaseJobScheduler):
    """Show scheduler status"""
    status = scheduler.get_status()
    stats = status.get('statistics', {})
    
    print(f"\nScheduler Status:")
    print(f"  Running: {status['running']}")
    print(f"  Active Workers: {status['active_workers']}")
    print(f"  Check Interval: {status['check_interval']}s")
    
    print(f"\nJob Statistics:")
    print(f"  Total Jobs: {stats.get('total_jobs', 0)}")
    print(f"  Active Jobs: {stats.get('active_jobs', 0)}")
    print(f"  Paused Jobs: {stats.get('paused_jobs', 0)}")
    print(f"  Total Executions: {stats.get('total_executions', 0)}")
    print(f"  Successful Executions: {stats.get('successful_executions', 0)}")
    print(f"  Failed Executions: {stats.get('failed_executions', 0)}")
    
    if stats.get('total_executions', 0) > 0:
        success_rate = (stats.get('successful_executions', 0) / stats.get('total_executions', 1)) * 100
        print(f"  Success Rate: {success_rate:.1f}%")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Database-driven Job Scheduler")
    parser.add_argument('--config', default='config.yaml', help='Configuration file path')
    parser.add_argument('--log-level', default='INFO', help='Log level (DEBUG, INFO, WARNING, ERROR)')
    parser.add_argument('--check-interval', type=int, default=60, help='Job check interval in seconds')
    
    # Commands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Start scheduler
    start_parser = subparsers.add_parser('start', help='Start the job scheduler')
    start_parser.add_argument('--daemon', action='store_true', help='Run in daemon mode')
    
    # List jobs
    list_parser = subparsers.add_parser('list', help='List all jobs')
    
    # Show job details
    show_parser = subparsers.add_parser('show', help='Show job details')
    show_parser.add_argument('job_id', help='Job ID to show')
    
    # Status
    status_parser = subparsers.add_parser('status', help='Show scheduler status')
    
    # Control jobs
    pause_parser = subparsers.add_parser('pause', help='Pause a job')
    pause_parser.add_argument('job_id', help='Job ID to pause')
    
    resume_parser = subparsers.add_parser('resume', help='Resume a job')
    resume_parser.add_argument('job_id', help='Job ID to resume')
    
    trigger_parser = subparsers.add_parser('trigger', help='Trigger immediate job execution')
    trigger_parser.add_argument('job_id', help='Job ID to trigger')
    
    delete_parser = subparsers.add_parser('delete', help='Delete a job')
    delete_parser.add_argument('job_id', help='Job ID to delete')
    
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    # Load configuration
    if not os.path.exists(args.config):
        print(f"Configuration file not found: {args.config}")
        sys.exit(1)
    
    config = load_config(args.config)
    
    # Create database manager
    db_manager = create_database_manager(config)
    
    # Create scheduler
    scheduler = DatabaseJobScheduler(db_manager, check_interval=args.check_interval)
    
    try:
        if args.command == 'start' or not args.command:
            # Start scheduler
            logger.info("Starting database job scheduler...")
            
            # Create default jobs if none exist
            create_default_jobs(scheduler, config)
            
            # Start scheduler
            scheduler.start()
            
            if args.daemon:
                # Daemon mode - run indefinitely
                try:
                    while scheduler.running:
                        time.sleep(1)
                except KeyboardInterrupt:
                    logger.info("Received interrupt signal")
            else:
                # Interactive mode
                print("Job scheduler started. Commands:")
                print("  status  - Show status")
                print("  list    - List jobs")
                print("  quit    - Stop scheduler and exit")
                
                while scheduler.running:
                    try:
                        command = input("\n> ").strip().lower()
                        
                        if command == 'quit' or command == 'exit':
                            break
                        elif command == 'status':
                            show_status(scheduler)
                        elif command == 'list':
                            list_jobs(scheduler)
                        elif command == 'help':
                            print("Commands: status, list, quit")
                        elif command:
                            print(f"Unknown command: {command}")
                            
                    except (KeyboardInterrupt, EOFError):
                        break
            
        elif args.command == 'list':
            list_jobs(scheduler)
            
        elif args.command == 'show':
            show_job_details(scheduler, args.job_id)
            
        elif args.command == 'status':
            show_status(scheduler)
            
        elif args.command == 'pause':
            if scheduler.pause_job(args.job_id):
                print(f"Job paused: {args.job_id}")
            else:
                print(f"Failed to pause job: {args.job_id}")
                
        elif args.command == 'resume':
            if scheduler.resume_job(args.job_id):
                print(f"Job resumed: {args.job_id}")
            else:
                print(f"Failed to resume job: {args.job_id}")
                
        elif args.command == 'trigger':
            if scheduler.trigger_job(args.job_id):
                print(f"Job triggered: {args.job_id}")
            else:
                print(f"Failed to trigger job: {args.job_id}")
                
        elif args.command == 'delete':
            if scheduler.delete_job(args.job_id):
                print(f"Job deleted: {args.job_id}")
            else:
                print(f"Failed to delete job: {args.job_id}")
        
    finally:
        # Cleanup
        if scheduler.running:
            scheduler.stop()

if __name__ == "__main__":
    main()