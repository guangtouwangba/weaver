#!/usr/bin/env python3
"""
Cloud Job Manager
Simple tool to manage cloud jobs - create, list, monitor, and control jobs
"""

import os
import sys
import argparse
import logging
from datetime import datetime
from dotenv import load_dotenv

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from database.database_adapter import create_database_manager
from database.cloud_job_models import CloudJob, CloudJobType, CloudJobStatus
from jobs.job_picker import CloudJobPicker

def setup_logging():
    """Setup basic logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

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

def get_db_manager(config_path: str):
    """Get database manager"""
    load_dotenv()
    config = load_config(config_path)
    
    # Auto-detect database provider
    if not config.get('database', {}).get('provider'):
        if os.getenv('SUPABASE_URL'):
            config.setdefault('database', {})['provider'] = 'supabase'
        else:
            config.setdefault('database', {})['provider'] = 'sqlite'
    
    return create_database_manager(config)

def create_job(args):
    """Create a new job"""
    print(f"📝 Creating job: {args.name}")
    
    db_manager = get_db_manager(args.config)
    
    # Parse config from command line
    job_config = {}
    if args.job_config:
        for config_item in args.job_config:
            if '=' in config_item:
                key, value = config_item.split('=', 1)
                job_config[key] = value
    
    # Default config based on job type
    if args.type == 'paper_fetch':
        job_config.setdefault('config_path', 'config.yaml')
        job_config.setdefault('max_papers', 100)
    elif args.type == 'maintenance':
        job_config.setdefault('cleanup_days', 30)
        job_config.setdefault('cleanup_executions', True)
    
    # Create job
    job = CloudJob(
        name=args.name,
        job_type=CloudJobType(args.type),
        config=job_config,
        description=args.description or f"{args.type} job created via CLI",
        max_retries=args.max_retries
    )
    
    # Save to database
    try:
        if hasattr(db_manager.adapter, 'client') and hasattr(db_manager.adapter.client, 'client'):
            # Supabase
            db_manager.adapter.client.client.table('cloud_jobs').insert(job.to_dict()).execute()
        else:
            # SQLite
            conn = db_manager.adapter._get_connection()
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
        
        print(f"✅ Job created successfully: {job.job_id}")
        print(f"   Name: {job.name}")
        print(f"   Type: {job.job_type.value}")
        print(f"   Config: {job.config}")
        
    except Exception as e:
        print(f"❌ Failed to create job: {e}")
        sys.exit(1)

def list_jobs(args):
    """List all jobs"""
    print("📋 Listing jobs...")
    
    db_manager = get_db_manager(args.config)
    
    try:
        if hasattr(db_manager.adapter, 'client') and hasattr(db_manager.adapter.client, 'client'):
            # Supabase
            query = db_manager.adapter.client.client.table('cloud_jobs').select('*').order('created_at')
            
            if args.status:
                query = query.eq('status', args.status)
                
            result = query.execute()
            jobs_data = result.data
        else:
            # SQLite
            conn = db_manager.adapter._get_connection()
            cursor = conn.cursor()
            
            if args.status:
                cursor.execute("SELECT * FROM cloud_jobs WHERE status = ? ORDER BY created_at", (args.status,))
            else:
                cursor.execute("SELECT * FROM cloud_jobs ORDER BY created_at")
            
            columns = [desc[0] for desc in cursor.description]
            jobs_data = [dict(zip(columns, row)) for row in cursor.fetchall()]
            cursor.close()
        
        if not jobs_data:
            print("ℹ️  No jobs found")
            return
        
        print(f"\n📊 Found {len(jobs_data)} jobs:")
        print("-" * 80)
        
        for job_data in jobs_data:
            status_icon = {
                'waiting': '⏳',
                'locked': '🔒',
                'success': '✅',
                'failed': '❌',
                'disabled': '🚫'
            }.get(job_data['status'], '❓')
            
            print(f"{status_icon} {job_data['name']} ({job_data['job_type']})")
            print(f"   ID: {job_data['job_id']}")
            print(f"   Status: {job_data['status']}")
            print(f"   Retries: {job_data['current_retries']}/{job_data['max_retries']}")
            print(f"   Created: {job_data['created_at']}")
            if job_data.get('last_execution'):
                print(f"   Last Execution: {job_data['last_execution']}")
            print()
        
    except Exception as e:
        print(f"❌ Failed to list jobs: {e}")
        sys.exit(1)

def show_job(args):
    """Show detailed job information"""
    print(f"🔍 Job details: {args.job_id}")
    
    db_manager = get_db_manager(args.config)
    
    try:
        if hasattr(db_manager.adapter, 'client') and hasattr(db_manager.adapter.client, 'client'):
            # Supabase
            result = db_manager.adapter.client.client.table('cloud_jobs').select('*').eq('job_id', args.job_id).execute()
            jobs_data = result.data
            
            # Get executions
            exec_result = db_manager.adapter.client.client.table('cloud_job_executions').select('*').eq('job_id', args.job_id).order('started_at', desc=True).limit(10).execute()
            executions_data = exec_result.data
        else:
            # SQLite
            conn = db_manager.adapter._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM cloud_jobs WHERE job_id = ?", (args.job_id,))
            columns = [desc[0] for desc in cursor.description]
            row = cursor.fetchone()
            jobs_data = [dict(zip(columns, row))] if row else []
            
            cursor.execute("SELECT * FROM cloud_job_executions WHERE job_id = ? ORDER BY started_at DESC LIMIT 10", (args.job_id,))
            exec_columns = [desc[0] for desc in cursor.description]
            executions_data = [dict(zip(exec_columns, row)) for row in cursor.fetchall()]
            cursor.close()
        
        if not jobs_data:
            print(f"❌ Job not found: {args.job_id}")
            return
        
        job_data = jobs_data[0]
        
        # Display job details
        print("\n📄 Job Information:")
        print("-" * 40)
        print(f"Name: {job_data['name']}")
        print(f"ID: {job_data['job_id']}")
        print(f"Type: {job_data['job_type']}")
        print(f"Status: {job_data['status']}")
        print(f"Description: {job_data.get('description', 'N/A')}")
        print(f"Retries: {job_data['current_retries']}/{job_data['max_retries']}")
        print(f"Created: {job_data['created_at']}")
        if job_data.get('last_execution'):
            print(f"Last Execution: {job_data['last_execution']}")
        if job_data.get('locked_by'):
            print(f"Locked By: {job_data['locked_by']}")
            print(f"Lock Expires: {job_data.get('lock_expires_at', 'N/A')}")
        
        # Display config
        import json
        config = json.loads(job_data['config']) if isinstance(job_data['config'], str) else job_data['config']
        print(f"\n⚙️  Configuration:")
        for key, value in config.items():
            print(f"  {key}: {value}")
        
        # Display recent executions
        if executions_data:
            print(f"\n📈 Recent Executions ({len(executions_data)}):")
            print("-" * 40)
            for exec_data in executions_data:
                status_icon = {'running': '🏃', 'success': '✅', 'failed': '❌'}.get(exec_data['status'], '❓')
                print(f"{status_icon} {exec_data['execution_id'][:8]}... - {exec_data['status']}")
                print(f"   Started: {exec_data['started_at']}")
                if exec_data.get('finished_at'):
                    print(f"   Finished: {exec_data['finished_at']}")
                    print(f"   Duration: {exec_data.get('duration_seconds', 0):.2f}s")
                if exec_data.get('error_message'):
                    print(f"   Error: {exec_data['error_message']}")
                print()
        else:
            print("\n📈 No executions found")
        
    except Exception as e:
        print(f"❌ Failed to show job: {e}")
        sys.exit(1)

def show_stats(args):
    """Show job statistics"""
    print("📊 Job Statistics")
    
    db_manager = get_db_manager(args.config)
    job_picker = CloudJobPicker(db_manager)
    
    try:
        stats = job_picker.get_job_statistics()
        
        print("-" * 30)
        print(f"Total Jobs: {stats.get('total_jobs', 0)}")
        print(f"⏳ Waiting: {stats.get('waiting_jobs', 0)}")
        print(f"🔒 Locked: {stats.get('locked_jobs', 0)}")
        print(f"✅ Success: {stats.get('success_jobs', 0)}")
        print(f"❌ Failed: {stats.get('failed_jobs', 0)}")
        print(f"🚫 Disabled: {stats.get('disabled_jobs', 0)}")
        print(f"\nCalculated at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        
    except Exception as e:
        print(f"❌ Failed to get statistics: {e}")
        sys.exit(1)

def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(description="Cloud Job Manager")
    parser.add_argument('--config', default='config.yaml', help='Configuration file path')
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Create job command
    create_parser = subparsers.add_parser('create', help='Create a new job')
    create_parser.add_argument('name', help='Job name')
    create_parser.add_argument('type', choices=['paper_fetch', 'maintenance', 'custom'], help='Job type')
    create_parser.add_argument('--description', help='Job description')
    create_parser.add_argument('--max-retries', type=int, default=3, help='Maximum retry attempts')
    create_parser.add_argument('--job-config', nargs='*', help='Job configuration (key=value pairs)')
    
    # List jobs command
    list_parser = subparsers.add_parser('list', help='List jobs')
    list_parser.add_argument('--status', choices=['waiting', 'locked', 'success', 'failed', 'disabled'], help='Filter by status')
    
    # Show job command
    show_parser = subparsers.add_parser('show', help='Show job details')
    show_parser.add_argument('job_id', help='Job ID')
    
    # Stats command
    subparsers.add_parser('stats', help='Show job statistics')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    setup_logging()
    
    if args.command == 'create':
        create_job(args)
    elif args.command == 'list':
        list_jobs(args)
    elif args.command == 'show':
        show_job(args)
    elif args.command == 'stats':
        show_stats(args)

if __name__ == "__main__":
    main()