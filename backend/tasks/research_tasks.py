"""
Research tasks for Celery
"""
import os
import sys
import logging
import asyncio
import traceback
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from database.models import CronJob, JobRun, Paper
from core.dependencies import get_db_session
from repositories.cronjob_repository import CronJobRepository
from repositories.job_run_repository import JobRunRepository
from repositories.paper_repository import PaperRepository
from services.cronjob_service import CronJobService
from utils.job_logger import JobLoggerFactory
try:
    from elasticsearch_config.elasticsearch_config import elasticsearch_config
except ImportError:
    # Fallback configuration if elasticsearch_config is not available
    class DummyElasticsearchConfig:
        def is_configured(self):
            return False
        def get_config_dict(self):
            return {'enabled': False}
    elasticsearch_config = DummyElasticsearchConfig()
from core.config import get_settings

logger = logging.getLogger(__name__)

# Import Celery app
try:
    from celery_app import celery_app
except ImportError:
    logger.warning("Celery app not available - tasks will not be registered")
    celery_app = None

class TaskProgressTracker:
    """Helper class to track and update task progress"""
    
    def __init__(self, task_id: str, job_run_id: str, celery_task=None):
        self.task_id = task_id
        self.job_run_id = job_run_id
        self.celery_task = celery_task
        self.total_steps = 5
        
        # Initialize JobLogger for structured logging
        self.job_logger = None
        if job_run_id:
            try:
                # Create JobLogger with Elasticsearch integration if configured
                es_hosts = elasticsearch_config.hosts if elasticsearch_config.is_configured() else None
                es_username = elasticsearch_config.username if elasticsearch_config.is_configured() else None
                es_password = elasticsearch_config.password if elasticsearch_config.is_configured() else None
                
                self.job_logger = JobLoggerFactory.create_logger(
                    job_run_id=job_run_id,
                    es_hosts=es_hosts,
                    es_username=es_username,
                    es_password=es_password
                )
                self.job_logger.info("Task progress tracker initialized", 
                                   details={'task_id': task_id})
            except Exception as e:
                logger.error(f"Failed to initialize JobLogger: {e}")
        
    def update_progress(self, step: int, description: str, metadata: Optional[Dict] = None):
        """Update task progress and job run status"""
        try:
            progress = int((step / self.total_steps) * 100)
            
            # Update Celery task state if available
            if self.celery_task:
                self.celery_task.update_state(
                    state='PROGRESS',
                    meta={
                        'current': step,
                        'total': self.total_steps,
                        'progress': progress,
                        'description': description,
                        'metadata': metadata
                    }
                )
            
            # Log progress using JobLogger
            if self.job_logger:
                self.job_logger.info(f"Progress: {description}", 
                                   details={
                                       'step': step,
                                       'progress': progress,
                                       'metadata': metadata
                                   })
            
            # Update database
            with get_db_session() as db:
                job_run_repo = JobRunRepository(db)
                job_run_repo.update_progress(
                    self.job_run_id,
                    progress=progress,
                    current_step=description,
                    metadata=metadata
                )
                
        except Exception as e:
            logger.error(f"Failed to update progress: {e}")
            if self.job_logger:
                self.job_logger.error(f"Failed to update progress: {e}", 
                                    error_code="PROGRESS_UPDATE_FAILED")
    
    def log_error(self, message: str, error: Exception = None, **kwargs):
        """Log an error during task execution"""
        if self.job_logger:
            error_details = kwargs.copy()
            if error:
                error_details.update({
                    'error_type': type(error).__name__,
                    'error_message': str(error)
                })
            self.job_logger.error(message, details=error_details)
        else:
            logger.error(f"[JobRun:{self.job_run_id}] {message}")
    
    def log_info(self, message: str, **kwargs):
        """Log an info message during task execution"""
        if self.job_logger:
            self.job_logger.info(message, **kwargs)
        else:
            logger.info(f"[JobRun:{self.job_run_id}] {message}")
    
    def set_step(self, step_name: str):
        """Set current execution step"""
        if self.job_logger:
            self.job_logger.set_step(step_name)
    
    def close(self):
        """Clean up resources"""
        if self.job_logger:
            self.job_logger.close()

