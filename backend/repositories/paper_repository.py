"""
Repository for paper database operations.
"""
from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database.models import Paper
from .base import BaseRepository

class PaperRepository(BaseRepository[Paper]):
    """Repository for paper operations"""
    
    def __init__(self, session: Session):
        super().__init__(session, Paper)
    
    def get_model_class(self):
        return Paper
    
    def get_by_arxiv_id(self, arxiv_id: str) -> Optional[Paper]:
        """Get paper by ArXiv ID"""
        return self.session.query(Paper).filter(Paper.arxiv_id == arxiv_id).first()
    
    def get_by_doi(self, doi: str) -> Optional[Paper]:
        """Get paper by DOI"""
        return self.session.query(Paper).filter(Paper.doi == doi).first()
    
    def get_by_embedding_status(self, status: str, skip: int = 0, 
                               limit: int = 100) -> List[Paper]:
        """Get papers by embedding status"""
        return self.session.query(Paper).filter(
            Paper.embedding_status == status
        ).offset(skip).limit(limit).all()
    
    def get_by_provider(self, embedding_provider: str, skip: int = 0, 
                       limit: int = 100) -> List[Paper]:
        """Get papers by embedding provider"""
        return self.session.query(Paper).filter(
            Paper.embedding_provider == embedding_provider
        ).offset(skip).limit(limit).all()
    
    def get_by_categories(self, categories: List[str], skip: int = 0, 
                         limit: int = 100) -> List[Paper]:
        """Get papers by categories"""
        return self.session.query(Paper).filter(
            Paper.categories.overlap(categories)
        ).offset(skip).limit(limit).all()
    
    def get_recent_papers(self, days: int = 30, skip: int = 0, 
                         limit: int = 100) -> List[Paper]:
        """Get papers published in the last N days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return self.session.query(Paper).filter(
            Paper.published >= cutoff_date
        ).order_by(Paper.published.desc()).offset(skip).limit(limit).all()
    
    def arxiv_id_exists(self, arxiv_id: str) -> bool:
        """Check if a paper with the given ArXiv ID exists"""
        return self.session.query(Paper).filter(Paper.arxiv_id == arxiv_id).first() is not None
    
    def update_embedding_status(self, paper_id: str, status: str, 
                               provider: Optional[str] = None,
                               model: Optional[str] = None,
                               vector_id: Optional[str] = None,
                               error: Optional[str] = None) -> Optional[Paper]:
        """Update paper embedding status and metadata"""
        paper = self.get_by_id(paper_id)
        if not paper:
            return None
        
        paper.embedding_status = status
        if provider:
            paper.embedding_provider = provider
        if model:
            paper.embedding_model = model
        if vector_id:
            paper.vector_id = vector_id
        if error:
            paper.embedding_error = error
        
        paper.last_embedded_at = datetime.utcnow()
        
        self.session.commit()
        self.session.refresh(paper)
        return paper
    
    def get_embedding_statistics(self) -> dict:
        """Get embedding statistics"""
        total_papers = self.count()
        pending_papers = self.session.query(Paper).filter(
            Paper.embedding_status == 'pending'
        ).count()
        completed_papers = self.session.query(Paper).filter(
            Paper.embedding_status == 'completed'
        ).count()
        failed_papers = self.session.query(Paper).filter(
            Paper.embedding_status == 'failed'
        ).count()
        
        return {
            "total_papers": total_papers,
            "pending_embeddings": pending_papers,
            "completed_embeddings": completed_papers,
            "failed_embeddings": failed_papers,
            "completion_rate": (completed_papers / total_papers * 100) if total_papers > 0 else 0
        }