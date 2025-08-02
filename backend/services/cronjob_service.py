"""
Cronjob service for managing job execution and scheduling.
Refactored to use repository pattern and dependency injection.
"""
import logging
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import BackgroundTasks

from database.models import CronJob, JobRun, Paper
from repositories.cronjob_repository import CronJobRepository
from repositories.job_run_repository import JobRunRepository
from repositories.paper_repository import PaperRepository
from core.exceptions import NotFoundError, ValidationError, ServiceError
from database.config_manager import get_config_manager
from retrieval.arxiv_client import ArxivClient, SearchOperator, SearchFilter, DateRange
from database.embeddings import EmbeddingModelFactory
from database.vector_db import VectorDBFactory
from api.batch_processor import BatchProcessorFactory
from utils.job_logger import JobLoggerFactory

logger = logging.getLogger(__name__)

class CronJobService:
    """Service for managing cronjobs and their execution"""
    
    def __init__(self, 
                 cronjob_repository: CronJobRepository,
                 job_run_repository: JobRunRepository,
                 paper_repository: Optional[PaperRepository] = None,
                 orchestrator: Optional['ResearchOrchestrator'] = None):
        self.cronjob_repo = cronjob_repository
        self.job_run_repo = job_run_repository
        self.paper_repo = paper_repository
        self.orchestrator = orchestrator
        self.config_manager = get_config_manager()
        self.arxiv_client = ArxivClient()
    
    def create_job(self, job_data: Dict[str, Any]) -> CronJob:
        """Create a new cronjob"""
        try:
            # Validate that name doesn't already exist
            if self.cronjob_repo.name_exists(job_data['name']):
                raise ValidationError(f"A cronjob with name '{job_data['name']}' already exists")
            
            # Validate providers
            self._validate_providers(
                job_data.get('embedding_provider', 'openai'),
                job_data.get('vector_db_provider', 'chroma')
            )
            
            # Create the job using repository
            job = self.cronjob_repo.create(
                id=str(uuid.uuid4()),
                name=job_data['name'],
                keywords=job_data['keywords'],
                cron_expression=job_data.get('cron_expression'),
                interval_hours=job_data.get('interval_hours'),
                enabled=job_data.get('enabled', True),
                max_papers_per_run=job_data.get('max_papers_per_run', 50),
                embedding_provider=job_data.get('embedding_provider', 'openai'),
                embedding_model=job_data.get('embedding_model', 'text-embedding-3-small'),
                vector_db_provider=job_data.get('vector_db_provider', 'chroma'),
                vector_db_config=job_data.get('vector_db_config')
            )
            
            logger.info(f"Created cronjob: {job.name} ({job.id})")
            return job
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error creating cronjob: {e}")
            raise ServiceError(f"Failed to create cronjob: {str(e)}")
    
    def update_job(self, job_id: str, update_data: Dict[str, Any]) -> CronJob:
        """Update an existing cronjob"""
        try:
            # Check if job exists
            job = self.cronjob_repo.get_by_id(job_id)
            if not job:
                raise NotFoundError(f"Cronjob {job_id} not found")
            
            # Validate name uniqueness if name is being updated
            if 'name' in update_data and update_data['name'] != job.name:
                if self.cronjob_repo.name_exists(update_data['name'], exclude_id=job_id):
                    raise ValidationError(f"A cronjob with name '{update_data['name']}' already exists")
            
            # Validate providers if they're being updated
            if 'embedding_provider' in update_data or 'vector_db_provider' in update_data:
                self._validate_providers(
                    update_data.get('embedding_provider', job.embedding_provider),
                    update_data.get('vector_db_provider', job.vector_db_provider)
                )
            
            # Update using repository
            updated_job = self.cronjob_repo.update(job_id, **update_data)
            logger.info(f"Updated cronjob: {updated_job.name} ({updated_job.id})")
            return updated_job
            
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            logger.error(f"Error updating cronjob {job_id}: {e}")
            raise ServiceError(f"Failed to update cronjob: {str(e)}")
    
    def delete_job(self, job_id: str) -> bool:
        """Delete a cronjob"""
        try:
            # Check if job exists
            job = self.cronjob_repo.get_by_id(job_id)
            if not job:
                raise NotFoundError(f"Cronjob {job_id} not found")
            
            # Delete using repository
            success = self.cronjob_repo.delete(job_id)
            if success:
                logger.info(f"Deleted cronjob: {job_id}")
            return success
            
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error deleting cronjob {job_id}: {e}")
            raise ServiceError(f"Failed to delete cronjob: {str(e)}")
    
    def get_job(self, job_id: str) -> CronJob:
        """Get a specific cronjob"""
        job = self.cronjob_repo.get_by_id(job_id)
        if not job:
            raise NotFoundError(f"Cronjob {job_id} not found")
        return job
    
    def list_jobs(self, skip: int = 0, limit: int = 100, enabled_only: bool = False) -> List[CronJob]:
        """List all cronjobs"""
        if enabled_only:
            return self.cronjob_repo.get_enabled_jobs(skip, limit)
        else:
            return self.cronjob_repo.get_all(skip, limit)
    
    def toggle_job(self, job_id: str) -> CronJob:
        """Toggle job enabled/disabled status"""
        try:
            job = self.cronjob_repo.get_by_id(job_id)
            if not job:
                raise NotFoundError(f"Cronjob {job_id} not found")
            
            # Toggle enabled status
            updated_job = self.cronjob_repo.update(job_id, enabled=not job.enabled)
            logger.info(f"Toggled cronjob {job_id}: enabled = {updated_job.enabled}")
            return updated_job
            
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error toggling cronjob {job_id}: {e}")
            raise ServiceError(f"Failed to toggle cronjob: {str(e)}")
    
    def trigger_job(self, job_id: str, background_tasks: BackgroundTasks, 
                   force_reprocess: bool = False) -> dict:
        """Trigger a job execution using Celery"""
        try:
            # Get the job
            job = self.cronjob_repo.get_by_id(job_id)
            if not job:
                raise NotFoundError(f"Cronjob {job_id} not found")
            
            # Try to use Celery task if available
            try:
                from tasks.research_tasks import execute_research_job
                
                # Trigger Celery task
                task = execute_research_job.delay(
                    job_id=job_id,
                    manual_trigger=True,
                    user_params={'force_reprocess': force_reprocess}
                )
                
                logger.info(f"Triggered Celery task for cronjob: {job.name} ({job.id}), task ID: {task.id}")
                
                return {
                    'job_run_id': None,  # Will be created by the Celery task
                    'task_id': task.id,
                    'status': 'started',
                    'message': 'Job execution started in background'
                }
                
            except (ImportError, AttributeError) as e:
                logger.warning(f"Celery not available ({str(e)}), falling back to FastAPI BackgroundTasks")
                
                # Fallback to FastAPI BackgroundTasks
                job_run = self.job_run_repo.create(
                    id=str(uuid.uuid4()),
                    job_id=job_id,
                    status='pending',
                    manual_trigger=True,
                    user_params={'force_reprocess': force_reprocess}
                )
                
                # Add background task for execution
                background_tasks.add_task(self._execute_job, str(job_run.id), force_reprocess)
                
                logger.info(f"Triggered cronjob: {job.name} ({job.id}), run ID: {job_run.id}")
                
                return {
                    'job_run_id': str(job_run.id),
                    'task_id': None,
                    'status': 'started',
                    'message': 'Job execution started in background'
                }
            
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error triggering cronjob {job_id}: {e}")
            raise ServiceError(f"Failed to trigger cronjob: {str(e)}")
    
    def get_job_runs(self, job_id: str, skip: int = 0, limit: int = 50, 
                    status_filter: Optional[str] = None) -> List[JobRun]:
        """Get job runs for a specific job"""
        return self.job_run_repo.get_by_job_id(job_id, skip, limit, status_filter)
    
    def get_job_run(self, run_id: str) -> JobRun:
        """Get a specific job run"""
        job_run = self.job_run_repo.get_by_id(run_id)
        if not job_run:
            raise NotFoundError(f"JobRun {run_id} not found")
        return job_run
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get comprehensive status for a job"""
        try:
            job = self.cronjob_repo.get_by_id(job_id)
            if not job:
                raise NotFoundError(f"Job {job_id} not found")
            
            # Get latest run
            latest_run = self.job_run_repo.get_latest_by_job_id(job_id)
            
            # Get run statistics
            runs = self.job_run_repo.get_by_job_id(job_id, limit=1000)
            total_runs = len(runs)
            successful_runs = len([r for r in runs if r.status == 'completed'])
            failed_runs = len([r for r in runs if r.status == 'failed'])
            success_rate = (successful_runs / total_runs * 100) if total_runs > 0 else 0
            
            return {
                'job_id': job_id,
                'job_name': job.name,
                'enabled': job.enabled,
                'latest_run': latest_run.to_dict() if latest_run else None,
                'statistics': {
                    'total_runs': total_runs,
                    'successful_runs': successful_runs,
                    'failed_runs': failed_runs,
                    'success_rate': success_rate
                }
            }
            
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error getting job statistics: {e}")
            raise ServiceError(f"Failed to get job status: {str(e)}")
    
    def get_overall_statistics(self) -> Dict[str, Any]:
        """Get overall system statistics"""
        try:
            jobs = self.cronjob_repo.get_all(limit=1000)
            total_jobs = len(jobs)
            active_jobs = len([j for j in jobs if j.enabled])
            
            # Get recent runs
            from datetime import datetime, timedelta
            start_date = datetime.utcnow() - timedelta(days=7)
            recent_runs = self.job_run_repo.get_all_runs(skip=0, limit=1000, start_date=start_date)
            recent_completed = len([r for r in recent_runs if r.status == 'completed'])
            recent_failed = len([r for r in recent_runs if r.status == 'failed'])
            
            return {
                'total_jobs': total_jobs,
                'active_jobs': active_jobs,
                'recent_runs': len(recent_runs),
                'recent_completed': recent_completed,
                'recent_failed': recent_failed
            }
            
        except Exception as e:
            logger.error(f"Error getting overall statistics: {e}")
            raise ServiceError(f"Failed to get statistics: {str(e)}")
    
    def _validate_providers(self, embedding_provider: str, vector_db_provider: str):
        """Validate that providers are supported"""
        # This would check against available providers
        pass
    
    async def _execute_job(self, job_run_id: str, force_reprocess: bool = False):
        """Execute a job with comprehensive logging"""
        try:
            # Get job run
            job_run = self.job_run_repo.get_by_id(job_run_id)
            if not job_run:
                logger.error(f"Job run {job_run_id} not found")
                return
            
            # Get job
            job = self.cronjob_repo.get_by_id(job_run.job_id)
            if not job:
                logger.error(f"Job {job_run.job_id} not found")
                return
            
            # Initialize paper repository if not already available
            # Use a separate database session for paper operations to avoid transaction conflicts
            if not self.paper_repo:
                from core.dependencies import get_db_session
                paper_db = get_db_session()
                self.paper_repo = PaperRepository(paper_db)
            
            # Create job logger
            job_logger = JobLoggerFactory.create_logger(job_run_id)
            
            try:
                # Update status to running
                job_logger.update_status('running', reason='Job execution started')
                
                with job_logger.timed_step("Fetching papers from ArXiv"):
                    papers = await self._fetch_papers_from_arxiv(job, job_logger)
                    job_logger.info(f"Found {len(papers)} papers from ArXiv")
                    job_logger.record_metric('papers_found', len(papers))
                
                if not papers:
                    job_logger.info("No new papers found")
                    job_logger.update_status('completed', reason='No new papers found')
                    return
                
                with job_logger.timed_step("Filtering existing papers"):
                    new_papers = self._filter_existing_papers(papers)
                    job_logger.info(f"Filtered to {len(new_papers)} new papers")
                    job_logger.record_metric('papers_filtered', len(new_papers))
                
                if not new_papers:
                    job_logger.info("No new papers after filtering")
                    job_logger.update_status('completed', reason='No new papers after filtering')
                    return
                
                with job_logger.timed_step("Processing papers"):
                    processing_stats = await self._process_papers(job, new_papers, job_logger)
                    job_logger.info(f"Processing completed: {processing_stats}")
                    job_logger.record_metric('papers_processed', processing_stats['papers_processed'])
                    job_logger.record_metric('papers_embedded', processing_stats['papers_embedded'])
                    job_logger.record_metric('embedding_errors', processing_stats['embedding_errors'])
                    job_logger.record_metric('vector_db_errors', processing_stats['vector_db_errors'])
                
                # Update job run with final stats
                self.job_run_repo.update(job_run_id, 
                                       status='completed',
                                       completed_at=datetime.now(),
                                       papers_found=len(papers),
                                       papers_processed=processing_stats['papers_processed'],
                                       papers_embedded=processing_stats['papers_embedded'],
                                       embedding_errors=processing_stats['embedding_errors'],
                                       vector_db_errors=processing_stats['vector_db_errors'])
                
                job_logger.update_status('completed', reason='Job completed successfully')
                job_logger.info(f"Job completed successfully: processed {processing_stats['papers_processed']} papers")
                
            except Exception as e:
                job_logger.error(f"Job execution failed: {str(e)}", error_code='EXECUTION_ERROR')  
                job_logger.update_status('failed', reason=f'Job execution failed: {str(e)}')
                
                # Update job run with error using a fresh database session
                try:
                    from core.dependencies import get_db_session
                    with get_db_session() as fresh_db:
                        fresh_job_run_repo = JobRunRepository(fresh_db)
                        fresh_job_run_repo.update(job_run_id,
                                                status='failed',
                                                completed_at=datetime.now(),
                                                error_message=str(e))
                        fresh_db.commit()
                except Exception as db_error:
                    logger.error(f"Failed to update job run status in database: {db_error}")
                
        except Exception as e:
            logger.error(f"Error in job execution: {e}")
            # Try to update job status with a fresh database session
            try:
                from core.dependencies import get_db_session
                with get_db_session() as fresh_db:
                    fresh_job_run_repo = JobRunRepository(fresh_db)
                    fresh_job_run_repo.update(job_run_id,
                                            status='failed',
                                            completed_at=datetime.now(),
                                            error_message=f"Critical error in job execution: {str(e)}")
                    fresh_db.commit()
            except Exception as db_error:
                logger.error(f"Failed to update job run status after critical error: {db_error}")
    
    async def _process_papers(self, job: CronJob, papers: List, job_logger) -> Dict[str, int]:
        """Process papers with detailed logging"""
        stats = {
            'papers_processed': 0,
            'papers_embedded': 0,
            'embedding_errors': 0,
            'vector_db_errors': 0
        }
        
        for i, paper in enumerate(papers):
            try:
                with job_logger.paper_context(paper.arxiv_id):
                    job_logger.info(f"Processing paper {i+1}/{len(papers)}: {paper.title}")
                    
                    # Save to SQL database
                    self._save_paper_to_sql(paper, job.embedding_provider, job.embedding_model)
                    stats['papers_processed'] += 1
                    
                    # Generate embeddings
                    try:
                        embedding_model = self._get_embedding_model_instance(job)
                        vector_db = self._get_vector_db_instance(job)
                        
                        # Generate embedding
                        embedding = await embedding_model.generate_embedding(paper.abstract or paper.title)
                        
                        # Store in vector database
                        vector_id = await vector_db.add_document(
                            content=paper.abstract or paper.title,
                            metadata={
                                'arxiv_id': paper.arxiv_id,
                                'title': paper.title,
                                'authors': paper.authors,
                                'categories': paper.categories,
                                'published': paper.published.isoformat() if paper.published else None
                            },
                            embedding=embedding
                        )
                        
                        stats['papers_embedded'] += 1
                        job_logger.info(f"Successfully embedded and stored paper: {paper.arxiv_id}")
                        
                    except Exception as e:
                        stats['embedding_errors'] += 1
                        job_logger.error(f"Embedding error for paper {paper.arxiv_id}: {str(e)}", 
                                       error_code='EMBEDDING_ERROR')
                        
            except Exception as e:
                job_logger.error(f"Error processing paper {paper.arxiv_id}: {str(e)}", 
                               error_code='PROCESSING_ERROR')
        
        return stats
    
    async def execute_job_async(self, cronjob: 'CronJob', job_run: 'JobRun', 
                               progress_callback=None) -> Dict[str, Any]:
        """Execute job asynchronously with progress tracking"""
        try:
            # Create job logger
            job_logger = JobLoggerFactory.create_logger(str(job_run.id))
            
            job_logger.info(f"Starting async execution of job: {cronjob.name}")
            
            # Update status
            job_logger.update_status('running', reason='Async job execution started')
            
            # Fetch papers
            with job_logger.timed_step("Fetching papers"):
                papers = await self._fetch_papers_from_arxiv(cronjob, job_logger)
                job_logger.info(f"Found {len(papers)} papers from ArXiv")
                job_logger.record_metric('papers_found', len(papers))
                
                if progress_callback:
                    progress_callback(25, f"Found {len(papers)} papers")
            
            if not papers:
                job_logger.info("No new papers found")
                job_logger.update_status('completed', reason='No new papers found')
                return {'status': 'completed', 'message': 'No new papers found'}
            
            # Filter existing papers
            with job_logger.timed_step("Filtering papers"):
                new_papers = self._filter_existing_papers(papers)
                job_logger.info(f"Filtered to {len(new_papers)} new papers")
                job_logger.record_metric('papers_filtered', len(new_papers))
                
                if progress_callback:
                    progress_callback(50, f"Processing {len(new_papers)} new papers")
            
            if not new_papers:
                job_logger.info("No new papers after filtering")
                job_logger.update_status('completed', reason='No new papers after filtering')
                return {'status': 'completed', 'message': 'No new papers after filtering'}
            
            # Process papers
            with job_logger.timed_step("Processing papers"):
                processing_stats = await self._process_papers(cronjob, new_papers, job_logger)
                job_logger.info(f"Processing completed: {processing_stats}")
                
                if progress_callback:
                    progress_callback(100, f"Completed: {processing_stats['papers_processed']} papers processed")
            
            # Update final status
            job_logger.update_status('completed', reason='Job completed successfully')
            
            return {
                'status': 'completed',
                'papers_found': len(papers),
                'papers_processed': processing_stats['papers_processed'],
                'papers_embedded': processing_stats['papers_embedded'],
                'embedding_errors': processing_stats['embedding_errors'],
                'vector_db_errors': processing_stats['vector_db_errors']
            }
            
        except Exception as e:
            job_logger.error(f"Async job execution failed: {str(e)}", error_code='ASYNC_EXECUTION_ERROR')
            job_logger.update_status('failed', reason=f'Async job execution failed: {str(e)}')
            raise
    
    def _get_vector_db_instance(self, job: CronJob):
        """Get vector database instance"""
        config = job.vector_db_config or {}
        vector_db = VectorDBFactory.create_instance(job.vector_db_provider, config)
        return vector_db
    
    def _get_embedding_model_instance(self, job: CronJob):
        """Get embedding model instance"""
        config = self.config_manager.get_embedding_config(job.embedding_provider)
        embedding_model = EmbeddingModelFactory.create_instance(job.embedding_provider, config)
        return embedding_model
    
    async def _fetch_papers_from_arxiv(self, job: CronJob, job_logger) -> List:
        """Fetch papers from ArXiv"""
        try:
            job_logger.info(f"Fetching papers for job: {job.name} with keywords: {job.keywords}")
            
            # Build search query
            search_query = " OR ".join([f'ti:"{keyword}" OR abs:"{keyword}"' for keyword in job.keywords])
            
            # Fetch papers with max_results parameter (sync call)
            papers = self.arxiv_client.search_papers(
                query=search_query,
                max_results=job.max_papers_per_run
            )
            
            job_logger.info(f"Found {len(papers)} unique papers for job {job.name}")
            return papers
            
        except Exception as e:
            logger.error(f"Error fetching papers from ArXiv: {e}")
            raise
    
    def _filter_existing_papers(self, papers: List) -> List:
        """Filter out papers that already exist in the database"""
        if not self.paper_repo:
            logger.warning("Paper repository not available, skipping paper filtering")
            return papers
        
        new_papers = []
        for paper in papers:
            try:
                existing_paper = self.paper_repo.get_by_arxiv_id(paper.arxiv_id)
                if not existing_paper:
                    new_papers.append(paper)
            except Exception as e:
                logger.error(f"Error checking if paper {paper.arxiv_id} exists: {e}")
                # In case of error, assume paper is new to avoid blocking the process
                new_papers.append(paper)
        
        logger.info(f"Filtered out {len(papers) - len(new_papers)} existing papers")
        return new_papers
    
    def _save_paper_to_sql(self, paper, embedding_provider: str, embedding_model: str):
        """Save paper to SQL database"""
        try:
            if self.paper_repo:
                self.paper_repo.create(
                    id=paper.arxiv_id,
                    arxiv_id=paper.arxiv_id,
                    title=paper.title,
                    authors=paper.authors,
                    abstract=paper.abstract,
                    categories=paper.categories,
                    published=paper.published,
                    pdf_url=paper.pdf_url,
                    entry_id=paper.entry_id,
                    doi=paper.doi,
                    embedding_provider=embedding_provider,
                    embedding_model=embedding_model
                )
        except Exception as e:
            logger.error(f"Error saving paper {paper.arxiv_id} to SQL: {e}")
    
    def get_all_job_runs(self, skip: int = 0, limit: int = 100,
                         status_filter: Optional[str] = None,
                         job_id_filter: Optional[str] = None,
                         start_date: Optional[str] = None,
                         end_date: Optional[str] = None) -> List[JobRun]:
        """Get all job runs with filtering"""
        try:
            # Parse dates if provided
            start_dt = None
            end_dt = None
            
            if start_date:
                try:
                    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                except ValueError:
                    logger.warning(f"Invalid start_date format: {start_date}")
            
            if end_date:
                try:
                    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                except ValueError:
                    logger.warning(f"Invalid end_date format: {end_date}")
            
            return self.job_run_repo.get_all_with_filters(
                skip, limit, status_filter, job_id_filter, start_dt, end_dt
            )
            
        except Exception as e:
            logger.error(f"Error getting all job runs: {e}")
            return []
    
    def get_history_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Get historical statistics"""
        try:
            # Get recent runs
            from datetime import datetime, timedelta
            start_date = datetime.utcnow() - timedelta(days=days)
            recent_runs = self.job_run_repo.get_all_runs(skip=0, limit=10000, start_date=start_date)
            
            # Calculate statistics
            total_runs = len(recent_runs)
            successful_runs = len([r for r in recent_runs if r.status == 'completed'])
            failed_runs = len([r for r in recent_runs if r.status == 'failed'])
            running_runs = len([r for r in recent_runs if r.status == 'running'])
            cancelled_runs = len([r for r in recent_runs if r.status == 'cancelled'])
            
            success_rate = (successful_runs / total_runs * 100) if total_runs > 0 else 0
            
            # Calculate paper statistics
            total_papers_found = sum(r.papers_found for r in recent_runs)
            total_papers_processed = sum(r.papers_processed for r in recent_runs)
            total_papers_embedded = sum(r.papers_embedded for r in recent_runs)
            total_embedding_errors = sum(r.embedding_errors for r in recent_runs)
            total_vector_errors = sum(r.vector_db_errors for r in recent_runs)
            
            return {
                'global_statistics': {
                    'period_days': days,
                    'total_runs': total_runs,
                    'successful_runs': successful_runs,
                    'failed_runs': failed_runs,
                    'running_runs': running_runs,
                    'cancelled_runs': cancelled_runs,
                    'success_rate': success_rate,
                    'paper_statistics': {
                        'total_found': total_papers_found,
                        'total_processed': total_papers_processed,
                        'total_embedded': total_papers_embedded,
                        'processing_rate': (total_papers_processed / total_papers_found * 100) if total_papers_found > 0 else 0,
                        'embedding_rate': (total_papers_embedded / total_papers_processed * 100) if total_papers_processed > 0 else 0,
                        'total_embedding_errors': total_embedding_errors,
                        'total_vector_errors': total_vector_errors
                    }
                },
                'daily_trends': self._get_daily_trends(days),
                'top_performing_jobs': self._get_top_performing_jobs(days),
                'period_summary': {
                    'period_days': days,
                    'start_date': (datetime.now() - timedelta(days=days)).isoformat(),
                    'end_date': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting history statistics: {e}")
            return {}
    
    def export_job_run_history(self, format: str = "csv",
                              status_filter: Optional[str] = None,
                              job_id_filter: Optional[str] = None,
                              start_date: Optional[str] = None,
                              end_date: Optional[str] = None):
        """Export job run history"""
        try:
            runs = self.get_all_job_runs(
                limit=10000,  # Large limit for export
                status_filter=status_filter,
                job_id_filter=job_id_filter,
                start_date=start_date,
                end_date=end_date
            )
            
            if format.lower() == "csv":
                return self._export_to_csv(runs)
            elif format.lower() == "json":
                return self._export_to_json(runs)
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            logger.error(f"Error exporting job run history: {e}")
            raise ServiceError(f"Failed to export history: {str(e)}")
    
    def _get_daily_trends(self, days: int) -> List[Dict[str, Any]]:
        """Get daily trends for the specified period"""
        try:
            trends = []
            for i in range(days):
                date = datetime.now() - timedelta(days=i)
                start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
                end_of_day = start_of_day + timedelta(days=1)
                
                # Get runs for this day
                daily_runs = self.job_run_repo.get_runs_in_period(start_of_day, end_of_day)
                
                total_runs = len(daily_runs)
                successful_runs = len([r for r in daily_runs if r.status == 'completed'])
                failed_runs = len([r for r in daily_runs if r.status == 'failed'])
                success_rate = (successful_runs / total_runs * 100) if total_runs > 0 else 0
                
                papers_found = sum(r.papers_found for r in daily_runs)
                papers_processed = sum(r.papers_processed for r in daily_runs)
                
                trends.append({
                    'date': start_of_day.strftime('%Y-%m-%d'),
                    'total_runs': total_runs,
                    'successful_runs': successful_runs,
                    'failed_runs': failed_runs,
                    'success_rate': success_rate,
                    'papers_found': papers_found,
                    'papers_processed': papers_processed
                })
            
            return trends
            
        except Exception as e:
            logger.error(f"Error getting daily trends: {e}")
            return []
    
    def _get_top_performing_jobs(self, days: int) -> List[Dict[str, Any]]:
        """Get top performing jobs for the specified period"""
        try:
            # Get recent runs
            from datetime import datetime, timedelta
            start_date = datetime.utcnow() - timedelta(days=days)
            recent_runs = self.job_run_repo.get_all_runs(skip=0, limit=10000, start_date=start_date)
            
            # Group by job
            job_stats = {}
            for run in recent_runs:
                job_id = run.job_id
                if job_id not in job_stats:
                    job_stats[job_id] = {
                        'total_runs': 0,
                        'successful_runs': 0,
                        'recent_runs': 0,
                        'recent_papers_processed': 0
                    }
                
                job_stats[job_id]['total_runs'] += 1
                if run.status == 'completed':
                    job_stats[job_id]['successful_runs'] += 1
                
                # Count recent activity (last 7 days)
                if run.started_at and (datetime.now() - run.started_at).days <= 7:
                    job_stats[job_id]['recent_runs'] += 1
                    job_stats[job_id]['recent_papers_processed'] += run.papers_processed
            
            # Calculate success rates and sort
            top_jobs = []
            for job_id, stats in job_stats.items():
                try:
                    job = self.cronjob_repo.get_by_id(job_id)
                    if job:
                        success_rate = (stats['successful_runs'] / stats['total_runs'] * 100) if stats['total_runs'] > 0 else 0
                        
                        top_jobs.append({
                            'job_id': job_id,
                            'job_name': job.name,
                            'total_runs': stats['total_runs'],
                            'success_rate': success_rate,
                            'recent_runs': stats['recent_runs'],
                            'recent_papers_processed': stats['recent_papers_processed'],
                            'enabled': job.enabled
                        })
                except Exception as e:
                    logger.error(f"Error processing job {job_id}: {e}")
                    continue
            
            # Sort by success rate and recent activity
            top_jobs.sort(key=lambda x: (x['success_rate'], x['recent_runs']), reverse=True)
            return top_jobs[:10]  # Return top 10
            
        except Exception as e:
            logger.error(f"Error getting top performing jobs: {e}")
            return []
    
    def _export_to_csv(self, runs: List[JobRun]) -> Dict[str, Any]:
        """Export runs to CSV format"""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Run ID', 'Job ID', 'Status', 'Started At', 'Completed At',
            'Papers Found', 'Papers Processed', 'Papers Embedded',
            'Embedding Errors', 'Vector DB Errors', 'Error Message'
        ])
        
        # Write data
        for run in runs:
            writer.writerow([
                run.id, run.job_id, run.status,
                run.started_at.isoformat() if run.started_at else '',
                run.completed_at.isoformat() if run.completed_at else '',
                run.papers_found, run.papers_processed, run.papers_embedded,
                run.embedding_errors, run.vector_db_errors,
                run.error_message or ''
            ])
        
        content = output.getvalue()
        output.close()
        
        return {
            'content': content,
            'content_type': 'text/csv',
            'filename': f'job_runs_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        }
    
    def _export_to_json(self, runs: List[JobRun]) -> Dict[str, Any]:
        """Export runs to JSON format"""
        import json
        
        data = {
            'export_date': datetime.now().isoformat(),
            'total_runs': len(runs),
            'runs': [run.to_dict() for run in runs]
        }
        
        content = json.dumps(data, indent=2, default=str)
        
        return {
            'content': content,
            'content_type': 'application/json',
            'filename': f'job_runs_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        }