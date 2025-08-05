#!/usr/bin/env python3
"""
Unified database adapter for ArXiv Paper Management
Supports both SQLite (local) and Supabase (cloud) backends
"""

import os
import logging
import sqlite3
from typing import List, Dict, Set, Optional, Any, Union
from datetime import datetime, timedelta
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class DatabaseAdapter(ABC):
    """Abstract base class for database adapters"""
    
    @abstractmethod
    def paper_exists(self, arxiv_id: str) -> bool:
        """Check if a paper already exists in the database"""
        pass
    
    @abstractmethod
    def get_existing_arxiv_ids(self) -> Set[str]:
        """Get all existing arXiv IDs from the database"""
        pass
    
    @abstractmethod
    def insert_paper(self, paper_data: Dict[str, Any], pdf_path: Optional[str] = None) -> bool:
        """Insert a new paper into the database"""
        pass
    
    @abstractmethod
    def get_paper_count(self) -> int:
        """Get total number of papers in the database"""
        pass
    
    @abstractmethod
    def get_recent_papers(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get papers added in the last N days"""
        pass
    
    @abstractmethod
    def get_papers_by_keywords(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """Get papers that match the given keywords"""
        pass

class SQLiteAdapter(DatabaseAdapter):
    """SQLite database adapter (backward compatibility)"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize the SQLite database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            # Check if papers table exists
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='papers'")
            table_exists = cursor.fetchone() is not None
            
            if table_exists:
                # Check if categories column exists
                cursor = conn.execute("PRAGMA table_info(papers)")
                columns = [row[1] for row in cursor.fetchall()]
                
                if 'categories' not in columns:
                    conn.execute("ALTER TABLE papers ADD COLUMN categories TEXT DEFAULT ''")
                    
                if 'pdf_path' not in columns:
                    conn.execute("ALTER TABLE papers ADD COLUMN pdf_path TEXT")
                    
                if 'updated_at' not in columns:
                    conn.execute("ALTER TABLE papers ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP")
            else:
                # Create new table with correct structure
                conn.execute("""
                    CREATE TABLE papers (
                        id TEXT PRIMARY KEY,
                        arxiv_id TEXT UNIQUE NOT NULL,
                        title TEXT NOT NULL,
                        authors TEXT NOT NULL,
                        abstract TEXT,
                        categories TEXT NOT NULL,
                        published DATETIME NOT NULL,
                        pdf_url TEXT,
                        pdf_path TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
            
            # Create indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_papers_arxiv_id ON papers(arxiv_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_papers_published ON papers(published)")
            conn.commit()
    
    def paper_exists(self, arxiv_id: str) -> bool:
        """Check if a paper already exists in the database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT 1 FROM papers WHERE arxiv_id = ?", (arxiv_id,))
            return cursor.fetchone() is not None
    
    def get_existing_arxiv_ids(self) -> Set[str]:
        """Get all existing arXiv IDs from the database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT arxiv_id FROM papers")
            return {row[0] for row in cursor.fetchall()}
    
    def insert_paper(self, paper_data: Dict[str, Any], pdf_path: Optional[str] = None) -> bool:
        """Insert a new paper into the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO papers 
                    (id, arxiv_id, title, authors, abstract, categories, published, pdf_url, pdf_path, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    paper_data.get('id', paper_data['arxiv_id']),
                    paper_data['arxiv_id'],
                    paper_data['title'],
                    paper_data['authors'],
                    paper_data.get('abstract', ''),
                    paper_data['categories'],
                    paper_data['published'],
                    paper_data.get('pdf_url', ''),
                    pdf_path or ''
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error inserting paper {paper_data.get('arxiv_id', 'unknown')}: {e}")
            return False
    
    def get_paper_count(self) -> int:
        """Get total number of papers in the database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM papers")
            return cursor.fetchone()[0]
    
    def get_recent_papers(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get papers added in the last N days"""
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM papers 
                WHERE created_at >= ? 
                ORDER BY created_at DESC
            """, (cutoff_date,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_papers_by_keywords(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """Get papers that match the given keywords"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Build WHERE clause for keyword matching
            where_conditions = []
            params = []
            
            for keyword in keywords:
                where_conditions.append("categories LIKE ?")
                params.append(f"%{keyword}%")
            
            where_clause = " OR ".join(where_conditions)
            
            cursor = conn.execute(f"""
                SELECT * FROM papers 
                WHERE {where_clause}
                ORDER BY published DESC
            """, params)
            
            return [dict(row) for row in cursor.fetchall()]

class SupabaseAdapter(DatabaseAdapter):
    """Supabase database adapter"""
    
    def __init__(self, supabase_url: str = None, supabase_key: str = None):
        from .supabase_client import SupabaseClient
        self.client = SupabaseClient(supabase_url, supabase_key)
    
    def paper_exists(self, arxiv_id: str) -> bool:
        """Check if a paper already exists in the database"""
        return self.client.paper_exists(arxiv_id)
    
    def get_existing_arxiv_ids(self) -> Set[str]:
        """Get all existing arXiv IDs from the database"""
        return self.client.get_existing_arxiv_ids()
    
    def insert_paper(self, paper_data: Dict[str, Any], pdf_path: Optional[str] = None) -> bool:
        """Insert a new paper into the database"""
        return self.client.insert_paper(paper_data, pdf_path)
    
    def get_paper_count(self) -> int:
        """Get total number of papers in the database"""
        return self.client.get_paper_count()
    
    def get_recent_papers(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get papers added in the last N days"""
        return self.client.get_recent_papers(days)
    
    def get_papers_by_keywords(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """Get papers that match the given keywords"""
        return self.client.get_papers_by_keywords(keywords)
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        return self.client.get_database_stats()
    
    def migrate_from_sqlite(self, sqlite_db_path: str) -> Dict[str, Any]:
        """Migrate data from SQLite to Supabase"""
        return self.client.migrate_from_sqlite(sqlite_db_path)

class DatabaseManager:
    """Unified database manager that handles both SQLite and Supabase"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.adapter: DatabaseAdapter = self._create_adapter()
        
        logger.info(f"Database manager initialized with {type(self.adapter).__name__}")
    
    def _create_adapter(self) -> DatabaseAdapter:
        """Create appropriate database adapter based on configuration"""
        db_config = self.config.get('database', {})
        db_url = db_config.get('url', 'sqlite:///papers.db')
        
        # Check if Supabase is configured
        supabase_url = os.getenv('SUPABASE_URL') or db_config.get('supabase_url')
        supabase_key = os.getenv('SUPABASE_ANON_KEY') or db_config.get('supabase_key')
        
        # Determine which adapter to use
        if db_config.get('provider', '').lower() == 'supabase':
            if supabase_url and supabase_key:
                logger.info("Using Supabase database adapter")
                return SupabaseAdapter(supabase_url, supabase_key)
            else:
                logger.warning("Supabase provider specified but credentials not found, falling back to SQLite")
        
        # Default to SQLite
        logger.info("Using SQLite database adapter")
        if db_url.startswith('sqlite:///'):
            db_path = db_url.replace('sqlite:///', '')
        else:
            db_path = 'papers.db'
        return SQLiteAdapter(db_path)
    
    def paper_exists(self, arxiv_id: str) -> bool:
        """Check if a paper already exists in the database"""
        return self.adapter.paper_exists(arxiv_id)
    
    def get_existing_arxiv_ids(self) -> Set[str]:
        """Get all existing arXiv IDs from the database"""
        return self.adapter.get_existing_arxiv_ids()
    
    def insert_paper(self, paper, pdf_path: Optional[str] = None) -> bool:
        """Insert a new paper into the database"""
        # Convert Paper object to dict if needed
        if hasattr(paper, '__dict__'):
            paper_data = {
                'id': paper.id,
                'arxiv_id': paper.arxiv_id,
                'title': paper.title,
                'authors': '|'.join(paper.authors) if isinstance(paper.authors, list) else paper.authors,
                'abstract': paper.abstract,
                'categories': '|'.join(paper.categories) if isinstance(paper.categories, list) else paper.categories,
                'published': paper.published.isoformat() if hasattr(paper.published, 'isoformat') else paper.published,
                'pdf_url': paper.pdf_url
            }
        else:
            paper_data = paper
        
        return self.adapter.insert_paper(paper_data, pdf_path)
    
    def get_paper_count(self) -> int:
        """Get total number of papers in the database"""
        return self.adapter.get_paper_count()
    
    def get_recent_papers(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get papers added in the last N days"""
        return self.adapter.get_recent_papers(days)
    
    def get_papers_by_keywords(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """Get papers that match the given keywords"""
        return self.adapter.get_papers_by_keywords(keywords)
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get database information"""
        info = {
            'adapter_type': type(self.adapter).__name__,
            'paper_count': self.get_paper_count()
        }
        
        # Add adapter-specific info
        if isinstance(self.adapter, SupabaseAdapter):
            info.update(self.adapter.get_database_stats())
        
        return info
    
    def migrate_to_supabase(self) -> Dict[str, Any]:
        """Migrate from SQLite to Supabase"""
        if not isinstance(self.adapter, SQLiteAdapter):
            return {'error': 'Migration only supported from SQLite'}
        
        # Create Supabase adapter
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')
        
        if not supabase_url or not supabase_key:
            return {'error': 'Supabase credentials not configured'}
        
        supabase_adapter = SupabaseAdapter(supabase_url, supabase_key)
        return supabase_adapter.migrate_from_sqlite(self.adapter.db_path)

def create_database_manager(config: Dict[str, Any]) -> DatabaseManager:
    """Factory function to create database manager"""
    return DatabaseManager(config)