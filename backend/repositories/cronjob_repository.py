"""
Repository for cronjob database operations.
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from database.models import CronJob
from .base import BaseRepository

class CronJobRepository(BaseRepository[CronJob]):
    """Repository for cronjob operations"""
    
    def __init__(self, session: Session):
        super().__init__(session, CronJob)
    
    def get_model_class(self):
        return CronJob
    
    def get_by_name(self, name: str) -> Optional[CronJob]:
        """Get cronjob by name"""
        return self.session.query(CronJob).filter(CronJob.name == name).first()
    
    def get_enabled_jobs(self, skip: int = 0, limit: int = 100) -> List[CronJob]:
        """Get enabled cronjobs"""
        return self.session.query(CronJob).filter(
            CronJob.enabled == True
        ).offset(skip).limit(limit).all()
    
    def get_by_provider(self, embedding_provider: str, vector_db_provider: str, 
                       skip: int = 0, limit: int = 100) -> List[CronJob]:
        """Get cronjobs by providers"""
        return self.session.query(CronJob).filter(
            CronJob.embedding_provider == embedding_provider,
            CronJob.vector_db_provider == vector_db_provider
        ).offset(skip).limit(limit).all()
    
    def name_exists(self, name: str, exclude_id: Optional[str] = None) -> bool:
        """Check if a cronjob name already exists"""
        query = self.session.query(CronJob).filter(CronJob.name == name)
        if exclude_id:
            query = query.filter(CronJob.id != exclude_id)
        return query.first() is not None
    
    def toggle_enabled(self, job_id: str) -> Optional[CronJob]:
        """Toggle the enabled status of a cronjob"""
        job = self.get_by_id(job_id)
        if not job:
            return None
        
        job.enabled = not job.enabled
        self.session.commit()
        self.session.refresh(job)
        return job