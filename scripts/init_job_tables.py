#!/usr/bin/env python3
"""
Initialize job tables in the database
Creates the necessary tables for the job scheduling system
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from database.database_adapter import create_database_manager

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

def create_sqlite_tables(db_path: str):
    """Create job tables in SQLite"""
    import sqlite3
    
    with sqlite3.connect(db_path) as conn:
        print("Creating job tables in SQLite...")
        
        # Create jobs table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                job_type TEXT NOT NULL CHECK (job_type IN ('paper_fetch', 'maintenance', 'custom')),
                schedule_expression TEXT NOT NULL,
                config TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'paused', 'deleted')),
                description TEXT DEFAULT '',
                timeout_seconds INTEGER DEFAULT 3600,
                retry_count INTEGER DEFAULT 3,
                retry_delay_seconds INTEGER DEFAULT 300,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_execution TIMESTAMP NULL,
                next_execution TIMESTAMP NULL
            )
        """)
        
        # Create job executions table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS job_executions (
                execution_id TEXT PRIMARY KEY,
                job_id TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'success', 'failed', 'cancelled', 'timeout')),
                started_at TIMESTAMP NULL,
                finished_at TIMESTAMP NULL,
                duration_seconds REAL NULL,
                result TEXT NULL,
                error_message TEXT NULL,
                retry_attempt INTEGER DEFAULT 0,
                logs TEXT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (job_id) REFERENCES jobs (job_id) ON DELETE CASCADE
            )
        """)
        
        # Create indexes
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status)",
            "CREATE INDEX IF NOT EXISTS idx_jobs_job_type ON jobs(job_type)", 
            "CREATE INDEX IF NOT EXISTS idx_jobs_next_execution ON jobs(next_execution)",
            "CREATE INDEX IF NOT EXISTS idx_jobs_status_next_execution ON jobs(status, next_execution)",
            "CREATE INDEX IF NOT EXISTS idx_job_executions_job_id ON job_executions(job_id)",
            "CREATE INDEX IF NOT EXISTS idx_job_executions_status ON job_executions(status)",
            "CREATE INDEX IF NOT EXISTS idx_job_executions_created_at ON job_executions(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_job_executions_job_status ON job_executions(job_id, status)"
        ]
        
        for index_sql in indexes:
            conn.execute(index_sql)
        
        conn.commit()
        print("✅ SQLite job tables created successfully")

def show_supabase_instructions():
    """Show instructions for setting up Supabase tables"""
    return """
📋 Supabase Setup Instructions:

1. Go to your Supabase project dashboard
2. Click on "SQL Editor" in the left sidebar
3. Click "New Query"
4. Copy and paste the SQL from: scripts/supabase_job_schema.sql
5. Click "Run" to execute the SQL

OR

Copy and run this simplified SQL:
----------------------------------------

-- Create jobs table
CREATE TABLE IF NOT EXISTS jobs (
    job_id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    name TEXT NOT NULL,
    job_type TEXT NOT NULL CHECK (job_type IN ('paper_fetch', 'maintenance', 'custom')),
    schedule_expression TEXT NOT NULL,
    config JSONB NOT NULL DEFAULT '{}'::jsonb,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'paused', 'deleted')),
    description TEXT DEFAULT '',
    timeout_seconds INTEGER DEFAULT 3600,
    retry_count INTEGER DEFAULT 3,
    retry_delay_seconds INTEGER DEFAULT 300,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_execution TIMESTAMP WITH TIME ZONE NULL,
    next_execution TIMESTAMP WITH TIME ZONE NULL
);

-- Create job executions table
CREATE TABLE IF NOT EXISTS job_executions (
    execution_id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    job_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'success', 'failed', 'cancelled', 'timeout')),
    started_at TIMESTAMP WITH TIME ZONE NULL,
    finished_at TIMESTAMP WITH TIME ZONE NULL,
    duration_seconds REAL NULL,
    result JSONB NULL DEFAULT '{}'::jsonb,
    error_message TEXT NULL,
    retry_attempt INTEGER DEFAULT 0,
    logs TEXT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    FOREIGN KEY (job_id) REFERENCES jobs (job_id) ON DELETE CASCADE
);

-- Enable Row Level Security and create policies
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE job_executions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow anonymous access on jobs" ON jobs FOR ALL TO anon, authenticated USING (true) WITH CHECK (true);
CREATE POLICY "Allow anonymous access on job_executions" ON job_executions FOR ALL TO anon, authenticated USING (true) WITH CHECK (true);

----------------------------------------

After running the SQL, your job tables will be ready!
"""

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Initialize job tables")
    parser.add_argument('--config', default='config.yaml', help='Configuration file path')
    parser.add_argument('--force', action='store_true', help='Force recreation of tables')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Load environment variables
    load_dotenv()
    
    # Load configuration
    if not os.path.exists(args.config):
        print(f"Configuration file not found: {args.config}")
        sys.exit(1)
    
    config = load_config(args.config)
    
    # Create database manager
    try:
        db_manager = create_database_manager(config)
        
        # Check database type
        if hasattr(db_manager.adapter, 'client') and hasattr(db_manager.adapter.client, 'client'):
            # Supabase
            print("📋 Supabase Database Detected")
            print("=" * 60)
            print(show_supabase_instructions())
            print("=" * 60)
            
        else:
            # SQLite
            print("📋 SQLite Database Detected")
            db_path = db_manager.adapter.db_path
            create_sqlite_tables(db_path)
            
            # Test the tables
            print("\n🧪 Testing table creation...")
            from jobs.job_manager import JobManager
            job_manager = JobManager(db_manager)
            
            stats = job_manager.get_job_statistics()
            print(f"✅ Job tables ready! Current stats: {stats}")
            
    except Exception as e:
        print(f"❌ Error initializing job tables: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()