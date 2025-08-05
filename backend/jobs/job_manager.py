#!/usr/bin/env python3
"""
Job Manager for database-driven job scheduling
Handles CRUD operations for jobs and job executions
"""

import os
import sys
import logging
import sqlite3
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
import json
from croniter import croniter

# Add backend path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database.database_adapter import DatabaseManager
from database.job_models import Job, JobExecution, JobStatus, JobType, ExecutionStatus

logger = logging.getLogger(__name__)

class JobManager:
    """Manages jobs and job executions in the database"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self._init_job_tables()
    
    def _init_job_tables(self):
        """Initialize job tables if they don't exist"""
        try:
            if hasattr(self.db_manager.adapter, 'client') and hasattr(self.db_manager.adapter.client, 'client'):
                # Supabase - tables should be created via SQL editor
                logger.info("Using Supabase - job tables should be created via SQL editor")
                self._test_job_tables_exist()
            else:
                # SQLite - create tables directly
                self._create_sqlite_tables()
        except Exception as e:
            logger.error(f"Failed to initialize job tables: {e}")
            raise
    
    def _test_job_tables_exist(self):
        """Test if job tables exist in Supabase"""
        try:
            # Try to query the jobs table
            if hasattr(self.db_manager.adapter, 'client'):
                result = self.db_manager.adapter.client.client.table("jobs").select("count", count="exact").limit(1).execute()
                logger.info("Job tables exist in Supabase")
        except Exception as e:
            logger.warning(f"Job tables may not exist in Supabase: {e}")
            logger.info("Please run the job_schema.sql in your Supabase SQL editor")
    
    def _create_sqlite_tables(self):
        """Create job tables in SQLite"""
        if hasattr(self.db_manager.adapter, 'db_path'):
            with sqlite3.connect(self.db_manager.adapter.db_path) as conn:
                # Read and execute the schema
                schema_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'job_schema.sql')
                if os.path.exists(schema_path):
                    with open(schema_path, 'r') as f:
                        schema_sql = f.read()
                    
                    # Extract only SQLite-compatible parts
                    sqlite_statements = []
                    for statement in schema_sql.split(';'):
                        statement = statement.strip()
                        if (statement and 
                            not statement.startswith('DO $$') and
                            'TIMESTAMP WITH TIME ZONE' not in statement and
                            'gen_random_uuid()' not in statement and
                            'JSONB' not in statement):
                            # Convert PostgreSQL specific syntax to SQLite
                            statement = statement.replace('JSONB', 'TEXT')
                            statement = statement.replace('TIMESTAMP WITH TIME ZONE', 'TIMESTAMP')
                            sqlite_statements.append(statement)
                    
                    for statement in sqlite_statements:
                        if statement:
                            try:
                                conn.execute(statement)
                            except sqlite3.Error as e:
                                if "already exists" not in str(e).lower():
                                    logger.warning(f"SQL statement failed: {e}")
                    
                    conn.commit()
                    logger.info("SQLite job tables created successfully")
                else:
                    # Fallback: create tables manually
                    self._create_sqlite_tables_manual(conn)
    
    def _create_sqlite_tables_manual(self, conn):
        """Create job tables manually for SQLite"""
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
            "CREATE INDEX IF NOT EXISTS idx_job_executions_job_id ON job_executions(job_id)",
            "CREATE INDEX IF NOT EXISTS idx_job_executions_status ON job_executions(status)",
            "CREATE INDEX IF NOT EXISTS idx_job_executions_created_at ON job_executions(created_at)"
        ]
        
        for index_sql in indexes:
            conn.execute(index_sql)
        
        conn.commit()
        logger.info("SQLite job tables created manually")
    
    # Job CRUD operations
    
    def create_job(self, job: Job) -> bool:
        """Create a new job"""
        try:
            # Calculate next execution time
            job.next_execution = self._calculate_next_execution(job.schedule_expression)
            
            if hasattr(self.db_manager.adapter, 'client') and hasattr(self.db_manager.adapter.client, 'client'):
                # Supabase
                job_data = job.to_dict()
                # Convert config to proper JSON for Supabase
                if isinstance(job_data['config'], str):
                    job_data['config'] = json.loads(job_data['config'])
                
                result = self.db_manager.adapter.client.client.table("jobs").insert(job_data).execute()
                success = len(result.data) > 0
            else:
                # SQLite
                with sqlite3.connect(self.db_manager.adapter.db_path) as conn:
                    job_data = job.to_dict()
                    conn.execute("""
                        INSERT INTO jobs (job_id, name, job_type, schedule_expression, config, status, 
                                        description, timeout_seconds, retry_count, retry_delay_seconds,
                                        created_at, updated_at, next_execution)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        job_data['job_id'], job_data['name'], job_data['job_type'],
                        job_data['schedule_expression'], job_data['config'], job_data['status'],
                        job_data['description'], job_data['timeout_seconds'], job_data['retry_count'],
                        job_data['retry_delay_seconds'], job_data['created_at'], job_data['updated_at'],
                        job_data['next_execution']
                    ))
                    conn.commit()
                    success = True
            
            logger.info(f"Created job: {job.name} ({job.job_id})")
            return success
            
        except Exception as e:
            logger.error(f"Failed to create job {job.name}: {e}")
            return False
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get a job by ID"""
        try:
            if hasattr(self.db_manager.adapter, 'client') and hasattr(self.db_manager.adapter.client, 'client'):
                # Supabase
                result = self.db_manager.adapter.client.client.table("jobs").select("*").eq("job_id", job_id).limit(1).execute()
                if result.data:
                    return Job.from_dict(result.data[0])
            else:
                # SQLite
                with sqlite3.connect(self.db_manager.adapter.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,))
                    row = cursor.fetchone()
                    if row:
                        return Job.from_dict(dict(row))
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get job {job_id}: {e}")
            return None
    
    def update_job(self, job: Job) -> bool:
        """Update an existing job"""
        try:
            job.updated_at = datetime.utcnow()
            # Recalculate next execution if schedule changed
            job.next_execution = self._calculate_next_execution(job.schedule_expression)
            
            if hasattr(self.db_manager.adapter, 'client') and hasattr(self.db_manager.adapter.client, 'client'):
                # Supabase
                job_data = job.to_dict()
                if isinstance(job_data['config'], str):
                    job_data['config'] = json.loads(job_data['config'])
                
                result = self.db_manager.adapter.client.client.table("jobs").update(job_data).eq("job_id", job.job_id).execute()
                success = len(result.data) > 0
            else:
                # SQLite
                with sqlite3.connect(self.db_manager.adapter.db_path) as conn:
                    job_data = job.to_dict()
                    conn.execute("""
                        UPDATE jobs SET name=?, job_type=?, schedule_expression=?, config=?, status=?,
                                      description=?, timeout_seconds=?, retry_count=?, retry_delay_seconds=?,
                                      updated_at=?, next_execution=?
                        WHERE job_id=?
                    """, (
                        job_data['name'], job_data['job_type'], job_data['schedule_expression'],
                        job_data['config'], job_data['status'], job_data['description'],
                        job_data['timeout_seconds'], job_data['retry_count'], job_data['retry_delay_seconds'],
                        job_data['updated_at'], job_data['next_execution'], job.job_id
                    ))
                    success = conn.rowcount > 0
                    conn.commit()
            
            logger.info(f"Updated job: {job.name} ({job.job_id})")
            return success
            
        except Exception as e:
            logger.error(f"Failed to update job {job.job_id}: {e}")
            return False
    
    def delete_job(self, job_id: str) -> bool:
        """Delete a job (soft delete by setting status to deleted)"""
        try:
            if hasattr(self.db_manager.adapter, 'client') and hasattr(self.db_manager.adapter.client, 'client'):
                # Supabase
                result = self.db_manager.adapter.client.client.table("jobs").update({
                    'status': 'deleted',
                    'updated_at': datetime.utcnow().isoformat()
                }).eq("job_id", job_id).execute()
                success = len(result.data) > 0
            else:
                # SQLite
                with sqlite3.connect(self.db_manager.adapter.db_path) as conn:
                    conn.execute("""
                        UPDATE jobs SET status='deleted', updated_at=CURRENT_TIMESTAMP
                        WHERE job_id=?
                    """, (job_id,))
                    success = conn.rowcount > 0
                    conn.commit()
            
            logger.info(f"Deleted job: {job_id}")
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete job {job_id}: {e}")
            return False
    
    def list_jobs(self, status: JobStatus = None, job_type: JobType = None, limit: int = None) -> List[Job]:
        """List jobs with optional filtering"""
        try:
            jobs = []
            
            if hasattr(self.db_manager.adapter, 'client') and hasattr(self.db_manager.adapter.client, 'client'):
                # Supabase
                query = self.db_manager.adapter.client.client.table("jobs").select("*")
                
                if status:
                    query = query.eq("status", status.value)
                if job_type:
                    query = query.eq("job_type", job_type.value)
                if limit:
                    query = query.limit(limit)
                
                query = query.order("created_at", desc=True)
                result = query.execute()
                
                for row in result.data:
                    jobs.append(Job.from_dict(row))
            else:
                # SQLite
                with sqlite3.connect(self.db_manager.adapter.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    
                    where_conditions = []
                    params = []
                    
                    if status:
                        where_conditions.append("status = ?")
                        params.append(status.value)
                    if job_type:
                        where_conditions.append("job_type = ?")
                        params.append(job_type.value)
                    
                    where_clause = " WHERE " + " AND ".join(where_conditions) if where_conditions else ""
                    limit_clause = f" LIMIT {limit}" if limit else ""
                    
                    query = f"SELECT * FROM jobs{where_clause} ORDER BY created_at DESC{limit_clause}"
                    cursor = conn.execute(query, params)
                    
                    for row in cursor.fetchall():
                        jobs.append(Job.from_dict(dict(row)))
            
            return jobs
            
        except Exception as e:
            logger.error(f"Failed to list jobs: {e}")
            return []
    
    def get_due_jobs(self) -> List[Job]:
        """Get jobs that are due for execution"""
        try:
            now = datetime.utcnow().isoformat()
            jobs = []
            
            if hasattr(self.db_manager.adapter, 'client') and hasattr(self.db_manager.adapter.client, 'client'):
                # Supabase
                result = self.db_manager.adapter.client.client.table("jobs").select("*").eq("status", "active").lte("next_execution", now).execute()
                
                for row in result.data:
                    jobs.append(Job.from_dict(row))
            else:
                # SQLite
                with sqlite3.connect(self.db_manager.adapter.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.execute("""
                        SELECT * FROM jobs 
                        WHERE status = 'active' AND next_execution <= ?
                        ORDER BY next_execution ASC
                    """, (now,))
                    
                    for row in cursor.fetchall():
                        jobs.append(Job.from_dict(dict(row)))
            
            return jobs
            
        except Exception as e:
            logger.error(f"Failed to get due jobs: {e}")
            return []
    
    # Job execution operations
    
    def create_execution(self, execution: JobExecution) -> bool:
        """Create a new job execution record"""
        try:
            if hasattr(self.db_manager.adapter, 'client') and hasattr(self.db_manager.adapter.client, 'client'):
                # Supabase
                execution_data = execution.to_dict()
                if isinstance(execution_data['result'], str):
                    execution_data['result'] = json.loads(execution_data['result'])
                
                result = self.db_manager.adapter.client.client.table("job_executions").insert(execution_data).execute()
                success = len(result.data) > 0
            else:
                # SQLite
                with sqlite3.connect(self.db_manager.adapter.db_path) as conn:
                    execution_data = execution.to_dict()
                    conn.execute("""
                        INSERT INTO job_executions (execution_id, job_id, status, started_at, finished_at,
                                                   duration_seconds, result, error_message, retry_attempt,
                                                   logs, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        execution_data['execution_id'], execution_data['job_id'], execution_data['status'],
                        execution_data['started_at'], execution_data['finished_at'], execution_data['duration_seconds'],
                        execution_data['result'], execution_data['error_message'], execution_data['retry_attempt'],
                        execution_data['logs'], execution_data['created_at']
                    ))
                    conn.commit()
                    success = True
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to create execution {execution.execution_id}: {e}")
            return False
    
    def update_execution(self, execution: JobExecution) -> bool:
        """Update a job execution record"""
        try:
            if hasattr(self.db_manager.adapter, 'client') and hasattr(self.db_manager.adapter.client, 'client'):
                # Supabase
                execution_data = execution.to_dict()
                if isinstance(execution_data['result'], str):
                    execution_data['result'] = json.loads(execution_data['result'])
                
                result = self.db_manager.adapter.client.client.table("job_executions").update(execution_data).eq("execution_id", execution.execution_id).execute()
                success = len(result.data) > 0
            else:
                # SQLite
                with sqlite3.connect(self.db_manager.adapter.db_path) as conn:
                    execution_data = execution.to_dict()
                    conn.execute("""
                        UPDATE job_executions SET status=?, started_at=?, finished_at=?, duration_seconds=?,
                                                 result=?, error_message=?, retry_attempt=?, logs=?
                        WHERE execution_id=?
                    """, (
                        execution_data['status'], execution_data['started_at'], execution_data['finished_at'],
                        execution_data['duration_seconds'], execution_data['result'], execution_data['error_message'],
                        execution_data['retry_attempt'], execution_data['logs'], execution.execution_id
                    ))
                    success = conn.rowcount > 0
                    conn.commit()
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to update execution {execution.execution_id}: {e}")
            return False
    
    def get_job_executions(self, job_id: str, limit: int = 10) -> List[JobExecution]:
        """Get execution history for a job"""
        try:
            executions = []
            
            if hasattr(self.db_manager.adapter, 'client') and hasattr(self.db_manager.adapter.client, 'client'):
                # Supabase
                result = self.db_manager.adapter.client.client.table("job_executions").select("*").eq("job_id", job_id).order("created_at", desc=True).limit(limit).execute()
                
                for row in result.data:
                    executions.append(JobExecution.from_dict(row))
            else:
                # SQLite
                with sqlite3.connect(self.db_manager.adapter.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.execute("""
                        SELECT * FROM job_executions
                        WHERE job_id = ?
                        ORDER BY created_at DESC
                        LIMIT ?
                    """, (job_id, limit))
                    
                    for row in cursor.fetchall():
                        executions.append(JobExecution.from_dict(dict(row)))
            
            return executions
            
        except Exception as e:
            logger.error(f"Failed to get executions for job {job_id}: {e}")
            return []
    
    def update_job_last_execution(self, job_id: str, execution_time: datetime = None):
        """Update the last execution time for a job and calculate next execution"""
        try:
            job = self.get_job(job_id)
            if not job:
                return False
            
            job.last_execution = execution_time or datetime.utcnow()
            job.next_execution = self._calculate_next_execution(job.schedule_expression, job.last_execution)
            
            return self.update_job(job)
            
        except Exception as e:
            logger.error(f"Failed to update job last execution {job_id}: {e}")
            return False
    
    # Utility methods
    
    def _calculate_next_execution(self, schedule_expression: str, base_time: datetime = None) -> datetime:
        """Calculate next execution time based on cron expression"""
        try:
            base = base_time or datetime.utcnow()
            cron = croniter(schedule_expression, base)
            return cron.get_next(datetime)
        except Exception as e:
            logger.error(f"Failed to calculate next execution for '{schedule_expression}': {e}")
            # Default to 1 hour from now
            return (base_time or datetime.utcnow()) + timedelta(hours=1)
    
    def get_job_statistics(self) -> Dict[str, Any]:
        """Get job system statistics"""
        try:
            stats = {
                'total_jobs': 0,
                'active_jobs': 0,
                'paused_jobs': 0,
                'total_executions': 0,
                'successful_executions': 0,
                'failed_executions': 0,
                'recent_executions': []
            }
            
            if hasattr(self.db_manager.adapter, 'client') and hasattr(self.db_manager.adapter.client, 'client'):
                # Supabase
                # Get job counts
                total_result = self.db_manager.adapter.client.client.table("jobs").select("count", count="exact").neq("status", "deleted").execute()
                stats['total_jobs'] = total_result.count or 0
                
                active_result = self.db_manager.adapter.client.client.table("jobs").select("count", count="exact").eq("status", "active").execute()
                stats['active_jobs'] = active_result.count or 0
                
                paused_result = self.db_manager.adapter.client.client.table("jobs").select("count", count="exact").eq("status", "paused").execute()
                stats['paused_jobs'] = paused_result.count or 0
                
                # Get execution counts
                exec_total_result = self.db_manager.adapter.client.client.table("job_executions").select("count", count="exact").execute()
                stats['total_executions'] = exec_total_result.count or 0
                
                success_result = self.db_manager.adapter.client.client.table("job_executions").select("count", count="exact").eq("status", "success").execute()
                stats['successful_executions'] = success_result.count or 0
                
                failed_result = self.db_manager.adapter.client.client.table("job_executions").select("count", count="exact").eq("status", "failed").execute()
                stats['failed_executions'] = failed_result.count or 0
                
            else:
                # SQLite
                with sqlite3.connect(self.db_manager.adapter.db_path) as conn:
                    # Job counts
                    cursor = conn.execute("SELECT COUNT(*) FROM jobs WHERE status != 'deleted'")
                    stats['total_jobs'] = cursor.fetchone()[0]
                    
                    cursor = conn.execute("SELECT COUNT(*) FROM jobs WHERE status = 'active'")
                    stats['active_jobs'] = cursor.fetchone()[0]
                    
                    cursor = conn.execute("SELECT COUNT(*) FROM jobs WHERE status = 'paused'")
                    stats['paused_jobs'] = cursor.fetchone()[0]
                    
                    # Execution counts
                    cursor = conn.execute("SELECT COUNT(*) FROM job_executions")
                    stats['total_executions'] = cursor.fetchone()[0]
                    
                    cursor = conn.execute("SELECT COUNT(*) FROM job_executions WHERE status = 'success'")
                    stats['successful_executions'] = cursor.fetchone()[0]
                    
                    cursor = conn.execute("SELECT COUNT(*) FROM job_executions WHERE status = 'failed'")
                    stats['failed_executions'] = cursor.fetchone()[0]
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get job statistics: {e}")
            return {
                'total_jobs': 0,
                'active_jobs': 0,
                'paused_jobs': 0,
                'total_executions': 0,
                'successful_executions': 0,
                'failed_executions': 0,
                'recent_executions': []
            }