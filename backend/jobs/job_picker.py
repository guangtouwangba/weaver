#!/usr/bin/env python3
"""
Cloud Job Picker
Atomically selects and locks jobs for execution to avoid conflicts
"""

import os
import sys
import logging
import uuid
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

# Add backend path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database.database_adapter import DatabaseManager
from database.cloud_job_models import CloudJob, CloudJobStatus, CloudJobType

logger = logging.getLogger(__name__)

class CloudJobPicker:
    """Handles atomic job selection and locking for cloud execution"""
    
    def __init__(self, db_manager: DatabaseManager, instance_id: str = None, lock_duration_minutes: int = 30):
        self.db_manager = db_manager
        self.instance_id = instance_id or f"worker-{str(uuid.uuid4())[:8]}"
        self.lock_duration_minutes = lock_duration_minutes
        
        logger.info(f"CloudJobPicker initialized with instance_id: {self.instance_id}")
    
    def get_next_job(self) -> Optional[CloudJob]:
        """
        Atomically get and lock the next available job
        Returns None if no jobs are available
        """
        try:
            # First try to release any expired locks
            self._release_expired_locks()
            
            # Try to get next job based on database type
            if hasattr(self.db_manager.adapter, 'client') and hasattr(self.db_manager.adapter.client, 'client'):
                # Supabase - use stored function for atomic operation
                return self._get_next_job_supabase()
            else:
                # SQLite - use transaction with row locking simulation
                return self._get_next_job_sqlite()
                
        except Exception as e:
            logger.error(f"Error getting next job: {e}")
            return None
    
    def _get_next_job_supabase(self) -> Optional[CloudJob]:
        """Get next job using Supabase - fallback to basic query if stored function not available"""
        try:
            # Try to use basic query instead of stored function for now
            result = self.db_manager.adapter.client.client.table('cloud_jobs').select('*').eq('status', 'waiting').order('created_at').limit(1).execute()
            
            if result.data and len(result.data) > 0:
                job_data = result.data[0]
                
                # Try to lock this job atomically
                lock_expires = datetime.utcnow() + timedelta(minutes=self.lock_duration_minutes)
                update_result = self.db_manager.adapter.client.client.table('cloud_jobs').update({
                    'status': 'locked',
                    'locked_at': datetime.utcnow().isoformat(),
                    'locked_by': self.instance_id,
                    'lock_expires_at': lock_expires.isoformat()
                }).eq('job_id', job_data['job_id']).eq('status', 'waiting').execute()
                
                if update_result.data and len(update_result.data) > 0:
                    # Successfully locked the job
                    job_data = update_result.data[0]
                    
                    # Convert to CloudJob object
                    job = CloudJob(
                        job_id=job_data['job_id'],
                        name=job_data['name'],
                        job_type=CloudJobType(job_data['job_type']),
                        config=job_data['config'],
                        description=job_data['description'],
                        current_retries=job_data.get('current_retries', 0),
                        max_retries=job_data.get('max_retries', 3),
                        status=CloudJobStatus.LOCKED,
                        locked_at=datetime.utcnow(),
                        locked_by=self.instance_id,
                        lock_expires_at=lock_expires
                    )
                    
                    logger.info(f"Picked job: {job.name} ({job.job_id}) - Instance: {self.instance_id}")
                    return job
                else:
                    # Failed to lock the job (race condition)
                    return None
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error getting job from Supabase: {e}")
            return None
    
    def _get_next_job_sqlite(self) -> Optional[CloudJob]:
        """Get next job using SQLite with transaction-based locking"""
        try:
            # Start transaction
            conn = sqlite3.connect(self.db_manager.adapter.db_path)
            cursor = conn.cursor()
            
            try:
                # Begin transaction
                cursor.execute("BEGIN IMMEDIATE")
                
                # Find next available job
                cursor.execute("""
                    SELECT job_id, name, job_type, config, description, 
                           max_retries, current_retries, created_at
                    FROM cloud_jobs 
                    WHERE (status = 'waiting' OR (status = 'failed' AND current_retries < max_retries))
                      AND (lock_expires_at IS NULL OR lock_expires_at < datetime('now'))
                    ORDER BY 
                        CASE 
                            WHEN status = 'waiting' THEN 0 
                            WHEN status = 'failed' THEN 1 
                            ELSE 2 
                        END,
                        created_at ASC
                    LIMIT 1
                """)
                
                row = cursor.fetchone()
                if not row:
                    conn.commit()
                    return None
                
                job_id = row[0]
                
                # Lock the job
                lock_expires = datetime.utcnow() + timedelta(minutes=self.lock_duration_minutes)
                cursor.execute("""
                    UPDATE cloud_jobs 
                    SET status = 'locked',
                        locked_at = ?,
                        locked_by = ?,
                        lock_expires_at = ?
                    WHERE job_id = ?
                """, (
                    datetime.utcnow().isoformat(),
                    self.instance_id,
                    lock_expires.isoformat(),
                    job_id
                ))
                
                # Commit transaction
                conn.commit()
                
                # Create CloudJob object
                import json
                job = CloudJob(
                    job_id=row[0],
                    name=row[1],
                    job_type=CloudJobType(row[2]),
                    config=json.loads(row[3]),
                    description=row[4],
                    max_retries=row[5],
                    current_retries=row[6],
                    created_at=datetime.fromisoformat(row[7]) if row[7] else None,
                    status=CloudJobStatus.LOCKED,
                    locked_at=datetime.utcnow(),
                    locked_by=self.instance_id,
                    lock_expires_at=lock_expires
                )
                
                logger.info(f"Picked job: {job.name} ({job.job_id}) - Instance: {self.instance_id}")
                return job
                
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                cursor.close()
                
        except Exception as e:
            logger.error(f"Error getting job from SQLite: {e}")
            return None
    
    def complete_job(self, job: CloudJob, success: bool, result: Dict[str, Any] = None, error_message: str = None):
        """Mark job as completed (success or failed)"""
        try:
            if success:
                new_status = CloudJobStatus.SUCCESS
            else:
                # Check if we should retry
                if job.current_retries < job.max_retries:
                    new_status = CloudJobStatus.WAITING
                    job.current_retries += 1
                else:
                    new_status = CloudJobStatus.FAILED
            
            # Update job status
            self._update_job_status(
                job.job_id, 
                new_status, 
                job.current_retries if not success else None
            )
            
            logger.info(f"Job {job.job_id} completed with status: {new_status.value}")
            
        except Exception as e:
            logger.error(f"Error completing job {job.job_id}: {e}")
    
    def _update_job_status(self, job_id: str, status: CloudJobStatus, current_retries: int = None):
        """Update job status and clear lock"""
        try:
            if hasattr(self.db_manager.adapter, 'client') and hasattr(self.db_manager.adapter.client, 'client'):
                # Supabase
                update_data = {
                    'status': status.value,
                    'locked_at': None,
                    'locked_by': None,
                    'lock_expires_at': None,
                    'last_execution': datetime.utcnow().isoformat()
                }
                
                if current_retries is not None:
                    update_data['current_retries'] = current_retries
                
                self.db_manager.adapter.client.client.table('cloud_jobs').update(update_data).eq('job_id', job_id).execute()
            else:
                # SQLite
                conn = sqlite3.connect(self.db_manager.adapter.db_path)
                cursor = conn.cursor()
                
                if current_retries is not None:
                    cursor.execute("""
                        UPDATE cloud_jobs 
                        SET status = ?, current_retries = ?, locked_at = NULL, 
                            locked_by = NULL, lock_expires_at = NULL, 
                            last_execution = ?
                        WHERE job_id = ?
                    """, (status.value, current_retries, datetime.utcnow().isoformat(), job_id))
                else:
                    cursor.execute("""
                        UPDATE cloud_jobs 
                        SET status = ?, locked_at = NULL, 
                            locked_by = NULL, lock_expires_at = NULL, 
                            last_execution = ?
                        WHERE job_id = ?
                    """, (status.value, datetime.utcnow().isoformat(), job_id))
                
                conn.commit()
                cursor.close()
                
        except Exception as e:
            logger.error(f"Error updating job status: {e}")
    
    def _release_expired_locks(self):
        """Release any expired job locks"""
        try:
            if hasattr(self.db_manager.adapter, 'client') and hasattr(self.db_manager.adapter.client, 'client'):
                # Supabase - query and update expired locks directly
                try:
                    # First find expired locks
                    now = datetime.utcnow().isoformat()
                    expired_result = self.db_manager.adapter.client.client.table('cloud_jobs').select('job_id', 'current_retries', 'max_retries').eq('status', 'locked').lt('lock_expires_at', now).execute()
                    
                    released_count = 0
                    if expired_result.data:
                        for job in expired_result.data:
                            # Determine new status based on retry count
                            new_status = 'waiting' if job['current_retries'] < job['max_retries'] else 'failed'
                            
                            # Update the job
                            update_result = self.db_manager.adapter.client.client.table('cloud_jobs').update({
                                'status': new_status,
                                'locked_at': None,
                                'locked_by': None,
                                'lock_expires_at': None
                            }).eq('job_id', job['job_id']).execute()
                            
                            if update_result.data:
                                released_count += 1
                    
                    if released_count > 0:
                        logger.info(f"Released {released_count} expired locks")
                        
                except Exception as e:
                    logger.warning(f"Could not release expired locks from Supabase: {e}")
            else:
                # SQLite
                conn = sqlite3.connect(self.db_manager.adapter.db_path)
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE cloud_jobs 
                    SET status = CASE 
                        WHEN current_retries < max_retries THEN 'waiting'
                        ELSE 'failed'
                    END,
                    locked_at = NULL,
                    locked_by = NULL,
                    lock_expires_at = NULL
                    WHERE status = 'locked' 
                      AND lock_expires_at < datetime('now')
                """)
                
                released_count = cursor.rowcount
                if released_count > 0:
                    logger.info(f"Released {released_count} expired locks")
                
                conn.commit()
                cursor.close()
                
        except Exception as e:
            logger.error(f"Error releasing expired locks: {e}")
    
    def get_job_statistics(self) -> Dict[str, int]:
        """Get current job statistics"""
        try:
            if hasattr(self.db_manager.adapter, 'client') and hasattr(self.db_manager.adapter.client, 'client'):
                # Supabase - query cloud_jobs table directly
                try:
                    result = self.db_manager.adapter.client.client.table('cloud_jobs').select('status').execute()
                    if result.data:
                        stats = {'total_jobs': 0, 'waiting_jobs': 0, 'locked_jobs': 0, 
                                'success_jobs': 0, 'failed_jobs': 0, 'disabled_jobs': 0}
                        for job in result.data:
                            status = job.get('status', 'unknown')
                            stats['total_jobs'] += 1
                            if status == 'waiting':
                                stats['waiting_jobs'] += 1
                            elif status == 'locked':
                                stats['locked_jobs'] += 1
                            elif status == 'success':
                                stats['success_jobs'] += 1
                            elif status == 'failed':
                                stats['failed_jobs'] += 1
                            elif status == 'disabled':
                                stats['disabled_jobs'] += 1
                        return stats
                    else:
                        return {'total_jobs': 0, 'waiting_jobs': 0, 'locked_jobs': 0, 
                               'success_jobs': 0, 'failed_jobs': 0, 'disabled_jobs': 0}
                except Exception as e:
                    logger.warning(f"Could not get job statistics from Supabase: {e}")
                    return {'total_jobs': 0, 'waiting_jobs': 0, 'locked_jobs': 0, 
                           'success_jobs': 0, 'failed_jobs': 0, 'disabled_jobs': 0}
            else:
                # SQLite
                conn = sqlite3.connect(self.db_manager.adapter.db_path)
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_jobs,
                        SUM(CASE WHEN status = 'waiting' THEN 1 ELSE 0 END) as waiting_jobs,
                        SUM(CASE WHEN status = 'locked' THEN 1 ELSE 0 END) as locked_jobs,
                        SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_jobs,
                        SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_jobs,
                        SUM(CASE WHEN status = 'disabled' THEN 1 ELSE 0 END) as disabled_jobs
                    FROM cloud_jobs
                """)
                
                row = cursor.fetchone()
                cursor.close()
                
                if row:
                    return {
                        'total_jobs': row[0],
                        'waiting_jobs': row[1],
                        'locked_jobs': row[2],
                        'success_jobs': row[3],
                        'failed_jobs': row[4],
                        'disabled_jobs': row[5]
                    }
            
            return {}
            
        except Exception as e:
            logger.error(f"Error getting job statistics: {e}")
            return {}