"""
Dependency injection setup for FastAPI.
"""
from functools import lru_cache
from fastapi import Depends
from sqlalchemy.orm import Session
from database.database import get_database
from repositories.cronjob_repository import CronJobRepository
from repositories.paper_repository import PaperRepository
from repositories.job_run_repository import JobRunRepository
from config import Config

# Database dependencies
def get_db_session() -> Session:
    """Get database session"""
    db = get_database()
    return db.get_session_direct()

def get_database_manager():
    """Get database manager"""
    return get_database()

# Repository dependencies
def get_cronjob_repository(session: Session = None) -> CronJobRepository:
    """Get cronjob repository"""
    if session is None:
        session = get_db_session()
    return CronJobRepository(session)

def get_paper_repository(session: Session = None) -> PaperRepository:
    """Get paper repository"""
    if session is None:
        session = get_db_session()
    return PaperRepository(session)

def get_job_run_repository(session: Session = None) -> JobRunRepository:
    """Get job run repository"""
    if session is None:
        session = get_db_session()
    return JobRunRepository(session)

# Service dependencies (moved to avoid circular imports)
def get_cronjob_service():
    """Get cronjob service with injected dependencies"""
    from services.cronjob_service import CronJobService
    
    session = get_db_session()
    cronjob_repo = CronJobRepository(session)
    job_run_repo = JobRunRepository(session)
    paper_repo = PaperRepository(session)
    
    return CronJobService(
        cronjob_repository=cronjob_repo,
        job_run_repository=job_run_repo,
        paper_repository=paper_repo,
        session=session
    )

def get_research_service():
    """Get research service"""
    from services.research_service import ResearchService
    return ResearchService()

# Orchestrator dependency (cached)
_orchestrator = None

def get_orchestrator():
    """Get research orchestrator (singleton)"""
    global _orchestrator
    if _orchestrator is None:
        from agents.orchestrator import ResearchOrchestrator
        _orchestrator = ResearchOrchestrator(
            openai_api_key=Config.OPENAI_API_KEY,
            deepseek_api_key=Config.DEEPSEEK_API_KEY,
            anthropic_api_key=Config.ANTHROPIC_API_KEY,
            default_provider=Config.DEFAULT_PROVIDER,
            agent_configs=Config.get_all_agent_configs(),
            db_path=Config.VECTOR_DB_PATH
        )
    return _orchestrator