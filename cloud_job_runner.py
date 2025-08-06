#!/usr/bin/env python3
"""
Cloud Job Runner
Simple, stateless job execution script for cloud environments

This script:
1. Connects to the cloud database
2. Picks up one available job atomically
3. Executes the job
4. Updates the result
5. Exits

Perfect for:
- AWS Lambda / Google Cloud Functions
- Kubernetes CronJobs  
- Docker container runs
- Cloud scheduled tasks
"""

import os
import sys
import logging
import argparse
import uuid
from datetime import datetime
from dotenv import load_dotenv

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from database.database_adapter import create_database_manager
from jobs.job_picker import CloudJobPicker
from jobs.simple_job_executor import SimpleJobExecutor

def setup_logging(level=logging.INFO):
    """Setup logging for cloud execution"""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Reduce noise from HTTP libraries
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('h11').setLevel(logging.WARNING)
    logging.getLogger('hpack').setLevel(logging.WARNING)
    logging.getLogger('hyperframe').setLevel(logging.WARNING)

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

def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description="Cloud Job Runner")
    parser.add_argument('--config', default='config.yaml', help='Configuration file path')
    parser.add_argument('--instance-id', help='Instance ID (auto-generated if not provided)')
    parser.add_argument('--lock-duration', type=int, default=30, help='Job lock duration in minutes')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    parser.add_argument('--dry-run', action='store_true', help='Show available jobs without executing')
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(log_level)
    
    logger = logging.getLogger(__name__)
    
    # Generate instance ID
    instance_id = args.instance_id or f"cloud-runner-{str(uuid.uuid4())[:8]}"
    
    logger.info(f"🚀 Cloud Job Runner starting - Instance: {instance_id}")
    logger.info(f"⚙️  Config: {args.config}, Lock duration: {args.lock_duration}m")
    
    try:
        # Load environment variables
        load_dotenv()
        
        # Load configuration
        if not os.path.exists(args.config):
            logger.error(f"❌ Configuration file not found: {args.config}")
            sys.exit(1)
        
        config = load_config(args.config)
        
        # Ensure we use cloud database (Supabase for cloud deployment)
        if not config.get('database', {}).get('provider'):
            logger.warning("⚠️  Database provider not specified, trying to detect from environment...")
            if os.getenv('SUPABASE_URL'):
                config.setdefault('database', {})['provider'] = 'supabase'
                logger.info("🔍 Detected Supabase credentials, using Supabase")
            else:
                logger.error("❌ No cloud database configured. Please set SUPABASE_URL in environment.")
                sys.exit(1)
        
        # Create database manager
        db_manager = create_database_manager(config)
        logger.info(f"✅ Connected to database: {type(db_manager.adapter).__name__}")
        
        # Create job picker and executor
        job_picker = CloudJobPicker(db_manager, instance_id, args.lock_duration)
        job_executor = SimpleJobExecutor(db_manager, instance_id)
        
        # Get job statistics
        stats = job_picker.get_job_statistics()
        logger.info(f"📊 Job Statistics: {stats}")
        
        if args.dry_run:
            logger.info("🔍 Dry run mode - not executing jobs")
            if stats.get('waiting_jobs', 0) > 0:
                logger.info(f"✅ Found {stats['waiting_jobs']} jobs ready for execution")
            else:
                logger.info("ℹ️  No jobs available for execution")
            return
        
        # Pick next available job
        logger.info("🔍 Looking for available jobs...")
        job = job_picker.get_next_job()
        
        if not job:
            logger.info("ℹ️  No jobs available for execution")
            logger.info("💤 Exiting - nothing to do")
            return
        
        logger.info(f"🎯 Picked job: {job.name} ({job.job_type.value}) - ID: {job.job_id}")
        
        # Execute the job
        logger.info("⚡ Starting job execution...")
        start_time = datetime.utcnow()
        
        execution_result = job_executor.execute_job(job)
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        # Update job status based on execution result
        success = execution_result.get('success', False)
        
        if success:
            logger.info(f"✅ Job completed successfully in {duration:.2f}s")
            logger.info(f"📋 Result: {execution_result.get('result', {})}")
        else:
            logger.error(f"❌ Job failed after {duration:.2f}s")
            logger.error(f"💥 Error: {execution_result.get('error', 'Unknown error')}")
        
        # Complete job (update status and release lock)
        job_picker.complete_job(
            job, 
            success, 
            execution_result.get('result'),
            execution_result.get('error')
        )
        
        # Final status
        if success:
            logger.info(f"🎉 Job runner completed successfully - Instance: {instance_id}")
        else:
            logger.error(f"💔 Job runner completed with errors - Instance: {instance_id}")
            sys.exit(1)
    
    except KeyboardInterrupt:
        logger.warning("⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Fatal error in job runner: {e}")
        if args.verbose:
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main()