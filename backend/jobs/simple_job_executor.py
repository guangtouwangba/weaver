#!/usr/bin/env python3
"""
Simple Cloud Job Executor
Lightweight job execution without complex thread management
"""

import os
import sys
import logging
import traceback
import sqlite3
from typing import Dict, Any, Callable
from datetime import datetime

# Add backend path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database.database_adapter import DatabaseManager
from database.cloud_job_models import CloudJob, CloudJobExecution, CloudJobType

logger = logging.getLogger(__name__)

class SimpleJobExecutor:
    """Simple job executor for cloud environments"""
    
    def __init__(self, db_manager: DatabaseManager, instance_id: str):
        self.db_manager = db_manager
        self.instance_id = instance_id
        self.job_handlers: Dict[str, Callable] = {}
        self.register_default_handlers()
        
        logger.info(f"SimpleJobExecutor initialized with instance_id: {instance_id}")
    
    def register_default_handlers(self):
        """Register default job handlers"""
        self.job_handlers['paper_fetch'] = self._handle_paper_fetch
        self.job_handlers['maintenance'] = self._handle_maintenance
        self.job_handlers['custom'] = self._handle_custom
    
    def register_handler(self, job_type: str, handler: Callable):
        """Register a custom job handler"""
        self.job_handlers[job_type] = handler
        logger.info(f"Registered handler for job type: {job_type}")
    
    def execute_job(self, job: CloudJob) -> Dict[str, Any]:
        """
        Execute a job and return the result
        Returns dict with success status and result/error info
        """
        # Create execution record
        execution = CloudJobExecution(
            job_id=job.job_id,
            instance_id=self.instance_id
        )
        
        try:
            # Log execution start
            self._record_execution_start(execution)
            
            logger.info(f"Executing job: {job.name} ({job.job_id})")
            
            # Get handler for job type
            job_type_str = job.job_type.value if isinstance(job.job_type, CloudJobType) else str(job.job_type)
            handler = self.job_handlers.get(job_type_str)
            
            if not handler:
                raise ValueError(f"No handler registered for job type: {job_type_str}")
            
            # Execute the job
            result = handler(job)
            
            # Mark execution as successful
            execution.mark_completed(result)
            self._record_execution_complete(execution)
            
            logger.info(f"Job completed successfully: {job.name} ({job.job_id})")
            
            return {
                'success': True,
                'result': result,
                'execution_id': execution.execution_id,
                'duration_seconds': execution.duration_seconds
            }
            
        except Exception as e:
            error_msg = str(e)
            error_trace = traceback.format_exc()
            
            logger.error(f"Job failed: {job.name} ({job.job_id}) - {error_msg}")
            logger.debug(f"Job error trace: {error_trace}")
            
            # Mark execution as failed
            execution.mark_failed(error_msg)
            execution.result = {'error_trace': error_trace}
            self._record_execution_complete(execution)
            
            return {
                'success': False,
                'error': error_msg,
                'error_trace': error_trace,
                'execution_id': execution.execution_id,
                'duration_seconds': execution.duration_seconds
            }
    
    def _record_execution_start(self, execution: CloudJobExecution):
        """Record execution start in database"""
        try:
            if hasattr(self.db_manager.adapter, 'client') and hasattr(self.db_manager.adapter.client, 'client'):
                # Supabase
                self.db_manager.adapter.client.client.table('cloud_job_executions').insert(
                    execution.to_dict()
                ).execute()
            else:
                # SQLite
                conn = sqlite3.connect(self.db_manager.adapter.db_path)
                cursor = conn.cursor()
                
                data = execution.to_dict()
                cursor.execute("""
                    INSERT INTO cloud_job_executions 
                    (execution_id, job_id, status, started_at, instance_id)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    data['execution_id'],
                    data['job_id'],
                    data['status'],
                    data['started_at'],
                    data['instance_id']
                ))
                
                conn.commit()
                cursor.close()
                
        except Exception as e:
            logger.error(f"Failed to record execution start: {e}")
    
    def _record_execution_complete(self, execution: CloudJobExecution):
        """Record execution completion in database"""
        try:
            if hasattr(self.db_manager.adapter, 'client') and hasattr(self.db_manager.adapter.client, 'client'):
                # Supabase
                update_data = {
                    'status': execution.status,
                    'finished_at': execution.finished_at.isoformat() if execution.finished_at else None,
                    'duration_seconds': execution.duration_seconds,
                    'result': execution.result,
                    'error_message': execution.error_message
                }
                
                self.db_manager.adapter.client.client.table('cloud_job_executions').update(
                    update_data
                ).eq('execution_id', execution.execution_id).execute()
            else:
                # SQLite
                conn = sqlite3.connect(self.db_manager.adapter.db_path)
                cursor = conn.cursor()
                
                import json
                cursor.execute("""
                    UPDATE cloud_job_executions 
                    SET status = ?, finished_at = ?, duration_seconds = ?, 
                        result = ?, error_message = ?
                    WHERE execution_id = ?
                """, (
                    execution.status,
                    execution.finished_at.isoformat() if execution.finished_at else None,
                    execution.duration_seconds,
                    json.dumps(execution.result),
                    execution.error_message,
                    execution.execution_id
                ))
                
                conn.commit()
                cursor.close()
                
        except Exception as e:
            logger.error(f"Failed to record execution completion: {e}")
    
    # Job Handlers
    
    def _handle_paper_fetch(self, job: CloudJob) -> Dict[str, Any]:
        """Handle paper fetching job"""
        try:
            logger.info(f"Starting paper fetch job with config: {job.config}")
            
            # Import here to avoid circular imports
            from simple_paper_fetcher import SimplePaperFetcher
            
            # Get configuration from job config
            config_path = job.config.get('config_path', 'config.yaml')
            
            # Create fetcher and run
            fetcher = SimplePaperFetcher(config_path)
            result = fetcher.run_once()
            
            # Extract key statistics
            stats = {
                'success': result.get('success', False),
                'new_papers': result.get('new_papers', 0),
                'total_papers': result.get('total_papers', 0),
                'duration_seconds': result.get('duration_seconds', 0),
                'errors': result.get('errors', []),
                'search_queries': result.get('search_queries', [])
            }
            
            logger.info(f"Paper fetch completed: {stats['new_papers']} new papers")
            return stats
            
        except Exception as e:
            logger.error(f"Paper fetch job failed: {e}")
            raise
    
    def _handle_maintenance(self, job: CloudJob) -> Dict[str, Any]:
        """Handle maintenance job"""
        try:
            logger.info(f"Starting maintenance job with config: {job.config}")
            
            # Get configuration
            cleanup_days = job.config.get('cleanup_days', 30)
            cleanup_executions = job.config.get('cleanup_executions', True)
            
            results = {
                'tasks_completed': [],
                'total_cleaned': 0
            }
            
            # Clean up old job executions
            if cleanup_executions:
                cleaned_count = self._cleanup_old_executions(cleanup_days)
                results['tasks_completed'].append(f"Cleaned {cleaned_count} old executions")
                results['total_cleaned'] += cleaned_count
            
            # Add more maintenance tasks as needed
            # e.g., database optimization, log cleanup, etc.
            
            logger.info(f"Maintenance completed: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Maintenance job failed: {e}")
            raise
    
    def _handle_custom(self, job: CloudJob) -> Dict[str, Any]:
        """Handle custom job - placeholder for user-defined jobs"""
        try:
            logger.info(f"Executing custom job: {job.name}")
            
            # Custom jobs should register their own handlers
            # This is a fallback that just returns the job config
            return {
                'success': True,
                'message': f'Custom job {job.name} executed successfully',
                'job_config': job.config,
                'execution_time': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Custom job failed: {e}")
            raise
    
    def _cleanup_old_executions(self, days: int) -> int:
        """Clean up old job executions"""
        try:
            cutoff_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            cutoff_date = cutoff_date.replace(day=cutoff_date.day - days)
            
            if hasattr(self.db_manager.adapter, 'client') and hasattr(self.db_manager.adapter.client, 'client'):
                # Supabase
                result = self.db_manager.adapter.client.client.table('cloud_job_executions').delete().lt(
                    'started_at', cutoff_date.isoformat()
                ).execute()
                
                # Count is not directly available in Supabase delete response
                # Return a placeholder count
                cleaned_count = len(result.data) if result.data else 0
                
            else:
                # SQLite
                conn = sqlite3.connect(self.db_manager.adapter.db_path)
                cursor = conn.cursor()
                
                cursor.execute("""
                    DELETE FROM cloud_job_executions
                    WHERE started_at < ?
                """, (cutoff_date.isoformat(),))
                
                cleaned_count = cursor.rowcount
                conn.commit()
                cursor.close()
            
            logger.info(f"Cleaned up {cleaned_count} old job executions (older than {days} days)")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old executions: {e}")
            return 0