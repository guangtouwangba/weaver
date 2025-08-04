#!/usr/bin/env python3
"""
Simplified ArXiv Paper Fetcher
Fetches papers based on keywords from config.yaml, deduplicates using SQLite, and downloads PDFs.
"""

import os
import sys
import yaml
import logging
import sqlite3
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Set, Optional
import time
import re
from urllib.parse import urlparse

# Add the backend directory to the path to import existing modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from retrieval.arxiv_client import ArxivClient, Paper, SearchOperator, SearchFilter, DateRange
import arxiv

class PaperDatabase:
    """Simple SQLite database for paper deduplication and metadata storage"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the SQLite database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS papers (
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
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_papers_arxiv_id ON papers(arxiv_id)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_papers_published ON papers(published)
            """)
            
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
    
    def insert_paper(self, paper: Paper, pdf_path: Optional[str] = None):
        """Insert a new paper into the database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO papers 
                (id, arxiv_id, title, authors, abstract, categories, published, pdf_url, pdf_path, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                paper.id,
                paper.arxiv_id,
                paper.title,
                '|'.join(paper.authors),  # Store authors as pipe-separated string
                paper.abstract,
                '|'.join(paper.categories),  # Store categories as pipe-separated string
                paper.published.isoformat(),
                paper.pdf_url,
                pdf_path
            ))
            conn.commit()
    
    def get_paper_count(self) -> int:
        """Get total number of papers in the database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM papers")
            return cursor.fetchone()[0]
    
    def get_recent_papers(self, days: int = 7) -> List[Dict]:
        """Get papers added in the last N days"""
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT arxiv_id, title, authors, published, pdf_path 
                FROM papers 
                WHERE created_at > ? 
                ORDER BY published DESC
            """, (cutoff_date,))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'arxiv_id': row[0],
                    'title': row[1],
                    'authors': row[2].split('|') if row[2] else [],
                    'published': row[3],
                    'pdf_path': row[4]
                })
            return results

class PDFDownloader:
    """Handles PDF download and storage"""
    
    def __init__(self, base_dir: str, create_subdirs: bool = True, 
                 filename_format: str = "{arxiv_id}.pdf", timeout: int = 300):
        self.base_dir = Path(base_dir)
        self.create_subdirs = create_subdirs
        self.filename_format = filename_format
        self.timeout = timeout
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def _safe_filename(self, text: str, max_length: int = 100) -> str:
        """Create a safe filename from text"""
        # Remove invalid characters
        safe = re.sub(r'[<>:"/\\|?*]', '', text)
        # Replace spaces with underscores
        safe = re.sub(r'\s+', '_', safe)
        # Limit length
        if len(safe) > max_length:
            safe = safe[:max_length]
        return safe
    
    def _get_pdf_path(self, paper: Paper) -> Path:
        """Determine the path where the PDF should be stored"""
        # Prepare variables for filename formatting
        format_vars = {
            'arxiv_id': paper.arxiv_id,
            'title_safe': self._safe_filename(paper.title),
            'date': paper.published.strftime('%Y-%m-%d')
        }
        
        filename = self.filename_format.format(**format_vars)
        
        if self.create_subdirs:
            # Create subdirectory by date
            subdir = self.base_dir / paper.published.strftime('%Y-%m-%d')
            subdir.mkdir(parents=True, exist_ok=True)
            return subdir / filename
        else:
            return self.base_dir / filename
    
    def download_pdf(self, paper: Paper) -> Optional[str]:
        """Download PDF for a paper and return the local file path"""
        try:
            pdf_path = self._get_pdf_path(paper)
            
            # Skip if file already exists
            if pdf_path.exists():
                logging.info(f"PDF already exists: {pdf_path}")
                return str(pdf_path)
            
            logging.info(f"Downloading PDF for {paper.arxiv_id}: {paper.title}")
            
            # Download the PDF
            response = requests.get(paper.pdf_url, timeout=self.timeout, stream=True)
            response.raise_for_status()
            
            # Save the PDF
            with open(pdf_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logging.info(f"PDF downloaded successfully: {pdf_path}")
            return str(pdf_path)
            
        except Exception as e:
            logging.error(f"Failed to download PDF for {paper.arxiv_id}: {e}")
            return None

class SimplePaperFetcher:
    """Main class for fetching and managing papers"""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config = self._load_config(config_path)
        self._setup_logging()
        
        # Initialize components
        db_path = self.config['database']['url'].replace('sqlite:///', '')
        self.database = PaperDatabase(db_path)
        
        self.arxiv_client = ArxivClient(
            max_results=self.config['search']['max_papers_per_run'],
            delay=self.config['advanced']['request_delay']
        )
        
        self.pdf_downloader = PDFDownloader(
            base_dir=self.config['pdf_storage']['base_directory'],
            create_subdirs=self.config['pdf_storage']['create_subdirectories'],
            filename_format=self.config['pdf_storage']['filename_format'],
            timeout=self.config['advanced']['download_timeout']
        )
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            sys.exit(1)
    
    def _setup_logging(self):
        """Setup logging configuration"""
        log_config = self.config['logging']
        
        # Setup file handler with rotation
        from logging.handlers import RotatingFileHandler
        
        # Create logs directory if it doesn't exist
        log_dir = Path(log_config['file']).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=getattr(logging, log_config['level']),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                RotatingFileHandler(
                    log_config['file'],
                    maxBytes=log_config['max_file_size_mb'] * 1024 * 1024,
                    backupCount=log_config['backup_count']
                ),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def fetch_papers(self) -> int:
        """Fetch papers based on configuration and return count of new papers"""
        logging.info("Starting paper fetch process")
        
        # Get existing arXiv IDs for deduplication
        existing_ids = self.database.get_existing_arxiv_ids()
        logging.info(f"Found {len(existing_ids)} existing papers in database")
        
        # Build search parameters
        keywords = self.config['search']['keywords']
        max_papers = self.config['search']['max_papers_per_run']
        days_back = self.config['search'].get('days_back', 0)
        
        # Create search filter
        search_filter = None
        if self.config['search'].get('categories'):
            search_filter = SearchFilter(
                categories=self.config['search']['categories'],
                date_range=days_back if days_back > 0 else None
            )
        elif days_back > 0:
            search_filter = SearchFilter(date_range=days_back)
        
        # Determine sort criterion
        sort_mapping = {
            'Relevance': arxiv.SortCriterion.Relevance,
            'LastUpdatedDate': arxiv.SortCriterion.LastUpdatedDate,
            'SubmittedDate': arxiv.SortCriterion.SubmittedDate
        }
        sort_by = sort_mapping.get(
            self.config['search'].get('sort_by', 'SubmittedDate'),
            arxiv.SortCriterion.SubmittedDate
        )
        
        # Search for papers
        logging.info(f"Searching for papers with keywords: {keywords}")
        papers = self.arxiv_client.search_papers_by_keywords(
            keywords=keywords,
            operator=SearchOperator.OR,
            search_filter=search_filter,
            max_results=max_papers,
            sort_by=sort_by
        )
        
        logging.info(f"Found {len(papers)} papers from ArXiv")
        
        # Filter out existing papers
        new_papers = [p for p in papers if p.arxiv_id not in existing_ids]
        logging.info(f"Found {len(new_papers)} new papers after deduplication")
        
        # Process new papers
        new_paper_count = 0
        for paper in new_papers:
            try:
                # Download PDF
                pdf_path = self.pdf_downloader.download_pdf(paper)
                
                # Store in database
                self.database.insert_paper(paper, pdf_path)
                new_paper_count += 1
                
                logging.info(f"Processed paper {new_paper_count}/{len(new_papers)}: {paper.title}")
                
                # Respect rate limits
                if self.config['advanced']['request_delay'] > 0:
                    time.sleep(self.config['advanced']['request_delay'])
                    
            except Exception as e:
                logging.error(f"Error processing paper {paper.arxiv_id}: {e}")
                continue
        
        logging.info(f"Successfully processed {new_paper_count} new papers")
        return new_paper_count
    
    def get_statistics(self) -> Dict:
        """Get statistics about the paper collection"""
        total_papers = self.database.get_paper_count()
        recent_papers = self.database.get_recent_papers(7)
        
        return {
            'total_papers': total_papers,
            'papers_this_week': len(recent_papers),
            'recent_papers': recent_papers[:10]  # Show last 10
        }
    
    def run_once(self):
        """Run the paper fetching process once"""
        try:
            start_time = datetime.now()
            logging.info("=" * 50)
            logging.info("Starting paper fetch run")
            
            new_papers = self.fetch_papers()
            
            end_time = datetime.now()
            duration = end_time - start_time
            
            # Get statistics
            stats = self.get_statistics()
            
            logging.info(f"Fetch run completed in {duration}")
            logging.info(f"New papers: {new_papers}")
            logging.info(f"Total papers in database: {stats['total_papers']}")
            logging.info("=" * 50)
            
            return {
                'success': True,
                'new_papers': new_papers,
                'duration_seconds': duration.total_seconds(),
                'statistics': stats
            }
            
        except Exception as e:
            logging.error(f"Error in fetch run: {e}")
            return {
                'success': False,
                'error': str(e)
            }

def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    else:
        config_path = "config.yaml"
    
    if not os.path.exists(config_path):
        print(f"Configuration file not found: {config_path}")
        print("Please create a config.yaml file or specify the path as an argument.")
        sys.exit(1)
    
    # Create and run the fetcher
    fetcher = SimplePaperFetcher(config_path)
    result = fetcher.run_once()
    
    if result['success']:
        print(f"✓ Successfully processed {result['new_papers']} new papers")
        print(f"✓ Total papers in database: {result['statistics']['total_papers']}")
    else:
        print(f"✗ Error: {result['error']}")
        sys.exit(1)

if __name__ == "__main__":
    main()