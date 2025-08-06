#!/usr/bin/env python3
"""
Lock Cleaner Thread
Periodically cleans up expired job locks to prevent orphaned locks from dead instances
"""

import os
import sys
import logging
import threading
import time
from typing import Optional
from datetime import datetime, timedelta

# Add backend path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database.database_adapter import DatabaseManager
from jobs.job_picker import CloudJobPicker

logger = logging.getLogger(__name__)

class LockCleanerThread:
    """Periodically cleans up expired job locks in a separate thread"""
    
    def __init__(self, db_manager: DatabaseManager, clean_interval: int = 300):  # 5 minutes default
        self.db_manager = db_manager
        self.clean_interval = clean_interval  # seconds between cleanup cycles
        
        # Create a job picker just for lock cleaning
        self.job_picker = CloudJobPicker(db_manager, "lock-cleaner")
        
        self.running = False
        self.thread: Optional[threading.Thread] = None
        
        # Statistics
        self.stats = {
            'cleanup_cycles': 0,
            'total_locks_released': 0,
            'last_cleanup_time': None,
            'thread_start_time': None
        }
        
        logger.info(f"LockCleanerThread initialized - Clean interval: {clean_interval}s")
    
    def start(self):
        """Start the lock cleaner thread"""
        if self.running:
            logger.warning("Lock cleaner thread is already running")
            return
        
        logger.info("Starting lock cleaner thread...")
        self.running = True
        self.stats['thread_start_time'] = datetime.utcnow()
        
        self.thread = threading.Thread(target=self._cleanup_loop, daemon=False)
        self.thread.start()
        
        logger.info("Lock cleaner thread started")
    
    def stop(self):
        """Stop the lock cleaner thread"""
        if not self.running:
            return
        
        logger.info("Stopping lock cleaner thread...")
        self.running = False
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=10)
        
        logger.info("Lock cleaner thread stopped")
    
    def _cleanup_loop(self):
        """Main cleanup loop - periodically releases expired locks"""
        logger.info(f"Lock cleanup loop started - cleaning every {self.clean_interval}s")
        
        while self.running:
            try:
                self.stats['last_cleanup_time'] = datetime.utcnow()
                self.stats['cleanup_cycles'] += 1
                
                # Release expired locks
                released_count = self._release_expired_locks()
                if released_count > 0:
                    self.stats['total_locks_released'] += released_count
                    logger.info(f"🧹 Cleaned up {released_count} expired locks (cycle #{self.stats['cleanup_cycles']})")
                
                # Also clean up very old failed jobs (optional)
                if self.stats['cleanup_cycles'] % 12 == 0:  # Every hour (12 * 5min cycles)
                    self._cleanup_old_failed_jobs()
                
                # Wait for next cleanup cycle
                if self.running:
                    time.sleep(self.clean_interval)
                    
            except Exception as e:
                logger.error(f"Error in lock cleanup loop: {e}")
                if self.running:
                    time.sleep(self.clean_interval)
        
        logger.info("Lock cleanup loop finished")
    
    def _release_expired_locks(self) -> int:
        """Release expired locks and return count of released locks"""
        try:
            if hasattr(self.db_manager.adapter, 'client') and hasattr(self.db_manager.adapter.client, 'client'):
                # Supabase
                now = datetime.utcnow().isoformat()
                expired_result = self.db_manager.adapter.client.client.table('cloud_jobs').select('job_id', 'current_retries', 'max_retries', 'locked_by').eq('status', 'locked').lt('lock_expires_at', now).execute()
                
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
                            logger.debug(f"Released expired lock for job {job['job_id']} (was locked by {job['locked_by']})")
                
                return released_count
                
            else:
                # SQLite
                import sqlite3
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
                conn.commit()
                cursor.close()
                
                return released_count
                
        except Exception as e:
            logger.error(f"Error releasing expired locks: {e}")
            return 0
    
    def _cleanup_old_failed_jobs(self):
        """Clean up very old failed jobs (older than 7 days)"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=7)
            
            if hasattr(self.db_manager.adapter, 'client') and hasattr(self.db_manager.adapter.client, 'client'):
                # Supabase
                result = self.db_manager.adapter.client.client.table('cloud_jobs').delete().eq('status', 'failed').lt('created_at', cutoff_date.isoformat()).execute()
                if result.data:
                    deleted_count = len(result.data)
                    if deleted_count > 0:
                        logger.info(f"🗑️  Cleaned up {deleted_count} old failed jobs (older than 7 days)")
            else:
                # SQLite
                import sqlite3
                conn = sqlite3.connect(self.db_manager.adapter.db_path)
                cursor = conn.cursor()
                
                cursor.execute("""
                    DELETE FROM cloud_jobs 
                    WHERE status = 'failed' 
                      AND created_at < ?
                """, (cutoff_date.isoformat(),))
                
                deleted_count = cursor.rowcount
                if deleted_count > 0:
                    logger.info(f"🗑️  Cleaned up {deleted_count} old failed jobs (older than 7 days)")
                
                conn.commit()
                cursor.close()
                
        except Exception as e:
            logger.warning(f"Error cleaning up old failed jobs: {e}")
    
    def get_status(self) -> dict:
        """Get current status of the lock cleaner"""
        return {
            'running': self.running,
            'clean_interval': self.clean_interval,
            'thread_alive': self.thread.is_alive() if self.thread else False,
            'statistics': self.stats.copy()
        }
    
    def is_healthy(self) -> bool:
        """Check if the lock cleaner thread is healthy"""
        return (
            self.running and 
            self.thread is not None and 
            self.thread.is_alive()
        )