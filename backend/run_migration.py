#!/usr/bin/env python3
"""
Simple script to run database migration
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.database import get_database
from sqlalchemy import text

def run_migration():
    """Run the migration to add missing columns"""
    db_manager = get_database()
    
    try:
        with db_manager.get_session() as session:
            # Add task_id column
            session.execute(text("ALTER TABLE job_runs ADD COLUMN IF NOT EXISTS task_id VARCHAR(255)"))
            
            # Add progress tracking columns
            session.execute(text("ALTER TABLE job_runs ADD COLUMN IF NOT EXISTS progress_percentage INTEGER DEFAULT 0"))
            session.execute(text("ALTER TABLE job_runs ADD COLUMN IF NOT EXISTS current_step VARCHAR(255)"))
            
            # Add manual trigger tracking columns
            session.execute(text("ALTER TABLE job_runs ADD COLUMN IF NOT EXISTS manual_trigger BOOLEAN DEFAULT false"))
            session.execute(text("ALTER TABLE job_runs ADD COLUMN IF NOT EXISTS user_params JSONB"))
            
            # Create indexes
            session.execute(text("CREATE INDEX IF NOT EXISTS idx_job_runs_task_id ON job_runs(task_id)"))
            session.execute(text("CREATE INDEX IF NOT EXISTS idx_job_runs_manual_trigger ON job_runs(manual_trigger)"))
            
            session.commit()
            print("✅ Migration completed successfully")
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise

if __name__ == "__main__":
    run_migration() 