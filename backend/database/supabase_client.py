#!/usr/bin/env python3
"""
Supabase database client for ArXiv Paper Management
Provides a unified interface for cloud database operations
"""

import os
import logging
from typing import List, Dict, Set, Optional, Any
from datetime import datetime, timedelta
import uuid

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

logger = logging.getLogger(__name__)

class SupabaseClient:
    """Supabase database client for paper management"""
    
    def __init__(self, supabase_url: str = None, supabase_key: str = None):
        if not SUPABASE_AVAILABLE:
            raise ImportError("supabase library is required. Install with: pip install supabase")
        
        # Get credentials from environment or parameters
        self.supabase_url = supabase_url or os.getenv('SUPABASE_URL')
        # Try service role key first (bypasses RLS), fallback to anon key
        self.supabase_key = (supabase_key or 
                           os.getenv('SUPABASE_SERVICE_ROLE_KEY') or 
                           os.getenv('SUPABASE_ANON_KEY'))
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError(
                "Supabase credentials not found. Please set SUPABASE_URL and "
                "(SUPABASE_ANON_KEY or SUPABASE_SERVICE_ROLE_KEY) in your environment variables or .env file."
            )
        
        # Initialize Supabase client
        try:
            self.client: Client = create_client(self.supabase_url, self.supabase_key)
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            raise
        
        # Test connection
        self._test_connection()
    
    def _test_connection(self):
        """Test Supabase connection"""
        try:
            # Try to read from papers table (will create if not exists)
            result = self.client.table("papers").select("count", count="exact").limit(1).execute()
            logger.info("Supabase connection test successful")
        except Exception as e:
            logger.warning(f"Connection test failed, table may not exist: {e}")
            # This is expected if table doesn't exist yet
    
    def create_papers_table(self):
        """
        Create papers table in Supabase
        Note: This should typically be done via Supabase Dashboard or SQL editor
        """
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS papers (
            id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            arxiv_id TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            authors TEXT NOT NULL,
            abstract TEXT,
            categories TEXT NOT NULL,
            published TIMESTAMP WITH TIME ZONE NOT NULL,
            pdf_url TEXT,
            pdf_path TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        -- Create indexes
        CREATE INDEX IF NOT EXISTS idx_papers_arxiv_id ON papers(arxiv_id);
        CREATE INDEX IF NOT EXISTS idx_papers_published ON papers(published);
        CREATE INDEX IF NOT EXISTS idx_papers_categories ON papers(categories);
        
        -- Enable Row Level Security
        ALTER TABLE papers ENABLE ROW LEVEL SECURITY;
        
        -- Create policy for public read access (adjust as needed)
        CREATE POLICY IF NOT EXISTS "Public read access" ON papers
            FOR SELECT TO anon, authenticated
            USING (true);
        
        -- Create policy for authenticated write access
        CREATE POLICY IF NOT EXISTS "Authenticated write access" ON papers
            FOR ALL TO authenticated
            USING (true);
        """
        
        logger.info("To create the papers table, run this SQL in your Supabase SQL editor:")
        logger.info(create_table_sql)
        
        return create_table_sql
    
    def paper_exists(self, arxiv_id: str) -> bool:
        """Check if a paper already exists in the database"""
        try:
            result = self.client.table("papers").select("arxiv_id").eq("arxiv_id", arxiv_id).limit(1).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error checking if paper exists: {e}")
            return False
    
    def get_existing_arxiv_ids(self) -> Set[str]:
        """Get all existing arXiv IDs from the database"""
        try:
            result = self.client.table("papers").select("arxiv_id").execute()
            return {row['arxiv_id'] for row in result.data}
        except Exception as e:
            logger.error(f"Error getting existing arXiv IDs: {e}")
            return set()
    
    def insert_paper(self, paper_data: Dict[str, Any], pdf_path: Optional[str] = None) -> bool:
        """Insert a new paper into the database"""
        try:
            # Prepare data for insertion
            insert_data = {
                'id': str(uuid.uuid4()),
                'arxiv_id': paper_data['arxiv_id'],
                'title': paper_data['title'],
                'authors': paper_data['authors'],
                'abstract': paper_data.get('abstract', ''),
                'categories': paper_data['categories'],
                'published': paper_data['published'],
                'pdf_url': paper_data.get('pdf_url', ''),
                'pdf_path': pdf_path or '',
                'updated_at': datetime.utcnow().isoformat()
            }
            
            # Insert or update (upsert)
            result = self.client.table("papers").upsert(
                insert_data,
                on_conflict="arxiv_id"
            ).execute()
            
            if result.data:
                logger.debug(f"Successfully inserted/updated paper: {paper_data['arxiv_id']}")
                return True
            else:
                logger.error(f"Failed to insert paper: {paper_data['arxiv_id']}")
                return False
                
        except Exception as e:
            logger.error(f"Error inserting paper {paper_data.get('arxiv_id', 'unknown')}: {e}")
            return False
    
    def get_paper_count(self) -> int:
        """Get total number of papers in the database"""
        try:
            result = self.client.table("papers").select("count", count="exact").execute()
            return result.count or 0
        except Exception as e:
            logger.error(f"Error getting paper count: {e}")
            return 0
    
    def get_recent_papers(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get papers added in the last N days"""
        try:
            cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
            
            result = self.client.table("papers").select("*").gte("created_at", cutoff_date).order("created_at", desc=True).execute()
            
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting recent papers: {e}")
            return []
    
    def get_papers_by_keywords(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """Get papers that match the given keywords in categories"""
        try:
            # Build query for keyword matching
            query = self.client.table("papers").select("*")
            
            # Add OR conditions for each keyword
            for keyword in keywords:
                query = query.or_(f"categories.ilike.%{keyword}%")
            
            result = query.order("published", desc=True).execute()
            
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting papers by keywords: {e}")
            return []
    
    def get_all_papers(self, limit: int = None) -> List[Dict[str, Any]]:
        """Get all papers from the database"""
        try:
            query = self.client.table("papers").select("*").order("published", desc=True)
            
            if limit:
                query = query.limit(limit)
            
            result = query.execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting all papers: {e}")
            return []
    
    def get_paper_by_arxiv_id(self, arxiv_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific paper by arXiv ID"""
        try:
            result = self.client.table("papers").select("*").eq("arxiv_id", arxiv_id).limit(1).execute()
            
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            logger.error(f"Error getting paper by arXiv ID {arxiv_id}: {e}")
            return None
    
    def update_paper_pdf_path(self, arxiv_id: str, pdf_path: str) -> bool:
        """Update the PDF path for a specific paper"""
        try:
            result = self.client.table("papers").update({
                'pdf_path': pdf_path,
                'updated_at': datetime.utcnow().isoformat()
            }).eq("arxiv_id", arxiv_id).execute()
            
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error updating PDF path for {arxiv_id}: {e}")
            return False
    
    def delete_paper(self, arxiv_id: str) -> bool:
        """Delete a paper from the database"""
        try:
            result = self.client.table("papers").delete().eq("arxiv_id", arxiv_id).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error deleting paper {arxiv_id}: {e}")
            return False
    
    def get_papers_without_pdf(self) -> List[Dict[str, Any]]:
        """Get papers that don't have PDF paths"""
        try:
            result = self.client.table("papers").select("*").or_("pdf_path.is.null,pdf_path.eq.").execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting papers without PDF: {e}")
            return []
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            # Total count
            total_result = self.client.table("papers").select("count", count="exact").execute()
            total_count = total_result.count or 0
            
            # Count with PDFs
            pdf_result = self.client.table("papers").select("count", count="exact").not_.or_("pdf_path.is.null,pdf_path.eq.").execute()
            pdf_count = pdf_result.count or 0
            
            # Recent papers (last 7 days)
            cutoff_date = (datetime.utcnow() - timedelta(days=7)).isoformat()
            recent_result = self.client.table("papers").select("count", count="exact").gte("created_at", cutoff_date).execute()
            recent_count = recent_result.count or 0
            
            return {
                'total_papers': total_count,
                'papers_with_pdf': pdf_count,
                'recent_papers_7d': recent_count,
                'pdf_coverage': (pdf_count / total_count * 100) if total_count > 0 else 0
            }
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {
                'total_papers': 0,
                'papers_with_pdf': 0,
                'recent_papers_7d': 0,
                'pdf_coverage': 0
            }
    
    def migrate_from_sqlite(self, sqlite_db_path: str) -> Dict[str, Any]:
        """Migrate data from SQLite to Supabase"""
        try:
            import sqlite3
            
            migration_stats = {
                'total_papers': 0,
                'migrated_papers': 0,
                'skipped_papers': 0,
                'errors': []
            }
            
            # Connect to SQLite
            with sqlite3.connect(sqlite_db_path) as conn:
                conn.row_factory = sqlite3.Row  # Enable dict-like access
                
                cursor = conn.execute("SELECT * FROM papers")
                papers = cursor.fetchall()
                
                migration_stats['total_papers'] = len(papers)
                
                for paper in papers:
                    try:
                        # Convert SQLite row to dict
                        paper_data = {
                            'arxiv_id': paper['arxiv_id'],
                            'title': paper['title'],
                            'authors': paper['authors'],
                            'abstract': paper['abstract'] or '',
                            'categories': paper['categories'],
                            'published': paper['published'],
                            'pdf_url': paper['pdf_url'] or ''
                        }
                        
                        # Insert into Supabase
                        success = self.insert_paper(paper_data, paper['pdf_path'])
                        
                        if success:
                            migration_stats['migrated_papers'] += 1
                        else:
                            migration_stats['skipped_papers'] += 1
                            
                    except Exception as e:
                        error_msg = f"Failed to migrate paper {paper['arxiv_id']}: {e}"
                        migration_stats['errors'].append(error_msg)
                        migration_stats['skipped_papers'] += 1
                        logger.error(error_msg)
            
            logger.info(f"Migration completed: {migration_stats['migrated_papers']}/{migration_stats['total_papers']} papers migrated")
            return migration_stats
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return {
                'total_papers': 0,
                'migrated_papers': 0,
                'skipped_papers': 0,
                'errors': [str(e)]
            }

# Utility function
def create_supabase_client(supabase_url: str = None, supabase_key: str = None) -> Optional[SupabaseClient]:
    """Create Supabase client with error handling"""
    try:
        return SupabaseClient(supabase_url, supabase_key)
    except Exception as e:
        logger.error(f"Failed to create Supabase client: {e}")
        return None