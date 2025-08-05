#!/usr/bin/env python3
"""
Job Management CLI Tool
Easy-to-use command line interface for managing scheduled jobs
"""

import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv

# Add backend directory to path  
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from database.database_adapter import create_database_manager
from jobs.job_scheduler import DatabaseJobScheduler
from database.job_models import JobType, JobStatus

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
        print(f"❌ Error loading config: {e}")
        sys.exit(1)

def print_jobs_table(jobs):
    """Print jobs in a nice table format"""
    if not jobs:
        print("📝 No jobs found.")
        return
    
    print(f"\n📋 Found {len(jobs)} jobs:")
    print("=" * 120)
    print(f"{'Name':<25} {'Type':<12} {'Status':<8} {'Schedule':<15} {'Next Run':<20} {'ID':<36}")
    print("=" * 120)
    
    for job in jobs:
        next_run = job.next_execution.strftime('%m-%d %H:%M') if job.next_execution else 'Not scheduled'
        status = job.status.value if hasattr(job.status, 'value') else str(job.status)
        job_type = job.job_type.value if hasattr(job.job_type, 'value') else str(job.job_type)
        
        print(f"{job.name[:24]:<25} {job_type:<12} {status:<8} {job.schedule_expression:<15} {next_run:<20} {job.job_id}")

def print_job_details(job, executions=None):
    """Print detailed job information"""
    print(f"\n🔍 Job Details:")
    print(f"   Name: {job.name}")
    print(f"   ID: {job.job_id}")
    print(f"   Type: {job.job_type.value if hasattr(job.job_type, 'value') else job.job_type}")
    print(f"   Status: {job.status.value if hasattr(job.status, 'value') else job.status}")
    print(f"   Schedule: {job.schedule_expression}")
    print(f"   Description: {job.description}")
    print(f"   Created: {job.created_at.strftime('%Y-%m-%d %H:%M:%S') if job.created_at else 'Unknown'}")
    print(f"   Last Run: {job.last_execution.strftime('%Y-%m-%d %H:%M:%S') if job.last_execution else 'Never'}")
    print(f"   Next Run: {job.next_execution.strftime('%Y-%m-%d %H:%M:%S') if job.next_execution else 'Not scheduled'}")
    print(f"   Timeout: {job.timeout_seconds}s")
    print(f"   Retries: {job.retry_count}")
    
    if job.config:
        print(f"   Config: {json.dumps(job.config, indent=2)}")
    
    if executions:
        print(f"\n📊 Recent Executions:")
        if not executions:
            print("   No executions found")
        else:
            print(f"   {'Status':<10} {'Started':<20} {'Duration':<10} {'Result'}")
            print(f"   {'-'*10} {'-'*20} {'-'*10} {'-'*30}")
            for exec in executions[:5]:  # Show last 5
                duration = f"{exec.duration_seconds:.1f}s" if exec.duration_seconds else "N/A"
                started = exec.started_at.strftime('%m-%d %H:%M:%S') if exec.started_at else "N/A"
                status = exec.status.value if hasattr(exec.status, 'value') else str(exec.status)
                
                if exec.status.value == 'success' if hasattr(exec.status, 'value') else exec.status == 'success':
                    result = f"✅ {exec.result.get('new_papers', 0) if exec.result else 0} papers"
                elif exec.error_message:
                    result = f"❌ {exec.error_message[:25]}..."
                else:
                    result = "⏳ In progress"
                
                print(f"   {status:<10} {started:<20} {duration:<10} {result}")

def create_paper_fetch_job(scheduler, name, schedule, config):
    """Create a paper fetch job"""
    job_config = {
        'config_path': 'config.yaml',
        'max_papers': config.get('search', {}).get('max_papers_per_run', 100),
        'keywords': config.get('search', {}).get('keywords', []),
        'categories': config.get('search', {}).get('categories', [])
    }
    
    job_id = scheduler.create_job(
        name=name,
        job_type="paper_fetch",
        schedule_expression=schedule,
        config=job_config,
        description=f"Paper fetching job - {schedule}"
    )
    
    if job_id:
        print(f"✅ Created paper fetch job: {name} ({job_id})")
        return job_id
    else:
        print(f"❌ Failed to create job: {name}")
        return None

