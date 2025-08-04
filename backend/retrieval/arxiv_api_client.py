#!/usr/bin/env python3
"""
Improved ArXiv API Client using direct HTTP requests to ArXiv's official API
More reliable than the arxiv Python package for search functionality.
"""

import requests
import xml.etree.ElementTree as ET
import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import time
import re
from urllib.parse import quote_plus

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
    arxiv_id: str = ""
    doi: Optional[str] = None
    
    def __post_init__(self):
        """Set arxiv_id from entry_id if not provided"""
        if not self.arxiv_id and self.entry_id:
            self.arxiv_id = self.entry_id.split('/')[-1]
        if not self.summary:
            self.summary = self.abstract

class ArxivAPIClient:
    """
    Direct ArXiv API client using HTTP requests to ArXiv's official API
    More reliable and flexible than the arxiv Python package
    """
    
    def __init__(self, max_results: int = 100, delay: float = 1.0):
        self.max_results = max_results
        self.delay = delay
        self.base_url = "http://export.arxiv.org/api/query"
        
        # ArXiv API namespace
        self.ns = {
            'atom': 'http://www.w3.org/2005/Atom',
            'arxiv': 'http://arxiv.org/schemas/atom'
        }
    
    def _build_search_query(self, keywords: List[str], categories: Optional[List[str]] = None, 
                           title_only: bool = False, abstract_only: bool = False) -> str:
        """Build ArXiv API search query"""
        if not keywords:
            raise ValueError("At least one keyword is required")
        
        # Clean keywords
        cleaned_keywords = [self._clean_keyword(kw) for kw in keywords]
        
        # Build search terms
        search_terms = []
        
        for keyword in cleaned_keywords:
            if title_only:
                search_terms.append(f'ti:"{keyword}"')
            elif abstract_only:
                search_terms.append(f'abs:"{keyword}"')
            else:
                # Search in all fields (title, abstract, etc.)
                search_terms.append(f'all:"{keyword}"')
        
        # Combine with OR
        query_part = " OR ".join(search_terms)
        
        # Add categories if specified
        if categories:
            cat_terms = [f'cat:{cat}' for cat in categories]
            cat_query = " OR ".join(cat_terms)
            query_part = f"({query_part}) AND ({cat_query})"
        
        return query_part
    
    def _clean_keyword(self, keyword: str) -> str:
        """Clean and normalize keyword for search"""
        # Remove extra whitespace and normalize
        cleaned = re.sub(r'\s+', ' ', keyword.strip())
        return cleaned
    
    def _parse_entry(self, entry) -> Paper:
        """Parse XML entry into Paper object"""
        try:
            # Extract basic information
            entry_id = entry.find('atom:id', self.ns).text
            arxiv_id = entry_id.split('/')[-1]
            
            title = entry.find('atom:title', self.ns).text.strip()
            title = re.sub(r'\s+', ' ', title)  # Clean up whitespace
            
            abstract = entry.find('atom:summary', self.ns).text.strip()
            abstract = re.sub(r'\s+', ' ', abstract)  # Clean up whitespace
            
            # Parse authors
            authors = []
            for author in entry.findall('atom:author', self.ns):
                name = author.find('atom:name', self.ns).text
                authors.append(name)
            
            # Parse dates
            published_str = entry.find('atom:published', self.ns).text
            updated_str = entry.find('atom:updated', self.ns).text
            
            published = datetime.fromisoformat(published_str.replace('Z', '+00:00'))
            updated = datetime.fromisoformat(updated_str.replace('Z', '+00:00'))
            
            # Parse categories
            categories = []
            for category in entry.findall('atom:category', self.ns):
                term = category.get('term')
                if term:
                    categories.append(term)
            
            # Get PDF URL
            pdf_url = None
            for link in entry.findall('atom:link', self.ns):
                if link.get('type') == 'application/pdf':
                    pdf_url = link.get('href')
                    break
            
            if not pdf_url:
                # Construct PDF URL from ArXiv ID
                pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
            
            # Get DOI if available
            doi = None
            doi_elem = entry.find('arxiv:doi', self.ns)
            if doi_elem is not None:
                doi = doi_elem.text
            
            return Paper(
                id=arxiv_id,
                title=title,
                authors=authors,
                abstract=abstract,
                categories=categories,
                published=published,
                updated=updated,
                pdf_url=pdf_url,
                entry_id=entry_id,
                arxiv_id=arxiv_id,
                doi=doi,
                summary=abstract
            )
            
        except Exception as e:
            logger.error(f"Error parsing entry: {e}")
            return None
    
    def search_papers(self, keywords: List[str], 
                     categories: Optional[List[str]] = None,
                     max_results: Optional[int] = None,
                     sort_by: str = "relevance",
                     title_only: bool = False,
                     abstract_only: bool = False) -> List[Paper]:
        """
        Search for papers on ArXiv using direct API calls
        
        Args:
            keywords: List of keywords to search for
            categories: ArXiv categories to filter by
            max_results: Maximum number of results
            sort_by: Sort order ('relevance', 'lastUpdatedDate', 'submittedDate')
            title_only: Search only in titles
            abstract_only: Search only in abstracts
            
        Returns:
            List of Paper objects
        """
        try:
            max_results = max_results or self.max_results
            
            # Build search query
            query = self._build_search_query(keywords, categories, title_only, abstract_only)
            
            # Map sort options
            sort_mapping = {
                'relevance': 'relevance',
                'lastUpdatedDate': 'lastUpdatedDate',
                'submittedDate': 'submittedDate'
            }
            sort_order = sort_mapping.get(sort_by, 'relevance')
            
            # Build request parameters
            params = {
                'search_query': query,
                'start': 0,
                'max_results': max_results,
                'sortBy': sort_order,
                'sortOrder': 'descending'
            }
            
            logger.info(f"Searching ArXiv with query: {query}")
            logger.info(f"Parameters: {params}")
            
            # Make API request
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            # Parse XML response
            root = ET.fromstring(response.content)
            
            # Extract papers
            papers = []
            entries = root.findall('atom:entry', self.ns)
            
            logger.info(f"Found {len(entries)} entries from ArXiv API")
            
            for entry in entries:
                paper = self._parse_entry(entry)
                if paper:
                    papers.append(paper)
            
            logger.info(f"Successfully parsed {len(papers)} papers")
            
            # Respect rate limits
            if self.delay > 0:
                time.sleep(self.delay)
            
            return papers
            
        except requests.RequestException as e:
            logger.error(f"Request error: {e}")
            return []
        except ET.ParseError as e:
            logger.error(f"XML parsing error: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return []
    
    def search_recent_papers(self, keywords: List[str], 
                           days_back: int = 7,
                           categories: Optional[List[str]] = None,
                           max_results: Optional[int] = None) -> List[Paper]:
        """
        Search for recent papers within specified days
        
        Args:
            keywords: Keywords to search for
            days_back: Number of days to look back
            categories: ArXiv categories to filter by
            max_results: Maximum results to return
            
        Returns:
            List of recent Paper objects
        """
        # Get all papers first, then filter by date
        papers = self.search_papers(
            keywords=keywords,
            categories=categories,
            max_results=max_results or self.max_results,
            sort_by="submittedDate"
        )
        
        # Filter by date
        cutoff_date = datetime.now() - timedelta(days=days_back)
        recent_papers = [
            paper for paper in papers 
            if paper.published.replace(tzinfo=None) >= cutoff_date
        ]
        
        logger.info(f"Found {len(recent_papers)} recent papers from last {days_back} days")
        return recent_papers
    
    def get_paper_by_id(self, arxiv_id: str) -> Optional[Paper]:
        """
        Get a specific paper by ArXiv ID
        
        Args:
            arxiv_id: ArXiv paper ID (e.g., "2301.12345")
            
        Returns:
            Paper object or None if not found
        """
        try:
            params = {
                'id_list': arxiv_id,
                'max_results': 1
            }
            
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            entries = root.findall('atom:entry', self.ns)
            
            if not entries:
                logger.warning(f"Paper not found: {arxiv_id}")
                return None
            
            paper = self._parse_entry(entries[0])
            if paper:
                logger.info(f"Retrieved paper: {paper.title}")
            
            return paper
            
        except Exception as e:
            logger.error(f"Error retrieving paper {arxiv_id}: {e}")
            return None
    
    def test_search(self, keyword: str = "RAG") -> List[Paper]:
        """Test search function with a simple keyword"""
        logger.info(f"Testing search with keyword: {keyword}")
        
        papers = self.search_papers(
            keywords=[keyword],
            categories=["cs.AI", "cs.LG", "cs.CL", "cs.IR"],
            max_results=10,
            sort_by="submittedDate"
        )
        
        logger.info(f"Test search returned {len(papers)} papers")
        for i, paper in enumerate(papers[:3], 1):
            logger.info(f"{i}. {paper.title}")
            logger.info(f"   ArXiv ID: {paper.arxiv_id}")
            logger.info(f"   Published: {paper.published.date()}")
        
        return papers

# Backward compatibility - create aliases for existing code
ArxivClient = ArxivAPIClient

# Keep existing enums for compatibility
class SearchOperator:
    AND = "AND"
    OR = "OR" 
    NOT = "NOT"

class DateRange:
    LAST_DAY = 1
    LAST_WEEK = 7
    LAST_MONTH = 30
    LAST_3_MONTHS = 90
    LAST_6_MONTHS = 180
    LAST_YEAR = 365

@dataclass
class SearchFilter:
    """Compatibility class for existing code"""
    categories: Optional[List[str]] = None
    authors: Optional[List[str]] = None
    date_range: Optional[int] = None
    exclude_keywords: Optional[List[str]] = None
    title_only: bool = False
    abstract_only: bool = False