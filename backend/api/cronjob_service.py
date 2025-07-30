"""
Cronjob service for managing job execution and scheduling
"""
import logging
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import BackgroundTasks

from database.models import CronJob, JobRun, Paper
from database.config_manager import get_config_manager
from retrieval.arxiv_client import ArxivClient, SearchOperator, SearchFilter, DateRange
from database.embeddings import EmbeddingModelFactory
from database.vector_db import VectorDBFactory
from api.batch_processor import BatchProcessorFactory

logger = logging.getLogger(__name__)

class CronJobService:
    """Service for managing cronjobs and their execution"""
    
    def __init__(self, session: Session):
        self.session = session
        self.config_manager = get_config_manager()
        self.arxiv_client = ArxivClient()
    
    def create_job(self, job_data: Dict[str, Any]) -> CronJob:
        """Create a new cronjob"""
        job = CronJob(
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
        
        self.session.add(job)
        self.session.commit()
        self.session.refresh(job)
        
        logger.info(f"Created cronjob: {job.name} ({job.id})")
        return job
    
    def update_job(self, job_id: str, update_data: Dict[str, Any]) -> Optional[CronJob]:
        """Update an existing cronjob"""
        job = self.session.query(CronJob).filter(CronJob.id == job_id).first()
        if not job:
            return None
        
        # Update fields
        for key, value in update_data.items():
            if hasattr(job, key) and value is not None:
                setattr(job, key, value)
        
        job.updated_at = datetime.utcnow()
        self.session.commit()
        self.session.refresh(job)
        
        logger.info(f"Updated cronjob: {job.name} ({job.id})")
        return job
    
    def delete_job(self, job_id: str) -> bool:
        """Delete a cronjob"""
        job = self.session.query(CronJob).filter(CronJob.id == job_id).first()
        if not job:
            return False
        
        self.session.delete(job)
        self.session.commit()
        
        logger.info(f"Deleted cronjob: {job.name} ({job.id})")
        return True
    
    def trigger_job(self, job_id: str, background_tasks: BackgroundTasks, 
                   force_reprocess: bool = False) -> str:
        """Trigger manual execution of a cronjob"""
        job = self.session.query(CronJob).filter(CronJob.id == job_id).first()
        if not job:
            raise ValueError(f"Cronjob {job_id} not found")
        
        # Create job run record
        job_run = JobRun(
            id=str(uuid.uuid4()),
            job_id=job_id,
            status='pending',
            started_at=datetime.utcnow()
        )
        
        self.session.add(job_run)
        self.session.commit()
        self.session.refresh(job_run)
        
        # Schedule background execution
        background_tasks.add_task(
            self._execute_job,
            job_run.id,
            force_reprocess
        )
        
        logger.info(f"Triggered cronjob: {job.name} ({job.id}), run ID: {job_run.id}")
        return str(job_run.id)
    
    async def _execute_job(self, job_run_id: str, force_reprocess: bool = False):
        """Execute a cronjob (background task)"""
        job_run = self.session.query(JobRun).filter(JobRun.id == job_run_id).first()
        if not job_run:
            logger.error(f"Job run {job_run_id} not found")
            return
        
        job = self.session.query(CronJob).filter(CronJob.id == job_run.job_id).first()
        if not job:
            logger.error(f"Job {job_run.job_id} not found")
            return
        
        try:
            # Update status to running
            job_run.status = 'running'
            job_run.started_at = datetime.utcnow()
            self.session.commit()
            
            logger.info(f"Starting execution of job: {job.name}")
            
            # Initialize providers
            vector_db = self._get_vector_db_instance(job)
            embedding_model = self._get_embedding_model_instance(job)
            
            # Fetch papers from ArXiv
            papers = await self._fetch_papers_from_arxiv(job)
            job_run.papers_found = len(papers)
            
            if not papers:
                job_run.status = 'completed'
                job_run.completed_at = datetime.utcnow()
                job_run.execution_log = {"message": "No new papers found"}
                self.session.commit()
                logger.info(f"Job {job.name} completed: no new papers found")
                return
            
            # Filter out existing papers unless force_reprocess is True
            if not force_reprocess:
                papers = self._filter_existing_papers(papers)
                job_run.papers_skipped = job_run.papers_found - len(papers)
            
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
                
                # Extract statistics from batch processor
                processed_count = processing_stats['papers_processed']
                embedded_count = processing_stats['papers_embedded']
                embedding_errors = processing_stats['embedding_errors']
                vector_errors = processing_stats['storage_errors']
                
                # Update job run progress
                job_run.papers_processed = processed_count
                job_run.papers_embedded = embedded_count
                job_run.embedding_errors = embedding_errors
                job_run.vector_db_errors = vector_errors
                self.session.commit()
                
                logger.info(f"Batch processing completed: {processed_count} processed, "
                           f"{embedded_count} embedded, {processing_stats['total_chunks']} chunks created")
                
            except Exception as e:
                logger.error(f"Error in batch processing: {e}")
                # Get partial stats even if processing failed
                processing_stats = batch_processor.get_processing_stats()
                processed_count = processing_stats['papers_processed']
                embedded_count = processing_stats['papers_embedded']
                embedding_errors = processing_stats['embedding_errors']
                vector_errors = processing_stats['storage_errors']
            
            # Finalize job run
            job_run.papers_processed = processed_count
            job_run.papers_embedded = embedded_count
            job_run.embedding_errors = embedding_errors
            job_run.vector_db_errors = vector_errors
            job_run.status = 'completed' if processed_count > 0 else 'partial'
            job_run.completed_at = datetime.utcnow()
            job_run.execution_log = {
                "total_papers": len(papers),
                "processed": processed_count,
                "embedded": embedded_count,
                "embedding_errors": embedding_errors,
                "vector_errors": vector_errors,
                "total_chunks": processing_stats.get('total_chunks', 0),
                "processing_time": processing_stats.get('processing_time', 0),
                "papers_per_second": processing_stats.get('papers_per_second', 0),
                "chunks_per_second": processing_stats.get('chunks_per_second', 0),
                "embedding_success_rate": processing_stats.get('embedding_success_rate', 0),
                "storage_success_rate": processing_stats.get('storage_success_rate', 0),
                "vector_db_provider": job.vector_db_provider,
                "embedding_provider": job.embedding_provider,
                "embedding_model": job.embedding_model
            }
            
            self.session.commit()
            
            logger.info(f"Completed job: {job.name}. Processed {processed_count}/{len(papers)} papers")
            
        except Exception as e:
            # Handle job failure
            job_run.status = 'failed'
            job_run.completed_at = datetime.utcnow()
            job_run.error_message = str(e)
            job_run.execution_log = {
                "error": str(e),
                "error_type": type(e).__name__
            }
            self.session.commit()
            
            logger.error(f"Job {job.name} failed: {e}")
    
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
            logger.info(f"Regular search: {len(papers)} papers, Trending: {len(trending_papers)} papers")
            
            return final_papers
            
        except Exception as e:
            logger.error(f"Error fetching papers from ArXiv: {e}")
            raise
    
    def _filter_existing_papers(self, papers: List) -> List:
        """Filter out papers that already exist in the database"""
        existing_arxiv_ids = set()
        
        # Get existing arxiv_ids from database
        for paper in papers:
            existing_paper = self.session.query(Paper).filter(
                Paper.arxiv_id == paper.arxiv_id
            ).first()
            if existing_paper:
                existing_arxiv_ids.add(paper.arxiv_id)
        
        # Filter out existing papers
        new_papers = [p for p in papers if p.arxiv_id not in existing_arxiv_ids]
        
        logger.info(f"Filtered out {len(papers) - len(new_papers)} existing papers")
        return new_papers
    
    def _save_paper_to_sql(self, paper, embedding_provider: str, embedding_model: str):
        """Save paper metadata to SQL database"""
        try:
            # Check if paper already exists
            existing_paper = self.session.query(Paper).filter(
                Paper.arxiv_id == paper.arxiv_id
            ).first()
            
            if existing_paper:
                # Update embedding metadata
                existing_paper.embedding_provider = embedding_provider
                existing_paper.embedding_model = embedding_model
                existing_paper.embedding_status = 'completed'
                existing_paper.last_embedded_at = datetime.utcnow()
            else:
                # Create new paper record
                new_paper = Paper(
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
                self.session.add(new_paper)
            
            self.session.commit()
            
        except Exception as e:
            logger.error(f"Error saving paper {paper.arxiv_id} to SQL database: {e}")
            self.session.rollback()
    
    def get_job_statistics(self) -> Dict[str, Any]:
        """Get overall job statistics"""
        try:
            total_jobs = self.session.query(CronJob).count()
            enabled_jobs = self.session.query(CronJob).filter(CronJob.enabled == True).count()
            total_runs = self.session.query(JobRun).count()
            successful_runs = self.session.query(JobRun).filter(JobRun.status == 'completed').count()
            failed_runs = self.session.query(JobRun).filter(JobRun.status == 'failed').count()
            running_jobs = self.session.query(JobRun).filter(JobRun.status == 'running').count()
            
            return {
                "total_jobs": total_jobs,
                "enabled_jobs": enabled_jobs,
                "total_runs": total_runs,
                "successful_runs": successful_runs,
                "failed_runs": failed_runs,
                "running_jobs": running_jobs,
                "success_rate": (successful_runs / total_runs * 100) if total_runs > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting job statistics: {e}")
            return {"error": str(e)}