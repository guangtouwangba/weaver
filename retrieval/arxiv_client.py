import arxiv
import logging
from typing import List, Dict, Optional, Any, Iterator
from dataclasses import dataclass
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import time

logger = logging.getLogger(__name__)

@dataclass
class Paper:
    """Data class representing a research paper"""
    id: str
    title: str
    authors: List[str]
    abstract: str
    categories: List[str]
    published: datetime
    updated: datetime
    pdf_url: str
    entry_id: str
    summary: str = ""
    full_text: str = ""

class ArxivClient:
    """Client for retrieving papers from arXiv with pagination support"""
    
    def __init__(self, max_results: int = 100, batch_size: int = 100, delay: float = 1.0):
        """
        Initialize ArxivClient
        
        Args:
            max_results: Maximum total results to return
            batch_size: Number of results per batch/request (for rate limiting)
            delay: Delay between requests to respect rate limits
        """
        self.max_results = max_results
        self.batch_size = batch_size
        self.delay = delay
        self.client = arxiv.Client()
    
    def _create_paper_from_result(self, result) -> Paper:
        """Helper method to create Paper object from arxiv result"""
        return Paper(
            id=result.entry_id.split('/')[-1],
            title=result.title,
            authors=[author.name for author in result.authors],
            abstract=result.summary,
            categories=result.categories,
            published=result.published,
            updated=result.updated,
            pdf_url=result.pdf_url,
            entry_id=result.entry_id,
            summary=result.summary
        )
    
    def search_papers_with_pagination(self, 
                                    query: str, 
                                    max_results: Optional[int] = None,
                                    sort_by: arxiv.SortCriterion = arxiv.SortCriterion.Relevance) -> List[Paper]:
        """
        Search for papers on arXiv with pagination support
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            sort_by: Sort criterion for results
            
        Returns:
            List of Paper objects
        """
        try:
            max_results = max_results or self.max_results
            papers = []
            
            logger.info(f"Starting search for query: {query}, target results: {max_results}")
            
            # Create search with the total max_results - arxiv library will handle pagination automatically
            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=sort_by
            )
            
            try:
                # Let arxiv library handle pagination automatically
                for result in self.client.results(search):
                    paper = self._create_paper_from_result(result)
                    papers.append(paper)
                    
                    # Log progress every batch_size papers
                    if len(papers) % self.batch_size == 0:
                        logger.info(f"Retrieved {len(papers)} papers so far...")
                    
                    # Respect rate limits by adding small delays
                    if self.delay > 0 and len(papers) % self.batch_size == 0:
                        time.sleep(self.delay)
                    
                    # Stop if we've reached max_results
                    if len(papers) >= max_results:
                        break
                
                logger.info(f"Final result: Retrieved {len(papers)} papers for query: {query}")
                return papers
                
            except Exception as e:
                logger.error(f"Error during search: {e}")
                return papers
            
        except Exception as e:
            logger.error(f"Error searching arXiv: {e}")
            return []
    
    def search_papers(self, 
                     query: str, 
                     max_results: Optional[int] = None,
                     sort_by: arxiv.SortCriterion = arxiv.SortCriterion.Relevance,
                     use_pagination: bool = True) -> List[Paper]:
        """
        Search for papers on arXiv
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            sort_by: Sort criterion for results
            use_pagination: Whether to use pagination for large result sets
            
        Returns:
            List of Paper objects
        """
        if use_pagination:
            return self.search_papers_with_pagination(query, max_results, sort_by)
        else:
            # Original implementation for backward compatibility
            try:
                max_results = max_results or self.max_results
                
                search = arxiv.Search(
                    query=query,
                    max_results=max_results,
                    sort_by=sort_by
                )
                
                papers = []
                for result in self.client.results(search):
                    paper = self._create_paper_from_result(result)
                    papers.append(paper)
                    
                logger.info(f"Retrieved {len(papers)} papers for query: {query}")
                return papers
                
            except Exception as e:
                logger.error(f"Error searching arXiv: {e}")
                return []
    
    def get_papers_by_author_with_pagination(self, author_name: str, max_results: Optional[int] = None) -> List[Paper]:
        """
        Get papers by a specific author with pagination support
        
        Args:
            author_name: Name of the author
            max_results: Maximum number of results
            
        Returns:
            List of Paper objects
        """
        query = f"au:{author_name}"
        return self.search_papers_with_pagination(query, max_results)
    
    def get_papers_by_category_with_pagination(self, category: str, max_results: Optional[int] = None) -> List[Paper]:
        """
        Get papers in a specific category with pagination support
        
        Args:
            category: arXiv category (e.g., 'cs.AI', 'cs.LG')
            max_results: Maximum number of results
            
        Returns:
            List of Paper objects
        """
        query = f"cat:{category}"
        return self.search_papers_with_pagination(query, max_results)
    
    def search_recent_papers_with_pagination(self, 
                                           query: str, 
                                           days_back: int = 30,
                                           max_results: Optional[int] = None) -> List[Paper]:
        """
        Search for recent papers within specified days with pagination support
        
        Args:
            query: Search query
            days_back: Number of days to look back
            max_results: Maximum results to return
            
        Returns:
            List of recent Paper objects
        """
        # Add date filter to query
        date_query = f"{query} AND submittedDate:[{days_back} days ago TO now]"
        return self.search_papers_with_pagination(date_query, max_results)
    
    def get_paper_by_id(self, paper_id: str) -> Optional[Paper]:
        """
        Get a specific paper by its arXiv ID
        
        Args:
            paper_id: arXiv paper ID
            
        Returns:
            Paper object or None if not found
        """
        try:
            search = arxiv.Search(id_list=[paper_id])
            results = list(self.client.results(search))
            
            if not results:
                logger.warning(f"Paper not found: {paper_id}")
                return None
                
            result = results[0]
            paper = self._create_paper_from_result(result)
            
            logger.info(f"Retrieved paper: {paper.title}")
            return paper
            
        except Exception as e:
            logger.error(f"Error retrieving paper {paper_id}: {e}")
            return None
    
    def get_papers_by_author(self, author_name: str, max_results: Optional[int] = None) -> List[Paper]:
        """
        Get papers by a specific author
        
        Args:
            author_name: Name of the author
            max_results: Maximum number of results
            
        Returns:
            List of Paper objects
        """
        query = f"au:{author_name}"
        return self.search_papers(query, max_results)
    
    def get_papers_by_category(self, category: str, max_results: Optional[int] = None) -> List[Paper]:
        """
        Get papers in a specific category
        
        Args:
            category: arXiv category (e.g., 'cs.AI', 'cs.LG')
            max_results: Maximum number of results
            
        Returns:
            List of Paper objects
        """
        query = f"cat:{category}"
        return self.search_papers(query, max_results)
    
    def download_paper_text(self, paper: Paper) -> str:
        """
        Download and extract text from a paper's PDF
        Note: This is a simplified implementation
        For production, consider using PyPDF2, pdfplumber, or similar
        
        Args:
            paper: Paper object
            
        Returns:
            Extracted text content
        """
        try:
            logger.info(f"Downloading text for paper: {paper.title}")
            # For now, return abstract + title as the text content
            # In production, implement PDF text extraction
            full_text = f"Title: {paper.title}\n\nAuthors: {', '.join(paper.authors)}\n\nAbstract: {paper.abstract}"
            paper.full_text = full_text
            return full_text
            
        except Exception as e:
            logger.error(f"Error downloading paper text: {e}")
            return paper.abstract
    
    def search_recent_papers(self, 
                           query: str, 
                           days_back: int = 30,
                           max_results: Optional[int] = None) -> List[Paper]:
        """
        Search for recent papers within specified days
        
        Args:
            query: Search query
            days_back: Number of days to look back
            max_results: Maximum results to return
            
        Returns:
            List of recent Paper objects
        """
        # Add date filter to query
        date_query = f"{query} AND submittedDate:[{days_back} days ago TO now]"
        return self.search_papers(date_query, max_results)