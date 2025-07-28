import arxiv
import logging
from typing import List, Dict, Optional, Any, Iterator, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import time
import re
from enum import Enum

logger = logging.getLogger(__name__)

class SearchOperator(Enum):
    """Search operators for combining keywords"""
    AND = "AND"
    OR = "OR"
    NOT = "NOT"

class DateRange(Enum):
    """Predefined date ranges for search"""
    LAST_DAY = 1
    LAST_WEEK = 7
    LAST_MONTH = 30
    LAST_3_MONTHS = 90
    LAST_6_MONTHS = 180
    LAST_YEAR = 365

@dataclass
class SearchFilter:
    """Advanced search filter configuration"""
    categories: Optional[List[str]] = None
    authors: Optional[List[str]] = None
    date_range: Optional[Union[DateRange, int]] = None
    exclude_keywords: Optional[List[str]] = None
    title_only: bool = False
    abstract_only: bool = False

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
    arxiv_id: str = ""
    doi: Optional[str] = None
    
    def __post_init__(self):
        """Set arxiv_id from entry_id if not provided"""
        if not self.arxiv_id and self.entry_id:
            self.arxiv_id = self.entry_id.split('/')[-1]

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
        paper_id = result.entry_id.split('/')[-1]
        return Paper(
            id=paper_id,
            title=result.title,
            authors=[author.name for author in result.authors],
            abstract=result.summary,
            categories=result.categories,
            published=result.published,
            updated=result.updated,
            pdf_url=result.pdf_url,
            entry_id=result.entry_id,
            summary=result.summary,
            arxiv_id=paper_id,
            doi=getattr(result, 'doi', None)
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
    
    # Enhanced keyword search methods for cronjob system
    
    def build_advanced_query(self, 
                           keywords: List[str], 
                           operator: SearchOperator = SearchOperator.OR,
                           search_filter: Optional[SearchFilter] = None) -> str:
        """
        Build advanced search query from keywords and filters
        
        Args:
            keywords: List of keywords to search for
            operator: How to combine keywords (AND, OR, NOT)
            search_filter: Additional search filters
            
        Returns:
            Formatted search query string
        """
        if not keywords:
            raise ValueError("At least one keyword is required")
        
        # Clean and prepare keywords
        cleaned_keywords = [self._clean_keyword(keyword) for keyword in keywords]
        
        # Build base query with operator
        if operator == SearchOperator.AND:
            base_query = " AND ".join([f'"{keyword}"' for keyword in cleaned_keywords])
        elif operator == SearchOperator.OR:
            base_query = " OR ".join([f'"{keyword}"' for keyword in cleaned_keywords])
        else:  # NOT
            if len(cleaned_keywords) > 1:
                excluded_terms = " OR ".join([f'"{kw}"' for kw in cleaned_keywords[1:]])
                base_query = f'"{cleaned_keywords[0]}" NOT ({excluded_terms})'
            else:
                base_query = f'NOT "{cleaned_keywords[0]}"'
        
        query_parts = [f"({base_query})"]
        
        # Apply search filters
        if search_filter:
            # Category filter
            if search_filter.categories:
                category_filter = " OR ".join([f"cat:{cat}" for cat in search_filter.categories])
                query_parts.append(f"({category_filter})")
            
            # Author filter
            if search_filter.authors:
                author_filter = " OR ".join([f"au:\"{author}\"" for author in search_filter.authors])
                query_parts.append(f"({author_filter})")
            
            # Date range filter
            if search_filter.date_range:
                days_back = search_filter.date_range.value if isinstance(search_filter.date_range, DateRange) else search_filter.date_range
                query_parts.append(f"submittedDate:[{days_back} days ago TO now]")
            
            # Exclude keywords
            if search_filter.exclude_keywords:
                exclude_filter = " OR ".join([f'"{kw}"' for kw in search_filter.exclude_keywords])
                query_parts.append(f"NOT ({exclude_filter})")
            
            # Title/abstract only filters
            if search_filter.title_only:
                # Modify base query to search only in title
                title_query = " OR ".join([f"ti:\"{keyword}\"" for keyword in cleaned_keywords])
                query_parts[0] = f"({title_query})"
            elif search_filter.abstract_only:
                # Modify base query to search only in abstract
                abstract_query = " OR ".join([f"abs:\"{keyword}\"" for keyword in cleaned_keywords])
                query_parts[0] = f"({abstract_query})"
        
        final_query = " AND ".join(query_parts)
        logger.info(f"Built advanced query: {final_query}")
        return final_query
    
    def _clean_keyword(self, keyword: str) -> str:
        """Clean and normalize keyword for search"""
        # Remove extra whitespace and normalize
        cleaned = re.sub(r'\s+', ' ', keyword.strip())
        
        # Escape special characters that might break the query
        special_chars = r'[+\-&|!(){}[\]^"~*?:\\]'
        cleaned = re.sub(special_chars, lambda m: f'\\{m.group(0)}', cleaned)
        
        return cleaned
    
    def search_papers_by_keywords(self, 
                                keywords: List[str],
                                operator: SearchOperator = SearchOperator.OR,
                                search_filter: Optional[SearchFilter] = None,
                                max_results: Optional[int] = None,
                                sort_by: arxiv.SortCriterion = arxiv.SortCriterion.Relevance) -> List[Paper]:
        """
        Search papers using multiple keywords with advanced filtering
        
        Args:
            keywords: List of keywords to search for
            operator: How to combine keywords (AND, OR, NOT)
            search_filter: Additional search filters
            max_results: Maximum number of results
            sort_by: Sort criterion for results
            
        Returns:
            List of Paper objects
        """
        try:
            # Build advanced query
            query = self.build_advanced_query(keywords, operator, search_filter)
            
            # Execute search
            papers = self.search_papers_with_pagination(query, max_results, sort_by)
            
            logger.info(f"Found {len(papers)} papers for keywords: {keywords}")
            return papers
            
        except Exception as e:
            logger.error(f"Error searching papers by keywords {keywords}: {e}")
            return []
    
    def search_papers_by_topic(self, 
                              topic: str,
                              related_terms: Optional[List[str]] = None,
                              categories: Optional[List[str]] = None,
                              max_results: Optional[int] = None,
                              recent_only: bool = False) -> List[Paper]:
        """
        Search papers by topic with automatic term expansion
        
        Args:
            topic: Main topic to search for
            related_terms: Additional related terms
            categories: Specific arXiv categories to search in
            max_results: Maximum number of results
            recent_only: Whether to search only recent papers (last 30 days)
            
        Returns:
            List of Paper objects
        """
        try:
            # Build keywords list
            keywords = [topic]
            if related_terms:
                keywords.extend(related_terms)
            
            # Build search filter
            search_filter = SearchFilter(
                categories=categories,
                date_range=DateRange.LAST_MONTH if recent_only else None
            )
            
            # Search with OR operator to find papers matching any of the terms
            papers = self.search_papers_by_keywords(
                keywords=keywords,
                operator=SearchOperator.OR,
                search_filter=search_filter,
                max_results=max_results
            )
            
            logger.info(f"Found {len(papers)} papers for topic: {topic}")
            return papers
            
        except Exception as e:
            logger.error(f"Error searching papers by topic {topic}: {e}")
            return []
    
    def search_trending_papers(self, 
                             keywords: List[str],
                             days_back: int = 7,
                             max_results: Optional[int] = None) -> List[Paper]:
        """
        Search for trending papers (recent papers with keywords)
        
        Args:
            keywords: Keywords to search for
            days_back: Number of days to look back
            max_results: Maximum number of results
            
        Returns:
            List of recent Paper objects sorted by submission date
        """
        try:
            search_filter = SearchFilter(date_range=days_back)
            
            papers = self.search_papers_by_keywords(
                keywords=keywords,
                operator=SearchOperator.OR,
                search_filter=search_filter,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.SubmittedDate
            )
            
            logger.info(f"Found {len(papers)} trending papers for keywords: {keywords}")
            return papers
            
        except Exception as e:
            logger.error(f"Error searching trending papers: {e}")
            return []
    
    def search_papers_with_exclusions(self, 
                                    include_keywords: List[str],
                                    exclude_keywords: List[str],
                                    max_results: Optional[int] = None) -> List[Paper]:
        """
        Search papers with explicit inclusion and exclusion keywords
        
        Args:
            include_keywords: Keywords that must be present
            exclude_keywords: Keywords to exclude
            max_results: Maximum number of results
            
        Returns:
            List of Paper objects
        """
        try:
            search_filter = SearchFilter(exclude_keywords=exclude_keywords)
            
            papers = self.search_papers_by_keywords(
                keywords=include_keywords,
                operator=SearchOperator.OR,
                search_filter=search_filter,
                max_results=max_results
            )
            
            logger.info(f"Found {len(papers)} papers with inclusions: {include_keywords}, exclusions: {exclude_keywords}")
            return papers
            
        except Exception as e:
            logger.error(f"Error searching papers with exclusions: {e}")
            return []
    
    def get_paper_statistics(self, keywords: List[str], days_back: int = 30) -> Dict[str, Any]:
        """
        Get statistics about papers matching keywords
        
        Args:
            keywords: Keywords to search for
            days_back: Number of days to analyze
            
        Returns:
            Dictionary with statistics
        """
        try:
            # Get papers for the specified period
            search_filter = SearchFilter(date_range=days_back)
            papers = self.search_papers_by_keywords(
                keywords=keywords,
                operator=SearchOperator.OR,
                search_filter=search_filter,
                max_results=1000  # Large number to get comprehensive stats
            )
            
            if not papers:
                return {
                    'total_papers': 0,
                    'keywords': keywords,
                    'period_days': days_back,
                    'categories': {},
                    'authors': {},
                    'daily_count': 0
                }
            
            # Analyze categories
            category_counts = {}
            for paper in papers:
                for category in paper.categories:
                    category_counts[category] = category_counts.get(category, 0) + 1
            
            # Analyze authors
            author_counts = {}
            for paper in papers:
                for author in paper.authors:
                    author_counts[author] = author_counts.get(author, 0) + 1
            
            # Get top categories and authors
            top_categories = dict(sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:10])
            top_authors = dict(sorted(author_counts.items(), key=lambda x: x[1], reverse=True)[:10])
            
            return {
                'total_papers': len(papers),
                'keywords': keywords,
                'period_days': days_back,
                'daily_average': len(papers) / days_back,
                'categories': top_categories,
                'authors': top_authors,
                'date_range': {
                    'earliest': min(papers, key=lambda p: p.published).published.isoformat(),
                    'latest': max(papers, key=lambda p: p.published).published.isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting paper statistics: {e}")
            return {'error': str(e)}