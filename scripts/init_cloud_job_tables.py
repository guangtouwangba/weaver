#!/usr/bin/env python3
"""
Initialize Cloud Job Tables
Creates the necessary tables for the cloud job system
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

def create_sqlite_tables(db_manager):
    """Create cloud job tables in SQLite"""
    import sqlite3
    
    conn = db_manager.adapter._get_connection()
    cursor = conn.cursor()
    
    print("Creating cloud job tables in SQLite...")
    
    try:
        # Read SQL schema
        schema_path = os.path.join(os.path.dirname(__file__), '..', 'backend', 'database', 'cloud_job_schema.sql')
        with open(schema_path, 'r') as f:
            sql_script = f.read()
        
        # Split into individual statements and execute
        statements = [stmt.strip() for stmt in sql_script.split(';') if stmt.strip()]
        
        for statement in statements:
            if statement:
                cursor.execute(statement)
        
        conn.commit()
        print("✅ SQLite cloud job tables created successfully")
        
        # Test by counting tables
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name LIKE 'cloud_%'")
        table_count = cursor.fetchone()[0]
        print(f"📊 Created {table_count} cloud job tables")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error creating SQLite tables: {e}")
        raise
    finally:
        cursor.close()

def show_supabase_instructions():
    """Show instructions for setting up Supabase tables"""
    return """
📋 Supabase Setup Instructions:

1. Go to your Supabase project dashboard
2. Click on "SQL Editor" in the left sidebar  
3. Click "New Query"
4. Copy and paste the SQL from: scripts/supabase_cloud_job_schema.sql
5. Click "Run" to execute the SQL

OR

Copy and run this essential SQL in Supabase SQL Editor:
----------------------------------------

-- Create cloud_jobs table
CREATE TABLE IF NOT EXISTS cloud_jobs (
    job_id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    name TEXT NOT NULL,
    job_type TEXT NOT NULL CHECK (job_type IN ('paper_fetch', 'maintenance', 'custom')),
    config JSONB NOT NULL DEFAULT '{}'::jsonb,
    status TEXT NOT NULL DEFAULT 'waiting' CHECK (status IN ('waiting', 'locked', 'success', 'failed', 'disabled')),
    description TEXT DEFAULT '',
    max_retries INTEGER DEFAULT 3,
    current_retries INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_execution TIMESTAMP WITH TIME ZONE NULL,
    locked_at TIMESTAMP WITH TIME ZONE NULL,
    locked_by TEXT NULL,
    lock_expires_at TIMESTAMP WITH TIME ZONE NULL
);

-- Create cloud_job_executions table
CREATE TABLE IF NOT EXISTS cloud_job_executions (
    execution_id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    job_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'running' CHECK (status IN ('running', 'success', 'failed')),
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    finished_at TIMESTAMP WITH TIME ZONE NULL,
    duration_seconds REAL NULL,
    result JSONB NULL DEFAULT '{}'::jsonb,
    error_message TEXT NULL,
    instance_id TEXT NULL,
    FOREIGN KEY (job_id) REFERENCES cloud_jobs (job_id) ON DELETE CASCADE
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_cloud_jobs_status ON cloud_jobs(status);
CREATE INDEX IF NOT EXISTS idx_cloud_jobs_status_retries ON cloud_jobs(status, current_retries, max_retries);

-- Enable Row Level Security
ALTER TABLE cloud_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE cloud_job_executions ENABLE ROW LEVEL SECURITY;

-- Create policies for access
CREATE POLICY "Allow anonymous access on cloud_jobs" ON cloud_jobs FOR ALL TO anon, authenticated USING (true) WITH CHECK (true);
CREATE POLICY "Allow anonymous access on cloud_job_executions" ON cloud_job_executions FOR ALL TO anon, authenticated USING (true) WITH CHECK (true);

----------------------------------------

After running the SQL, your cloud job tables will be ready!

For advanced features (atomic job picking), also run the stored functions from:
scripts/supabase_cloud_job_schema.sql
"""

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Initialize cloud job tables")
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
    
    # Auto-detect database provider
    if not config.get('database', {}).get('provider'):
        if os.getenv('SUPABASE_URL'):
            config.setdefault('database', {})['provider'] = 'supabase'
        else:
            config.setdefault('database', {})['provider'] = 'sqlite'
    
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
            
            # Test connection
            try:
                result = db_manager.adapter.client.client.table('cloud_jobs').select('COUNT(*)').execute()
                print("✅ Supabase connection test successful")
                print("💡 Tables may already exist - check your Supabase dashboard")
            except Exception as e:
                if 'relation "cloud_jobs" does not exist' in str(e):
                    print("⚠️  Cloud job tables not found - please run the SQL above")
                else:
                    print(f"⚠️  Connection test failed: {e}")
            
        else:
            # SQLite
            print("📋 SQLite Database Detected")
            create_sqlite_tables(db_manager)
            
            # Test the tables
            print("\n🧪 Testing table creation...")
            try:
                from jobs.job_picker import CloudJobPicker
                job_picker = CloudJobPicker(db_manager)
                stats = job_picker.get_job_statistics()
                print(f"✅ Cloud job tables ready! Current stats: {stats}")
            except Exception as e:
                print(f"⚠️  Warning: {e}")
            
    except Exception as e:
        print(f"❌ Error initializing cloud job tables: {e}")
        if "Invalid URL" in str(e):
            print("💡 Make sure your SUPABASE_URL is valid and starts with https://")
        elif "supabase library" in str(e):
            print("💡 Install Supabase library: pip install supabase==2.9.1")
        sys.exit(1)

if __name__ == "__main__":
    main()