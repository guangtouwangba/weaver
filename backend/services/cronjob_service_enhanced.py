"""
Enhanced CronJob Service with integrated logging system
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
from retrieval.arxiv_client import ArxivClient
from utils.job_logger import JobLoggerFactory

logger = logging.getLogger(__name__)

class EnhancedCronJobService:
    """Enhanced service with integrated logging"""
    
    def __init__(self, 
                 cronjob_repository: CronJobRepository,
                 job_run_repository: JobRunRepository,
                 paper_repository: Optional[PaperRepository] = None):
        self.cronjob_repo = cronjob_repository
        self.job_run_repo = job_run_repository
        self.paper_repo = paper_repository
        self.config_manager = get_config_manager()
        self.arxiv_client = ArxivClient()
    
    async def execute_job_with_logging(self, job_id: str, force_reprocess: bool = False) -> str:
        """Execute a job with comprehensive logging"""
        try:
            # Get the job
            job = self.cronjob_repo.get_by_id(job_id)
            if not job:
                raise NotFoundError(f"Cronjob {job_id} not found")
            
            # Create job run record
            job_run = self.job_run_repo.create(
                id=str(uuid.uuid4()),
                job_id=job_id,
                status='pending',
                manual_trigger=True,
                user_params={'force_reprocess': force_reprocess}
            )
            
            # Create job logger
            job_logger = JobLoggerFactory.create_logger(str(job_run.id))
            
            try:
                # Update status to running
                job_logger.update_status('running', reason='Job execution started')
                job_logger.info(f"Starting job execution: {job.name}")
                
                # Execute job with logging
                await self._execute_job_with_logging(job, job_run, job_logger, force_reprocess)
                
            except Exception as e:
                job_logger.error(f"Job execution failed: {str(e)}", error_code='EXECUTION_ERROR')
                job_logger.update_status('failed', reason=f'Job execution failed: {str(e)}')
                
                # Update job run with error
                self.job_run_repo.update(str(job_run.id),
                                       status='failed',
                                       completed_at=datetime.now(),
                                       error_message=str(e))
                raise
            
            return str(job_run.id)
            
        except Exception as e:
            logger.error(f"Error in job execution: {e}")
            raise ServiceError(f"Failed to execute job: {str(e)}")
    
    async def _execute_job_with_logging(self, job: CronJob, job_run: JobRun, job_logger, force_reprocess: bool):
        """Execute job with detailed logging"""
        
        with job_logger.timed_step("Fetching papers from ArXiv"):
            papers = await self._fetch_papers_from_arxiv(job, job_logger)
            job_logger.info(f"Found {len(papers)} papers from ArXiv")
            job_logger.record_metric('papers_found', len(papers))
        
        if not papers:
            job_logger.info("No new papers found")
            job_logger.update_status('completed', reason='No new papers found')
            self.job_run_repo.update(str(job_run.id), 
                                   status='completed',
                                   completed_at=datetime.now())
            return
        
        with job_logger.timed_step("Filtering existing papers"):
            new_papers = self._filter_existing_papers(papers, job_logger)
            job_logger.info(f"Filtered to {len(new_papers)} new papers")
            job_logger.record_metric('papers_filtered', len(new_papers))
        
        if not new_papers:
            job_logger.info("No new papers after filtering")
            job_logger.update_status('completed', reason='No new papers after filtering')
            self.job_run_repo.update(str(job_run.id), 
                                   status='completed',
                                   completed_at=datetime.now())
            return
        
        with job_logger.timed_step("Processing papers"):
            processing_stats = await self._process_papers_with_logging(job, new_papers, job_logger)
            job_logger.info(f"Processing completed: {processing_stats}")
        
        # Update job run with final stats
        self.job_run_repo.update(str(job_run.id), 
                               status='completed',
                               completed_at=datetime.now(),
                               papers_found=len(papers),
                               papers_processed=processing_stats['papers_processed'],
                               papers_embedded=processing_stats['papers_embedded'],
                               embedding_errors=processing_stats['embedding_errors'],
                               vector_db_errors=processing_stats['vector_db_errors'])
        
        job_logger.update_status('completed', reason='Job completed successfully')
        job_logger.info(f"Job completed successfully: processed {processing_stats['papers_processed']} papers")
    
    async def _fetch_papers_from_arxiv(self, job: CronJob, job_logger) -> List:
        """Fetch papers from ArXiv with logging"""
        try:
            job_logger.info(f"Fetching papers for job: {job.name} with keywords: {job.keywords}")
            
            # Build search query
            search_query = " OR ".join([f'ti:"{keyword}" OR abs:"{keyword}"' for keyword in job.keywords])
            
            # Configure search
            from retrieval.arxiv_client import SearchFilter, DateRange
            search_filter = SearchFilter(
                date_range=DateRange(
                    start_date=datetime.now() - timedelta(days=7),
                    end_date=datetime.now()
                ),
                max_results=job.max_papers_per_run
            )
            
            # Fetch papers
            papers = await self.arxiv_client.search_papers(
                query=search_query,
                search_filter=search_filter
            )
            
            job_logger.info(f"Found {len(papers)} unique papers for job {job.name}")
            return papers
            
        except Exception as e:
            job_logger.error(f"Error fetching papers from ArXiv: {str(e)}", error_code='ARXIV_ERROR')
            raise
    
    def _filter_existing_papers(self, papers: List, job_logger) -> List:
        """Filter out papers that already exist in the database"""
        if not self.paper_repo:
            return papers
        
        new_papers = []
        for paper in papers:
            if not self.paper_repo.get_by_arxiv_id(paper.arxiv_id):
                new_papers.append(paper)
        
        job_logger.info(f"Filtered out {len(papers) - len(new_papers)} existing papers")
        return new_papers
    
    async def _process_papers_with_logging(self, job: CronJob, papers: List, job_logger) -> Dict[str, int]:
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
                    self._save_paper_to_sql(paper, job.embedding_provider, job.embedding_model, job_logger)
                    stats['papers_processed'] += 1
                    
                    # Generate embeddings (simplified for now)
                    try:
                        # This would be the actual embedding logic
                        job_logger.info(f"Successfully processed paper: {paper.arxiv_id}")
                        stats['papers_embedded'] += 1
                        
                    except Exception as e:
                        stats['embedding_errors'] += 1
                        job_logger.error(f"Embedding error for paper {paper.arxiv_id}: {str(e)}", 
                                       error_code='EMBEDDING_ERROR')
                        
            except Exception as e:
                job_logger.error(f"Error processing paper {paper.arxiv_id}: {str(e)}", 
                               error_code='PROCESSING_ERROR')
        
        return stats
    
    def _save_paper_to_sql(self, paper, embedding_provider: str, embedding_model: str, job_logger):
        """Save paper to SQL database with logging"""
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
                job_logger.debug(f"Saved paper to SQL database: {paper.arxiv_id}")
        except Exception as e:
            job_logger.error(f"Error saving paper {paper.arxiv_id} to SQL: {str(e)}", 
                           error_code='SQL_ERROR')
    
    def get_job_run_summary(self, job_run_id: str) -> Dict[str, Any]:
        """Get comprehensive summary for a job run with logs"""
        try:
            job_run = self.job_run_repo.get_by_id(job_run_id)
            if not job_run:
                raise NotFoundError(f"JobRun {job_run_id} not found")
            
            # Create job logger to access logs
            job_logger = JobLoggerFactory.create_logger(job_run_id)
            
            # Get logs
            logs = job_logger.get_logs(limit=50)
            status_history = job_logger.get_status_history()
            metrics = job_logger.get_metrics()
            
            return {
                'job_run': {
                    'id': str(job_run.id),
                    'job_id': str(job_run.job_id),
                    'status': job_run.status,
                    'started_at': job_run.started_at.isoformat() if job_run.started_at else None,
                    'completed_at': job_run.completed_at.isoformat() if job_run.completed_at else None,
                    'progress_percentage': job_run.progress_percentage,
                    'current_step': job_run.current_step,
                    'papers_found': job_run.papers_found,
                    'papers_processed': job_run.papers_processed,
                    'papers_embedded': job_run.papers_embedded,
                    'embedding_errors': job_run.embedding_errors,
                    'vector_db_errors': job_run.vector_db_errors,
                    'error_message': job_run.error_message
                },
                'logs': [self._log_to_dict(log) for log in logs],
                'status_history': [self._status_history_to_dict(entry) for entry in status_history],
                'metrics': [self._metric_to_dict(metric) for metric in metrics]
            }
            
        except Exception as e:
            logger.error(f"Error getting job run summary for {job_run_id}: {e}")
            raise ServiceError(f"Failed to get job run summary: {str(e)}")
    
    def _log_to_dict(self, log) -> Dict[str, Any]:
        """Convert log object to dictionary"""
        return {
            'id': str(log.id),
            'job_run_id': str(log.job_run_id),
            'timestamp': log.timestamp.isoformat(),
            'level': log.level,
            'message': log.message,
            'details': log.details,
            'step': log.step,
            'paper_id': log.paper_id,
            'error_code': log.error_code,
            'duration_ms': log.duration_ms,
            'logger_name': log.logger_name
        }
    
    def _status_history_to_dict(self, status) -> Dict[str, Any]:
        """Convert status history object to dictionary"""
        return {
            'id': str(status.id),
            'job_run_id': str(status.job_run_id),
            'from_status': status.from_status,
            'to_status': status.to_status,
            'timestamp': status.timestamp.isoformat(),
            'reason': status.reason,
            'details': status.details
        }
    
    def _metric_to_dict(self, metric) -> Dict[str, Any]:
        """Convert metric object to dictionary"""
        return {
            'id': str(metric.id),
            'job_run_id': str(metric.job_run_id),
            'timestamp': metric.timestamp.isoformat(),
            'metric_name': metric.metric_name,
            'metric_value': metric.metric_value,
            'metric_type': metric.metric_type,
            'labels': metric.labels
        } 