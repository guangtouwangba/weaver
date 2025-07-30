"""
Celery tasks for research job execution
"""
import asyncio
import logging
import traceback
from datetime import datetime
from typing import Dict, Any, Optional
from celery import current_task
from celery.exceptions import Retry, Ignore

from celery_app import celery_app
from database.database import get_db_session
from repositories.job_run_repository import JobRunRepository
from repositories.cronjob_repository import CronJobRepository
from services.cronjob_service import CronJobService
from agents.orchestrator import ResearchOrchestrator
from core.config import get_settings
from tasks.task_utils import TaskRetryPolicy, TaskProgressManager, handle_task_error, validate_task_environment

logger = logging.getLogger(__name__)

class TaskProgressTracker:
    """Helper class to track and update task progress"""
    
    def __init__(self, task_id: str, job_run_id: str):
        self.task_id = task_id
        self.job_run_id = job_run_id
        self.progress_manager = TaskProgressManager(current_task, total_steps=5)
        
    def update_progress(self, step: int, description: str, metadata: Optional[Dict] = None):
        """Update task progress and job run status"""
        try:
            # Use the progress manager to update Celery state
            progress_data = self.progress_manager.update(step, description, metadata)
            
            # Update database
            with get_db_session() as db:
                job_run_repo = JobRunRepository(db)
                job_run_repo.update_progress(
                    self.job_run_id,
                    progress=progress_data['progress'],
                    current_step=description,
                    metadata=metadata
                )
                
        except Exception as e:
            logger.error(f"Failed to update progress: {e}")

@celery_app.task(bind=True, name='tasks.research_tasks.execute_research_job')
def execute_research_job(self, job_id: str, manual_trigger: bool = False, user_params: Optional[Dict] = None):
    """
    Execute a research job asynchronously
    
    Args:
        job_id: The cronjob ID to execute
        manual_trigger: Whether this was manually triggered
        user_params: Additional parameters from user
    
    Returns:
        Dict with execution results
    """
    task_id = self.request.id
    job_run_id = None
    retry_policy = TaskRetryPolicy(max_retries=3, base_delay=60, backoff_factor=2.0)
    
    # Validate task environment
    env_validation = validate_task_environment()
    if not env_validation['overall_health']:
        logger.error(f"Task environment validation failed: {env_validation['errors']}")
        return {
            'success': False,
            'error': 'Task environment validation failed',
            'validation_errors': env_validation['errors']
        }
    
    try:
        # Initialize progress tracker
        tracker = TaskProgressTracker(task_id, "")
        
        tracker.update_progress(0, "Initializing job execution...")
        
        # Get database session
        with get_db_session() as db:
            cronjob_repo = CronJobRepository(db)
            job_run_repo = JobRunRepository(db)
            
            # Get the cronjob
            cronjob = cronjob_repo.get_by_id(job_id)
            if not cronjob:
                raise ValueError(f"CronJob {job_id} not found")
            
            # Create job run record
            job_run = job_run_repo.create({
                'job_id': job_id,
                'status': 'running',
                'task_id': task_id,
                'started_at': datetime.utcnow(),
                'manual_trigger': manual_trigger,
                'user_params': user_params or {}
            })
            job_run_id = str(job_run.id)
            
            # Update tracker with job run ID
            tracker.job_run_id = job_run_id
            tracker.update_progress(1, f"Starting research for keywords: {', '.join(cronjob.keywords)}")
            
            # Initialize settings and orchestrator
            settings = get_settings()
            settings.validate()
            
            # Create orchestrator for this job
            orchestrator = ResearchOrchestrator(
                openai_api_key=settings.OPENAI_API_KEY,
                deepseek_api_key=settings.DEEPSEEK_API_KEY,
                anthropic_api_key=settings.ANTHROPIC_API_KEY,
                default_provider=settings.DEFAULT_PROVIDER,
                agent_configs=settings.get_all_agent_configs(),
                db_path=settings.VECTOR_DB_PATH
            )
            
            tracker.update_progress(2, "Fetching papers from arXiv...")
            
            # Execute the research job using the service
            cronjob_service = CronJobService(cronjob_repo, job_run_repo, orchestrator)
            
            # Run the actual job execution
            result = asyncio.run(cronjob_service.execute_job_async(
                cronjob, 
                job_run, 
                progress_callback=tracker.update_progress
            ))
            
            tracker.update_progress(5, "Job completed successfully")
            
            # Update final job run status
            job_run_repo.complete_job_run(
                job_run_id,
                status='completed',
                **result
            )
            
            return {
                'success': True,
                'job_run_id': job_run_id,
                'task_id': task_id,
                'result': result,
                'message': f"Successfully processed {result.get('papers_processed', 0)} papers"
            }
            
    except Exception as exc:
        error_message = str(exc)
        error_traceback = traceback.format_exc()
        
        logger.error(f"Task {task_id} failed: {error_message}")
        logger.error(f"Traceback: {error_traceback}")
        
        # Update job run as failed if we have the ID
        if job_run_id:
            try:
                with get_db_session() as db:
                    job_run_repo = JobRunRepository(db)
                    job_run_repo.complete_job_run(
                        job_run_id,
                        status='failed',
                        error_message=error_message,
                        execution_log={'error': error_traceback}
                    )
            except Exception as db_error:
                logger.error(f"Failed to update job run status: {db_error}")
        
        # Update task state
        self.update_state(
            state='FAILURE',
            meta={
                'error': error_message,
                'error_type': type(exc).__name__,
                'job_run_id': job_run_id,
                'traceback': error_traceback
            }
        )
        
        # Use improved error handling
        handle_task_error(self, exc, retry_policy)