def interactive_mode(scheduler):
    """Interactive job management mode"""
    print("\n🎛️  Interactive Job Management")
    print("=" * 50)
    
    while True:
        print("\nCommands:")
        print("  list    - List all jobs")
        print("  show    - Show job details")
        print("  create  - Create a new job")
        print("  pause   - Pause a job")
        print("  resume  - Resume a job")
        print("  trigger - Trigger immediate execution")
        print("  delete  - Delete a job")
        print("  status  - Show scheduler status")
        print("  quit    - Exit")
        
        try:
            command = input("\n> ").strip().lower()
            
            if command == 'quit' or command == 'exit':
                break
                
            elif command == 'list':
                jobs = scheduler.list_jobs()
                print_jobs_table(jobs)
                
            elif command == 'show':
                job_id = input("Enter job ID (or name): ").strip()
                
                # Try to find by ID first, then by name
                job = scheduler.get_job(job_id)
                if not job:
                    jobs = scheduler.list_jobs()
                    matching_jobs = [j for j in jobs if j.name.lower() == job_id.lower()]
                    if matching_jobs:
                        job = matching_jobs[0]
                
                if job:
                    executions = scheduler.job_manager.get_job_executions(job.job_id, limit=10)
                    print_job_details(job, executions)
                else:
                    print(f"❌ Job not found: {job_id}")
                    
            elif command == 'create':
                print("\n📝 Create New Job")
                name = input("Job name: ").strip()
                if not name:
                    print("❌ Job name is required")
                    continue
                
                print("Job types: paper_fetch, maintenance, custom")
                job_type = input("Job type [paper_fetch]: ").strip() or "paper_fetch"
                
                print("Schedule examples:")
                print("  0 */2 * * *   - Every 2 hours")
                print("  0 9 * * *     - Daily at 9 AM")
                print("  0 9 * * 1-5   - Weekdays at 9 AM")
                schedule = input("Schedule (cron): ").strip()
                if not schedule:
                    print("❌ Schedule is required")
                    continue
                
                if job_type == "paper_fetch":
                    config = load_config()
                    job_id = create_paper_fetch_job(scheduler, name, schedule, config)
                else:
                    # For other job types, use basic config
                    job_id = scheduler.create_job(
                        name=name,
                        job_type=job_type,
                        schedule_expression=schedule,
                        config={}
                    )
                    
                    if job_id:
                        print(f"✅ Created job: {name} ({job_id})")
                    else:
                        print(f"❌ Failed to create job: {name}")
                        
            elif command in ['pause', 'resume', 'trigger', 'delete']:
                job_id = input(f"Enter job ID to {command}: ").strip()
                
                if command == 'pause':
                    success = scheduler.pause_job(job_id)
                    action = "paused"
                elif command == 'resume':
                    success = scheduler.resume_job(job_id)
                    action = "resumed"
                elif command == 'trigger':
                    success = scheduler.trigger_job(job_id)
                    action = "triggered"
                elif command == 'delete':
                    confirm = input(f"Are you sure you want to delete job {job_id}? (y/N): ").strip().lower()
                    if confirm == 'y':
                        success = scheduler.delete_job(job_id)
                        action = "deleted"
                    else:
                        print("❌ Cancelled")
                        continue
                
                if success:
                    print(f"✅ Job {action}: {job_id}")
                else:
                    print(f"❌ Failed to {command} job: {job_id}")
                    
            elif command == 'status':
                status = scheduler.get_status()
                stats = status.get('statistics', {})
                
                print(f"\n📊 Scheduler Status:")
                print(f"   Running: {'✅ Yes' if status['running'] else '❌ No'}")
                print(f"   Active Workers: {status['active_workers']}")
                print(f"   Check Interval: {status['check_interval']}s")
                
                print(f"\n📈 Statistics:")
                print(f"   Total Jobs: {stats.get('total_jobs', 0)}")
                print(f"   Active Jobs: {stats.get('active_jobs', 0)}")
                print(f"   Paused Jobs: {stats.get('paused_jobs', 0)}")
                print(f"   Total Executions: {stats.get('total_executions', 0)}")
                print(f"   Success Rate: {(stats.get('successful_executions', 0) / max(stats.get('total_executions', 1), 1) * 100):.1f}%")
                
            elif command == 'help':
                continue  # Shows the help menu again
                
            elif command:
                print(f"❌ Unknown command: {command}")
                
        except (KeyboardInterrupt, EOFError):
            print("\n👋 Goodbye!")
            break

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Job Management CLI")
    parser.add_argument('--config', default='config.yaml', help='Configuration file path')
    parser.add_argument('command', nargs='?', help='Command to run (list, show, create, etc.)')
    parser.add_argument('args', nargs='*', help='Command arguments')
    
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Load configuration
    if not os.path.exists(args.config):
        print(f"❌ Configuration file not found: {args.config}")
        sys.exit(1)
    
    config = load_config(args.config)
    
    # Create database manager and scheduler
    try:
        db_manager = create_database_manager(config)
        scheduler = DatabaseJobScheduler(db_manager)
        
        print("🔧 Job Management Tool")
        print(f"Database: {type(db_manager.adapter).__name__}")
        
        if args.command:
            # Command mode
            if args.command == 'list':
                jobs = scheduler.list_jobs()
                print_jobs_table(jobs)
                
            elif args.command == 'show' and args.args:
                job_id = args.args[0]
                job = scheduler.get_job(job_id)
                if job:
                    executions = scheduler.job_manager.get_job_executions(job.job_id, limit=10)
                    print_job_details(job, executions)
                else:
                    print(f"❌ Job not found: {job_id}")
                    
            elif args.command == 'create':
                if len(args.args) >= 3:
                    name, job_type, schedule = args.args[:3]
                    if job_type == "paper_fetch":
                        create_paper_fetch_job(scheduler, name, schedule, config)
                    else:
                        job_id = scheduler.create_job(name, job_type, schedule, {})
                        if job_id:
                            print(f"✅ Created job: {name} ({job_id})")
                else:
                    print("❌ Usage: manage_jobs.py create <name> <type> <schedule>")
                    
            elif args.command in ['pause', 'resume', 'trigger', 'delete'] and args.args:
                job_id = args.args[0]
                
                if args.command == 'pause':
                    success = scheduler.pause_job(job_id)
                elif args.command == 'resume':
                    success = scheduler.resume_job(job_id)
                elif args.command == 'trigger':
                    success = scheduler.trigger_job(job_id)
                elif args.command == 'delete':
                    success = scheduler.delete_job(job_id)
                
                if success:
                    print(f"✅ Job {args.command}ed: {job_id}")
                else:
                    print(f"❌ Failed to {args.command} job: {job_id}")
                    
            elif args.command == 'status':
                status = scheduler.get_status()
                stats = status.get('statistics', {})
                
                print(f"📊 Scheduler Status: {'Running' if status['running'] else 'Stopped'}")
                print(f"📈 Jobs: {stats.get('active_jobs', 0)} active, {stats.get('total_jobs', 0)} total")
                print(f"📊 Executions: {stats.get('total_executions', 0)} total, {(stats.get('successful_executions', 0) / max(stats.get('total_executions', 1), 1) * 100):.1f}% success rate")
                
            else:
                print(f"❌ Unknown command or missing arguments: {args.command}")
                print("Available commands: list, show <id>, create <name> <type> <schedule>, pause <id>, resume <id>, trigger <id>, delete <id>, status")
        else:
            # Interactive mode
            interactive_mode(scheduler)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()