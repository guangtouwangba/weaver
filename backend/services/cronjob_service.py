"""
Cronjob service for managing job execution and scheduling.
Refactored to use repository pattern and dependency injection.
"""
import logging
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
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
            if not self.cronjob_repo.exists(job_id):
                raise NotFoundError(f"Cronjob {job_id} not found")
            
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
        """Get a cronjob by ID"""
        job = self.cronjob_repo.get_by_id(job_id)
        if not job:
            raise NotFoundError(f"Cronjob {job_id} not found")
        return job
    
    def list_jobs(self, skip: int = 0, limit: int = 100, enabled_only: bool = False) -> List[CronJob]:
        """List cronjobs with optional filtering"""
        if enabled_only:
            return self.cronjob_repo.get_enabled_jobs(skip, limit)
        return self.cronjob_repo.get_all(skip, limit)
    
    def toggle_job(self, job_id: str) -> CronJob:
        """Toggle cronjob enabled/disabled status"""
        try:
            job = self.cronjob_repo.toggle_enabled(job_id)
            if not job:
                raise NotFoundError(f"Cronjob {job_id} not found")
            return job
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error toggling cronjob {job_id}: {e}")
            raise ServiceError(f"Failed to toggle cronjob: {str(e)}")
    
    def trigger_job(self, job_id: str, background_tasks: BackgroundTasks, 
                   force_reprocess: bool = False, user_params: Optional[Dict] = None) -> Dict[str, str]:
        """Trigger manual execution of a cronjob using Celery"""
        try:
            job = self.cronjob_repo.get_by_id(job_id)
            if not job:
                raise NotFoundError(f"Cronjob {job_id} not found")
            
            # Import Celery task here to avoid circular imports
            from tasks.research_tasks import execute_research_job
            
            # Trigger Celery task immediately
            task = execute_research_job.delay(
                job_id=job_id,
                manual_trigger=True,
                user_params=user_params or {'force_reprocess': force_reprocess}
            )
            
            logger.info(f"Triggered Celery task for cronjob: {job.name} ({job.id}), task ID: {task.id}")
            
            return {
                'task_id': task.id,
                'job_id': job_id,
                'status': 'PENDING'
            }
            
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error triggering cronjob {job_id}: {e}")
            raise ServiceError(f"Failed to trigger cronjob: {str(e)}")
    
    def get_job_runs(self, job_id: str, skip: int = 0, limit: int = 50, 
                    status_filter: Optional[str] = None) -> List[JobRun]:
        """Get job runs for a specific cronjob"""
        if not self.cronjob_repo.exists(job_id):
            raise NotFoundError(f"Cronjob {job_id} not found")
        
        return self.job_run_repo.get_runs_by_job_id(job_id, skip, limit, status_filter)
    
    def get_job_run(self, run_id: str) -> JobRun:
        """Get a specific job run"""
        run = self.job_run_repo.get_by_id(run_id)
        if not run:
            raise NotFoundError(f"Job run {run_id} not found")
        return run
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get current status of a cronjob"""
        job = self.cronjob_repo.get_by_id(job_id)
        if not job:
            raise NotFoundError(f"Cronjob {job_id} not found")
        
        latest_run = self.job_run_repo.get_latest_run_by_job_id(job_id)
        statistics = self.job_run_repo.get_job_statistics(job_id)
        
        return {
            "job_id": job_id,
            "job_name": job.name,
            "enabled": job.enabled,
            "latest_run": latest_run,
            "statistics": statistics
        }
    
    def get_overall_statistics(self) -> Dict[str, Any]:
        """Get overall job statistics"""
        try:
            total_jobs = self.cronjob_repo.count()
            enabled_jobs = len(self.cronjob_repo.get_enabled_jobs(limit=1000))  # Get all enabled
            running_jobs = self.job_run_repo.get_running_jobs_count()
            
            return {
                "total_jobs": total_jobs,
                "enabled_jobs": enabled_jobs,
                "running_jobs": running_jobs
            }
        except Exception as e:
            logger.error(f"Error getting job statistics: {e}")
            return {"error": str(e)}
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get Celery task status and progress"""
        try:
            from celery_app import celery_app
            from celery.result import AsyncResult
            
            # Get task result
            task_result = AsyncResult(task_id, app=celery_app)
            
            # Get job run associated with this task
            job_run = self.job_run_repo.get_by_task_id(task_id)
            
            status_data = {
                'task_id': task_id,
                'status': task_result.status,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            if task_result.info:
                if isinstance(task_result.info, dict):
                    status_data.update(task_result.info)
                else:
                    status_data['info'] = str(task_result.info)
            
            # Add job run information if available
            if job_run:
                status_data.update({
                    'job_run_id': str(job_run.id),
                    'job_id': str(job_run.job_id),
                    'progress_percentage': job_run.progress_percentage,
                    'current_step': job_run.current_step,
                    'started_at': job_run.started_at.isoformat() if job_run.started_at else None,
                    'completed_at': job_run.completed_at.isoformat() if job_run.completed_at else None
                })
            
            return status_data
            
        except Exception as e:
            logger.error(f"Error getting task status for {task_id}: {e}")
            return {
                'task_id': task_id,
                'status': 'UNKNOWN',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def get_task_progress(self, task_id: str) -> Dict[str, Any]:
        """Get detailed task progress information"""
        try:
            from celery_app import celery_app
            from celery.result import AsyncResult
            
            task_result = AsyncResult(task_id, app=celery_app)
            job_run = self.job_run_repo.get_by_task_id(task_id)
            
            progress_data = {
                'task_id': task_id,
                'status': task_result.status,
                'progress': 0,
                'description': 'Task pending...',
                'current': 0,
                'total': 1
            }
            
            # Get progress from Celery task
            if task_result.info and isinstance(task_result.info, dict):
                progress_data.update({
                    'progress': task_result.info.get('progress', 0),
                    'description': task_result.info.get('description', 'Processing...'),
                    'current': task_result.info.get('current', 0),
                    'total': task_result.info.get('total', 1),
                    'metadata': task_result.info.get('metadata', {})
                })
            
            # Supplement with database information
            if job_run:
                progress_data.update({
                    'job_run_id': str(job_run.id),
                    'db_progress': job_run.progress_percentage,
                    'current_step': job_run.current_step,
                    'papers_found': job_run.papers_found,
                    'papers_processed': job_run.papers_processed,
                    'papers_embedded': job_run.papers_embedded,
                    'errors': {
                        'embedding_errors': job_run.embedding_errors,
                        'vector_db_errors': job_run.vector_db_errors
                    }
                })
            
            return progress_data
            
        except Exception as e:
            logger.error(f"Error getting task progress for {task_id}: {e}")
            return {
                'task_id': task_id,
                'status': 'ERROR',
                'error': str(e),
                'progress': 0
            }
    
    def cancel_task(self, task_id: str) -> Dict[str, Any]:
        """Cancel a running Celery task"""
        try:
            from celery_app import celery_app
            
            # Revoke the task
            celery_app.control.revoke(task_id, terminate=True)
            
            # Update job run status if exists
            job_run = self.job_run_repo.get_by_task_id(task_id)
            if job_run:
                self.job_run_repo.update_run_status(
                    str(job_run.id), 
                    'cancelled', 
                    datetime.utcnow(),
                    'Task cancelled by user'
                )
            
            logger.info(f"Cancelled task: {task_id}")
            return {
                'task_id': task_id,
                'status': 'CANCELLED',
                'message': 'Task cancelled successfully'
            }
            
        except Exception as e:
            logger.error(f"Error cancelling task {task_id}: {e}")
            return {
                'task_id': task_id,
                'status': 'ERROR',
                'error': str(e)
            }
    
    def _validate_providers(self, embedding_provider: str, vector_db_provider: str):
        """Validate that the specified providers are available"""
        available_providers = self.config_manager.get_available_providers()
        
        if embedding_provider not in available_providers['embedding']:
            raise ValidationError(f"Embedding provider '{embedding_provider}' not available")
        
        if vector_db_provider not in available_providers['vector_db']:
            raise ValidationError(f"Vector DB provider '{vector_db_provider}' not available")
    
    async def _execute_job(self, job_run_id: str, force_reprocess: bool = False):
        """Execute a cronjob (background task)"""
        job_run = self.job_run_repo.get_by_id(job_run_id)
        if not job_run:
            logger.error(f"Job run {job_run_id} not found")
            return
        
        job = self.cronjob_repo.get_by_id(job_run.job_id)
        if not job:
            logger.error(f"Job {job_run.job_id} not found")
            return
        
        try:
            # Update status to running
            self.job_run_repo.update_run_status(job_run_id, 'running', datetime.utcnow())
            logger.info(f"Starting execution of job: {job.name}")
            
            # Initialize providers
            vector_db = self._get_vector_db_instance(job)
            embedding_model = self._get_embedding_model_instance(job)
            
            # Fetch papers from ArXiv
            papers = await self._fetch_papers_from_arxiv(job)
            self.job_run_repo.update(job_run_id, papers_found=len(papers))
            
            if not papers:
                self.job_run_repo.update_run_status(
                    job_run_id, 'completed', datetime.utcnow()
                )
                self.job_run_repo.update(
                    job_run_id, 
                    execution_log={"message": "No new papers found"}
                )
                logger.info(f"Job {job.name} completed: no new papers found")
                return
            
            # Filter out existing papers unless force_reprocess is True
            if not force_reprocess:
                papers = self._filter_existing_papers(papers)
                skipped_count = self.job_run_repo.get_by_id(job_run_id).papers_found - len(papers)
                self.job_run_repo.update(job_run_id, papers_skipped=skipped_count)
            
            # Process papers using batch processor
            batch_processor = BatchProcessorFactory.create_balanced_processor(
                embedding_model=embedding_model,
                vector_db=vector_db
            )
            
            try:
                # Process all papers in batches
                processing_stats = await batch_processor.process_papers_batch(papers)
                
                # Update paper records in SQL database for successfully processed papers
                for paper in papers:
                    try:
                        self._save_paper_to_sql(paper, job.embedding_provider, job.embedding_model)
                    except Exception as e:
                        logger.error(f"Error saving paper {paper.arxiv_id} to SQL: {e}")
                
                # Update job run with final statistics
                self.job_run_repo.update(
                    job_run_id,
                    papers_processed=processing_stats['papers_processed'],
                    papers_embedded=processing_stats['papers_embedded'],
                    embedding_errors=processing_stats['embedding_errors'],
                    vector_db_errors=processing_stats['storage_errors'],
                    execution_log={
                        "total_papers": len(papers),
                        "processed": processing_stats['papers_processed'],
                        "embedded": processing_stats['papers_embedded'],
                        "embedding_errors": processing_stats['embedding_errors'],
                        "vector_errors": processing_stats['storage_errors'],
                        "total_chunks": processing_stats.get('total_chunks', 0),
                        "processing_time": processing_stats.get('processing_time', 0),
                        "vector_db_provider": job.vector_db_provider,
                        "embedding_provider": job.embedding_provider,
                        "embedding_model": job.embedding_model
                    }
                )
                
                status = 'completed' if processing_stats['papers_processed'] > 0 else 'partial'
                self.job_run_repo.update_run_status(job_run_id, status, datetime.utcnow())
                
                logger.info(f"Completed job: {job.name}. Processed {processing_stats['papers_processed']}/{len(papers)} papers")
                
            except Exception as e:
                logger.error(f"Error in batch processing: {e}")
                self.job_run_repo.update_run_status(
                    job_run_id, 'failed', datetime.utcnow(), str(e)
                )
            
        except Exception as e:
            # Handle job failure
            self.job_run_repo.update_run_status(
                job_run_id, 'failed', datetime.utcnow(), str(e)
            )
            self.job_run_repo.update(
                job_run_id,
                execution_log={
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            logger.error(f"Job {job.name} failed: {e}")
    
    async def execute_job_async(self, cronjob: 'CronJob', job_run: 'JobRun', 
                               progress_callback=None) -> Dict[str, Any]:
        """Execute a cronjob asynchronously with progress tracking"""
        try:
            logger.info(f"Starting async execution of job: {cronjob.name}")
            
            # Update status to running
            self.job_run_repo.update_run_status(str(job_run.id), 'running', datetime.utcnow())
            
            if progress_callback:
                progress_callback(1, "Initializing job execution...")
            
            # Initialize providers
            vector_db = self._get_vector_db_instance(cronjob)
            embedding_model = self._get_embedding_model_instance(cronjob)
            
            if progress_callback:
                progress_callback(2, "Fetching papers from arXiv...")
            
            # Fetch papers from ArXiv
            papers = await self._fetch_papers_from_arxiv(cronjob)
            self.job_run_repo.update(str(job_run.id), papers_found=len(papers))
            
            if not papers:
                if progress_callback:
                    progress_callback(5, "Job completed - no new papers found")
                
                return {
                    "papers_processed": 0,
                    "papers_embedded": 0,
                    "embedding_errors": 0,
                    "storage_errors": 0,
                    "message": "No new papers found"
                }
            
            if progress_callback:
                progress_callback(3, f"Processing {len(papers)} papers...")
            
            # Filter out existing papers unless force_reprocess is True
            force_reprocess = job_run.user_params.get('force_reprocess', False) if job_run.user_params else False
            if not force_reprocess and self.paper_repo:
                papers = self._filter_existing_papers(papers)
                skipped_count = job_run.papers_found - len(papers)
                self.job_run_repo.update(str(job_run.id), papers_skipped=skipped_count)
                
                if progress_callback:
                    progress_callback(3, f"Processing {len(papers)} new papers (skipped {skipped_count} existing)...")
            
            # Process papers using batch processor
            from api.batch_processor import BatchProcessorFactory
            batch_processor = BatchProcessorFactory.create_balanced_processor(
                embedding_model=embedding_model,
                vector_db=vector_db
            )
            
            if progress_callback:
                progress_callback(4, "Embedding and storing papers...")
            
            # Process all papers in batches
            processing_stats = await batch_processor.process_papers_batch(papers)
            
            # Update paper records in SQL database for successfully processed papers
            if self.paper_repo:
                for paper in papers:
                    try:
                        self._save_paper_to_sql(paper, cronjob.embedding_provider, cronjob.embedding_model)
                    except Exception as e:
                        logger.error(f"Error saving paper {paper.arxiv_id} to SQL: {e}")
            
            if progress_callback:
                progress_callback(5, f"Job completed successfully - processed {processing_stats['papers_processed']} papers")
            
            # Return final statistics
            return {
                "papers_processed": processing_stats['papers_processed'],
                "papers_embedded": processing_stats['papers_embedded'],
                "embedding_errors": processing_stats['embedding_errors'],
                "storage_errors": processing_stats['storage_errors'],
                "total_chunks": processing_stats.get('total_chunks', 0),
                "processing_time": processing_stats.get('processing_time', 0),
                "vector_db_provider": cronjob.vector_db_provider,
                "embedding_provider": cronjob.embedding_provider,
                "embedding_model": cronjob.embedding_model
            }
            
        except Exception as e:
            logger.error(f"Async job execution failed: {e}")
            raise
    
    def _get_vector_db_instance(self, job: CronJob):
        """Get vector database instance for the job"""
        config = job.vector_db_config or {}
        config['provider'] = job.vector_db_provider
        
        # Add environment-based configuration for Pinecone
        if job.vector_db_provider == 'pinecone':
            import os
            config.update({
                'api_key': os.getenv('PINECONE_API_KEY'),
                'index_name': os.getenv('PINECONE_INDEX_NAME', 'research-papers'),
                'environment': os.getenv('PINECONE_ENVIRONMENT', 'us-west1-gcp'),
                'dimension': int(os.getenv('PINECONE_DIMENSION', '384'))
            })
            logger.info(f"Pinecone config: api_key={'*' * 10 if config.get('api_key') else 'NOT_FOUND'}, index_name={config.get('index_name')}, environment={config.get('environment')}")
        
        return VectorDBFactory.create(job.vector_db_provider, config)
    
    def _get_embedding_model_instance(self, job: CronJob):
        """Get embedding model instance for the job"""
        config = {
            'provider': job.embedding_provider,
            'model_name': job.embedding_model
        }
        
        # Add API keys from environment if available
        import os
        if job.embedding_provider == 'openai':
            config['api_key'] = os.getenv('OPENAI_API_KEY')
        elif job.embedding_provider == 'deepseek':
            config['api_key'] = os.getenv('DEEPSEEK_API_KEY')
        elif job.embedding_provider == 'anthropic':
            config['api_key'] = os.getenv('ANTHROPIC_API_KEY')
        
        return EmbeddingModelFactory.create(job.embedding_provider, job.embedding_model, config)
    
    async def _fetch_papers_from_arxiv(self, job: CronJob) -> List:
        """Fetch papers from ArXiv based on job keywords using enhanced search"""
        try:
            logger.info(f"Fetching papers for job: {job.name} with keywords: {job.keywords}")
            
            # Use enhanced keyword search with OR operator to find papers matching any keyword
            papers = self.arxiv_client.search_papers_by_keywords(
                keywords=job.keywords,
                operator=SearchOperator.OR,
                search_filter=SearchFilter(
                    date_range=DateRange.LAST_MONTH  # Focus on recent papers
                ),
                max_results=job.max_papers_per_run
            )
            
            # Additional search for trending papers in the last week
            trending_papers = self.arxiv_client.search_trending_papers(
                keywords=job.keywords,
                days_back=7,
                max_results=min(20, job.max_papers_per_run // 2)  # Up to 20 trending papers
            )
            
            # Combine and deduplicate
            all_papers = papers + trending_papers
            seen_ids = set()
            unique_papers = []
            
            for paper in all_papers:
                if paper.arxiv_id not in seen_ids:
                    seen_ids.add(paper.arxiv_id)
                    unique_papers.append(paper)
            
            # Limit to max papers per run
            final_papers = unique_papers[:job.max_papers_per_run]
            
            logger.info(f"Found {len(final_papers)} unique papers for job {job.name}")
            return final_papers
            
        except Exception as e:
            logger.error(f"Error fetching papers from ArXiv: {e}")
            raise
    
    def _filter_existing_papers(self, papers: List) -> List:
        """Filter out papers that already exist in the database"""
        if not self.paper_repo:
            return papers
            
        new_papers = []
        for paper in papers:
            if not self.paper_repo.arxiv_id_exists(paper.arxiv_id):
                new_papers.append(paper)
        
        logger.info(f"Filtered out {len(papers) - len(new_papers)} existing papers")
        return new_papers
    
    def _save_paper_to_sql(self, paper, embedding_provider: str, embedding_model: str):
        """Save paper metadata to SQL database"""
        if not self.paper_repo:
            return
            
        try:
            # Check if paper already exists
            existing_paper = self.paper_repo.get_by_arxiv_id(paper.arxiv_id)
            
            if existing_paper:
                # Update embedding metadata
                self.paper_repo.update_embedding_status(
                    existing_paper.id,
                    'completed',
                    provider=embedding_provider,
                    model=embedding_model
                )
            else:
                # Create new paper record
                self.paper_repo.create(
                    id=paper.id,
                    arxiv_id=paper.arxiv_id,
                    title=paper.title,
                    authors=paper.authors,
                    abstract=paper.abstract,
                    summary=paper.summary,
                    categories=paper.categories,
                    published=paper.published,
                    pdf_url=paper.pdf_url,
                    entry_id=paper.entry_id,
                    doi=getattr(paper, 'doi', None),
                    embedding_provider=embedding_provider,
                    embedding_model=embedding_model,
                    embedding_status='completed',
                    last_embedded_at=datetime.utcnow()
                )
            
        except Exception as e:
            logger.error(f"Error saving paper {paper.arxiv_id} to SQL database: {e}")
            raise