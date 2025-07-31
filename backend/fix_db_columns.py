#!/usr/bin/env python3
"""
Quick fix script to add missing database columns
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from database.database import get_database
    from sqlalchemy import text
    
    def fix_database():
        """Add missing columns to job_runs table"""
        db_manager = get_database()
        
        try:
            with db_manager.get_session() as session:
                print("Adding missing columns to job_runs table...")
                
                # Add missing columns with proper defaults
                session.execute(text("ALTER TABLE job_runs ADD COLUMN IF NOT EXISTS task_id VARCHAR(255)"))
                session.execute(text("ALTER TABLE job_runs ADD COLUMN IF NOT EXISTS progress_percentage INTEGER DEFAULT 0"))
                session.execute(text("ALTER TABLE job_runs ADD COLUMN IF NOT EXISTS current_step VARCHAR(255)"))
                session.execute(text("ALTER TABLE job_runs ADD COLUMN IF NOT EXISTS manual_trigger BOOLEAN DEFAULT false"))
                session.execute(text("ALTER TABLE job_runs ADD COLUMN IF NOT EXISTS user_params JSONB"))
                
                # Update existing records to have default values
                session.execute(text("UPDATE job_runs SET progress_percentage = 0 WHERE progress_percentage IS NULL"))
                session.execute(text("UPDATE job_runs SET manual_trigger = false WHERE manual_trigger IS NULL"))
                
                # Create useful indexes
                session.execute(text("CREATE INDEX IF NOT EXISTS idx_job_runs_task_id ON job_runs(task_id)"))
                session.execute(text("CREATE INDEX IF NOT EXISTS idx_job_runs_manual_trigger ON job_runs(manual_trigger)"))
                session.execute(text("CREATE INDEX IF NOT EXISTS idx_job_runs_progress ON job_runs(progress_percentage)"))
                
                session.commit()
                print("✅ Database columns added successfully!")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
        return True

    if __name__ == "__main__":
        success = fix_database()
        exit(0 if success else 1)
        
except ImportError as e:
    print(f"Import error: {e}")
    print("This script must be run from the backend directory with proper dependencies installed")
    exit(1)