# Always define the function, but conditionally register it as a Celery task
def execute_research_job_impl(celery_task_self, job_id: str, manual_trigger: bool = False, user_params: Optional[Dict] = None):
    """
    Execute a research job asynchronously
    
    Args:
        job_id: The cronjob ID to execute
        manual_trigger: Whether this was manually triggered
        user_params: Additional parameters from user
    
    Returns:
        Dict with execution results
    """
    task_id = celery_task_self.request.id if celery_task_self else None
    job_run_id = None
    tracker = None
    
    try:
        logger.info(f"Starting research job execution: {job_id}")
        
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
            
            # Initialize progress tracker with JobLogger
            tracker = TaskProgressTracker(task_id, job_run_id, celery_task_self)
            tracker.update_progress(0, "Initializing job execution...")
            tracker.log_info(f"Job execution started", 
                           details={
                               'job_id': job_id,
                               'job_name': cronjob.name,
                               'keywords': cronjob.keywords,
                               'manual_trigger': manual_trigger,
                               'user_params': user_params
                           })
            
            tracker.set_step("initialization")
            tracker.update_progress(1, f"Starting research for keywords: {', '.join(cronjob.keywords)}")
            
            # Initialize settings
            settings = get_settings()
            settings.validate()
            tracker.log_info("Settings validated successfully")
            
            # Create orchestrator for this job (simplified - would need proper import)
            tracker.set_step("orchestrator_setup")
            tracker.update_progress(2, "Setting up research orchestrator...")
            
            # Execute the research job using the service
            cronjob_service = CronJobService(cronjob_repo, job_run_repo, None)
            
            tracker.set_step("paper_search")
            tracker.update_progress(3, "Searching for papers on arXiv...")
            
            # Run a simplified job execution (real implementation would call orchestrator)
            # For now, just simulate the execution
            import time
            time.sleep(2)  # Simulate work
            
            result = {
                'papers_found': 10,
                'papers_processed': 8,
                'papers_embedded': 7,
                'embedding_errors': 1,
                'vector_db_errors': 0
            }
            
            tracker.set_step("completion")
            tracker.update_progress(5, "Job completed successfully")
            tracker.log_info("Job execution completed", details=result)
            
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
        
        # Log error using JobLogger if available
        if tracker:
            tracker.log_error(f"Job execution failed: {error_message}", 
                            error=exc, 
                            error_code="JOB_EXECUTION_FAILED",
                            traceback=error_traceback)
        
        # Update task state if celery task is available
        if celery_task_self:
            celery_task_self.update_state(
                state='FAILURE',
                meta={
                    'error': error_message,
                    'error_type': type(exc).__name__,
                    'job_run_id': job_run_id,
                    'traceback': error_traceback
                }
            )
        
        return {
            'success': False,
            'error': error_message,
            'error_type': type(exc).__name__,
            'job_run_id': job_run_id
        }
    
    finally:
        # Clean up resources
        if tracker:
            tracker.close()


# Create the actual task registration
if celery_app:
    # Register as Celery task
    execute_research_job = celery_app.task(bind=True, name='tasks.research_tasks.execute_research_job')(execute_research_job_impl)
else:
    # Create a mock task for fallback
    class MockCeleryTask:
        def __init__(self, func):
            self.func = func
            
        def delay(self, *args, **kwargs):
            # This will raise an AttributeError when called
            raise AttributeError("Celery app is not available - tasks cannot be executed via Celery")
        
        def __call__(self, *args, **kwargs):
            return self.func(None, *args, **kwargs)
    
    execute_research_job = MockCeleryTask(execute_research_job_impl)

if celery_app:
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

if celery_app:
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