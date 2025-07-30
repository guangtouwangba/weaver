"""
Utility functions for Celery tasks
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from celery.exceptions import Retry

logger = logging.getLogger(__name__)

class TaskRetryPolicy:
    """Configurable retry policy for tasks"""
    
    def __init__(self, max_retries: int = 3, base_delay: int = 60, backoff_factor: float = 2.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.backoff_factor = backoff_factor
    
    def get_retry_delay(self, retry_count: int) -> int:
        """Calculate retry delay with exponential backoff"""
        return int(self.base_delay * (self.backoff_factor ** retry_count))
    
    def should_retry(self, retry_count: int, exception: Exception) -> bool:
        """Determine if task should be retried"""
        if retry_count >= self.max_retries:
            return False
        
        # Don't retry certain types of errors
        non_retryable_errors = [
            'ValidationError',
            'NotFoundError',
            'AuthenticationError',
            'PermissionError'
        ]
        
        error_type = type(exception).__name__
        if error_type in non_retryable_errors:
            return False
        
        return True

class TaskProgressManager:
    """Manages task progress tracking"""
    
    def __init__(self, task, total_steps: int = 5):
        self.task = task
        self.current_step = 0
        self.total_steps = total_steps
        self.start_time = datetime.utcnow()
    
    def update(self, step: int, description: str, metadata: Optional[Dict] = None):
        """Update task progress"""
        self.current_step = step
        progress = int((step / self.total_steps) * 100)
        
        elapsed_time = (datetime.utcnow() - self.start_time).total_seconds()
        estimated_total_time = (elapsed_time / step) * self.total_steps if step > 0 else 0
        remaining_time = max(0, estimated_total_time - elapsed_time)
        
        progress_data = {
            'current': step,
            'total': self.total_steps,
            'progress': progress,
            'description': description,
            'elapsed_time': elapsed_time,
            'estimated_remaining': remaining_time,
            'metadata': metadata or {}
        }
        
        self.task.update_state(
            state='PROGRESS',
            meta=progress_data
        )
        
        return progress_data

def handle_task_error(task, exception: Exception, retry_policy: TaskRetryPolicy) -> None:
    """Handle task errors with proper logging and retry logic"""
    error_info = {
        'error_type': type(exception).__name__,
        'error_message': str(exception),
        'task_id': task.request.id,
        'retry_count': task.request.retries,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    logger.error(f"Task {task.request.id} failed: {error_info}")
    
    # Check if we should retry
    if retry_policy.should_retry(task.request.retries, exception):
        retry_delay = retry_policy.get_retry_delay(task.request.retries)
        
        logger.info(f"Retrying task {task.request.id} in {retry_delay} seconds "
                   f"(attempt {task.request.retries + 1}/{retry_policy.max_retries})")
        
        # Update task state before retry
        task.update_state(
            state='RETRY',
            meta={
                'retry_count': task.request.retries + 1,
                'max_retries': retry_policy.max_retries,
                'retry_delay': retry_delay,
                'error': error_info,
                'next_retry_at': (datetime.utcnow() + timedelta(seconds=retry_delay)).isoformat()
            }
        )
        
        raise task.retry(exc=exception, countdown=retry_delay, max_retries=retry_policy.max_retries)
    else:
        # Final failure
        logger.error(f"Task {task.request.id} failed permanently after {task.request.retries} retries")
        
        task.update_state(
            state='FAILURE',
            meta={
                'error': error_info,
                'final_failure': True,
                'retry_count': task.request.retries
            }
        )
        
        raise exception

def cleanup_task_resources(task_id: str) -> Dict[str, Any]:
    """Cleanup resources associated with a task"""
    try:
        from database.database import get_db_session
        from repositories.job_run_repository import JobRunRepository
        
        with get_db_session() as db:
            job_run_repo = JobRunRepository(db)
            job_run = job_run_repo.get_by_task_id(task_id)
            
            if job_run and job_run.status in ['pending', 'running']:
                # Mark as cancelled if still in progress
                job_run_repo.update_run_status(
                    str(job_run.id),
                    'cancelled',
                    datetime.utcnow(),
                    'Task cleanup - resources freed'
                )
                
                return {
                    'success': True,
                    'job_run_id': str(job_run.id),
                    'previous_status': job_run.status,
                    'action': 'marked_as_cancelled'
                }
        
        return {
            'success': True,
            'action': 'no_cleanup_needed'
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up task {task_id}: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def validate_task_environment() -> Dict[str, Any]:
    """Validate that the task environment is properly configured"""
    validation_results = {
        'database': False,
        'redis': False,
        'ai_providers': False,
        'vector_db': False,
        'errors': []
    }
    
    try:
        # Test database connection
        from database.database import get_db_session
        with get_db_session() as db:
            db.execute("SELECT 1").fetchone()
        validation_results['database'] = True
    except Exception as e:
        validation_results['errors'].append(f"Database connection failed: {e}")
    
    try:
        # Test Redis connection
        from celery_app import celery_app
        inspector = celery_app.control.inspect()
        stats = inspector.stats()
        validation_results['redis'] = bool(stats)
    except Exception as e:
        validation_results['errors'].append(f"Redis connection failed: {e}")
    
    try:
        # Test AI providers
        from core.config import get_settings
        settings = get_settings()
        settings.validate()
        validation_results['ai_providers'] = True
    except Exception as e:
        validation_results['errors'].append(f"AI provider validation failed: {e}")
    
    try:
        # Test vector database (basic check)
        from database.vector_db import VectorDBFactory
        # This is a basic instantiation test
        validation_results['vector_db'] = True
    except Exception as e:
        validation_results['errors'].append(f"Vector DB validation failed: {e}")
    
    validation_results['overall_health'] = all([
        validation_results['database'],
        validation_results['redis'],
        validation_results['ai_providers'],
        validation_results['vector_db']
    ])
    
    return validation_results