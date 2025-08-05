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

from retrieval.arxiv_api_client import ArxivAPIClient, Paper, SearchOperator, SearchFilter, DateRange
from storage.storage_manager import create_storage_manager
from database.database_adapter import create_database_manager
from dotenv import load_dotenv

# Note: PaperDatabase class replaced by DatabaseManager (unified adapter)

class SimplePaperFetcher:
    """Main class for fetching and managing papers"""
    
    def __init__(self, config_path: str = "config.yaml"):
        # Load environment variables first
        load_dotenv()
        
        self.config = self._load_config(config_path)
        self._setup_logging()
        
        # Initialize components with unified database manager
        self.database = create_database_manager(self.config)
        
        self.arxiv_client = ArxivAPIClient(
            max_results=self.config['search']['max_papers_per_run'],
            delay=self.config['advanced']['request_delay']
        )
        
        # Initialize storage manager (supports both local and OSS)
        self.storage_manager = create_storage_manager(self.config['pdf_storage'])
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file with environment variable substitution"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Substitute environment variables in the format ${VAR_NAME}
                import re
                def replace_env_var(match):
                    var_name = match.group(1)
                    return os.environ.get(var_name, match.group(0))
                
                content = re.sub(r'\$\{([^}]+)\}', replace_env_var, content)
                
                return yaml.safe_load(content)
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
        
        # Get categories and sort by
        categories = self.config['search'].get('categories')
        sort_by = self.config['search'].get('sort_by', 'submittedDate').lower()
        
        # Map sort options to API format
        sort_mapping = {
            'relevance': 'relevance',
            'lastupdateddate': 'lastUpdatedDate', 
            'submitteddate': 'submittedDate'
        }
        sort_by = sort_mapping.get(sort_by, 'submittedDate')
        
        # Search for papers
        logging.info(f"Searching for papers with keywords: {keywords}")
        
        if days_back > 0:
            # Use recent search for date filtering
            papers = self.arxiv_client.search_recent_papers(
                keywords=keywords,
                days_back=days_back,
                categories=categories,
                max_results=max_papers
            )
        else:
            # Use regular search
            papers = self.arxiv_client.search_papers(
                keywords=keywords,
                categories=categories,
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
                # Download and store PDF using storage manager
                success, pdf_path = self.storage_manager.download_and_store_pdf(
                    paper, 
                    timeout=self.config['advanced']['download_timeout']
                )
                
                if not success:
                    logging.error(f"Failed to download/store PDF for {paper.arxiv_id}")
                    continue
                
                # Store in database using unified adapter
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
        
        # Get database info
        db_info = self.database.get_database_info()
        
        return {
            'total_papers': total_papers,
            'papers_this_week': len(recent_papers),
            'recent_papers': recent_papers[:10],  # Show last 10
            'database_type': db_info.get('adapter_type', 'Unknown')
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