@celery_app.task(bind=True, name='tasks.research_tasks.process_papers')
def process_papers(self, papers_data: list, job_config: Dict[str, Any]):
    """
    Process and embed a batch of papers
    
    Args:
        papers_data: List of paper data to process
        job_config: Configuration for processing (embedding model, vector DB, etc.)
    
    Returns:
        Dict with processing results
    """
    task_id = self.request.id
    
    try:
        self.update_state(
            state='PROGRESS',
            meta={
                'current': 0,
                'total': len(papers_data),
                'progress': 0,
                'description': f"Processing {len(papers_data)} papers..."
            }
        )
        
        # Initialize settings
        settings = get_settings()
        
        # Create orchestrator for processing
        orchestrator = ResearchOrchestrator(
            openai_api_key=settings.OPENAI_API_KEY,
            deepseek_api_key=settings.DEEPSEEK_API_KEY,
            anthropic_api_key=settings.ANTHROPIC_API_KEY,
            default_provider=settings.DEFAULT_PROVIDER,
            agent_configs=settings.get_all_agent_configs(),
            db_path=settings.VECTOR_DB_PATH
        )
        
        processed_count = 0
        embedded_count = 0
        errors = []
        
        for i, paper_data in enumerate(papers_data):
            try:
                # Update progress
                progress = int((i / len(papers_data)) * 100)
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'current': i + 1,
                        'total': len(papers_data),
                        'progress': progress,
                        'description': f"Processing paper: {paper_data.get('title', 'Unknown')[:50]}..."
                    }
                )
                
                # Process the paper (this would be async in real implementation)
                result = asyncio.run(orchestrator.process_single_paper(paper_data))
                
                if result.get('success'):
                    processed_count += 1
                    if result.get('embedded'):
                        embedded_count += 1
                else:
                    errors.append({
                        'paper_id': paper_data.get('id'),
                        'error': result.get('error', 'Unknown error')
                    })
                    
            except Exception as e:
                logger.error(f"Error processing paper {paper_data.get('id')}: {e}")
                errors.append({
                    'paper_id': paper_data.get('id'),
                    'error': str(e)
                })
        
        # Final update
        self.update_state(
            state='SUCCESS',
            meta={
                'current': len(papers_data),
                'total': len(papers_data),
                'progress': 100,
                'description': "Processing completed"
            }
        )
        
        return {
            'success': True,
            'task_id': task_id,
            'processed_count': processed_count,
            'embedded_count': embedded_count,
            'error_count': len(errors),
            'errors': errors[:10]  # Limit error list size
        }
        
    except Exception as exc:
        error_message = str(exc)
        error_traceback = traceback.format_exc()
        
        logger.error(f"Paper processing task {task_id} failed: {error_message}")
        logger.error(f"Traceback: {error_traceback}")
        
        self.update_state(
            state='FAILURE',
            meta={
                'error': error_message,
                'error_type': type(exc).__name__,
                'traceback': error_traceback
            }
        )
        
        raise self.retry(exc=exc, countdown=30, max_retries=2)

@celery_app.task(name='tasks.research_tasks.cleanup_old_tasks')
def cleanup_old_tasks():
    """
    Periodic task to cleanup old task results and job runs
    """
    try:
        # This would implement cleanup logic for:
        # 1. Old Celery task results
        # 2. Old job run records
        # 3. Orphaned task records
        
        logger.info("Starting cleanup of old tasks and job runs...")
        
        with get_db_session() as db:
            job_run_repo = JobRunRepository(db)
            
            # Cleanup job runs older than 30 days
            cleanup_result = job_run_repo.cleanup_old_runs(days=30)
            
            logger.info(f"Cleanup completed: {cleanup_result}")
            
        return {
            'success': True,
            'message': 'Cleanup completed successfully',
            'result': cleanup_result
        }
        
    except Exception as e:
        logger.error(f"Cleanup task failed: {e}")
        return {
            'success': False,
            'error': str(e)
        }

@celery_app.task(name='tasks.research_tasks.health_check')
def health_check():
    """
    Health check task to verify Celery worker is functioning
    """
    try:
        # Test database connection
        with get_db_session() as db:
            # Simple query to test DB connectivity
            result = db.execute("SELECT 1").fetchone()
            
        # Test Redis connection
        from celery_app import celery_app
        inspector = celery_app.control.inspect()
        stats = inspector.stats()
        
        return {
            'success': True,
            'timestamp': datetime.utcnow().isoformat(),
            'database': 'connected',
            'redis': 'connected' if stats else 'disconnected',
            'worker_stats': stats
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }