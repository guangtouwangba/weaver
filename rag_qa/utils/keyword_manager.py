#!/usr/bin/env python3
"""
Keyword manager for RAG module
Handles keyword extraction and selection from the papers database
"""

import os
import sys
import logging
from typing import List, Dict, Set
from collections import Counter

# Add backend path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from database.database_adapter import DatabaseManager

logger = logging.getLogger(__name__)

class KeywordManager:
    """Manages keywords from the papers database"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.db_manager = DatabaseManager(config)
    
    def get_available_keywords(self) -> List[Dict[str, any]]:
        """
        Get all available keywords from the database with statistics
        
        Returns:
            List of keyword dictionaries with counts and examples
        """
        try:
            # Get all papers using the unified database adapter
            # Since we need all papers, we'll use a high limit or implement get_all_papers
            # For now, we'll get papers by common keywords to get a representative sample
            common_keywords = ['ai', 'ml', 'rag', 'agent', 'learning', 'neural', 'deep']
            papers = self.db_manager.get_papers_by_keywords(common_keywords)
            
            # If no papers found with common keywords, try getting recent papers
            if not papers:
                papers = self.db_manager.get_recent_papers(365)  # Last year
            
            if not papers:
                logger.warning("No papers with categories found in database")
                return []
                
            # Extract and count keywords
            keyword_counter = Counter()
            keyword_papers = {}  # keyword -> list of paper info
            
            for paper in papers:
                categories = paper.get('categories', '')
                title = paper.get('title', '')
                arxiv_id = paper.get('arxiv_id', '')
                
                # Split categories by common delimiters
                keywords = self._extract_keywords(categories)
                
                for keyword in keywords:
                    keyword_counter[keyword] += 1
                    
                    if keyword not in keyword_papers:
                        keyword_papers[keyword] = []
                    
                    keyword_papers[keyword].append({
                        'title': title,
                        'arxiv_id': arxiv_id
                    })
            
            # Format results
            result = []
            for keyword, count in keyword_counter.most_common():
                result.append({
                    'keyword': keyword,
                    'count': count,
                    'examples': keyword_papers[keyword][:3]  # Show first 3 examples
                })
            
            logger.info(f"Found {len(result)} unique keywords from {len(papers)} papers")
            return result
                
        except Exception as e:
            logger.error(f"Failed to get keywords from database: {e}")
            return []
    
    def _extract_keywords(self, categories: str) -> Set[str]:
        """
        Extract keywords from categories string
        
        Args:
            categories: String containing categories/keywords
            
        Returns:
            Set of cleaned keywords
        """
        keywords = set()
        
        # Common delimiters for categories
        delimiters = [',', ';', '|', ' ', '\t', '\n']
        
        # Split by delimiters
        parts = [categories]
        for delimiter in delimiters:
            new_parts = []
            for part in parts:
                new_parts.extend(part.split(delimiter))
            parts = new_parts
        
        # Clean and filter keywords
        for part in parts:
            keyword = part.strip().lower()
            
            # Filter out empty, very short, or very long keywords
            if 2 <= len(keyword) <= 20:
                # Remove common prefixes
                if keyword.startswith('cs.'):
                    keyword = keyword[3:]
                elif keyword.startswith('stat.'):
                    keyword = keyword[5:]
                elif keyword.startswith('math.'):
                    keyword = keyword[5:]
                
                # Only add if it's a meaningful keyword
                if len(keyword) >= 2 and keyword.isalpha():
                    keywords.add(keyword)
        
        return keywords
    
    def get_papers_by_keywords(self, selected_keywords: List[str]) -> List[Dict[str, any]]:
        """
        Get papers that match the selected keywords
        
        Args:
            selected_keywords: List of keywords to search for
            
        Returns:
            List of paper dictionaries with metadata
        """
        if not selected_keywords:
            return []
        
        try:
            # Use the unified database adapter
            papers = self.db_manager.get_papers_by_keywords(selected_keywords)
            
            logger.info(f"Found {len(papers)} papers matching keywords: {selected_keywords}")
            return papers
                
        except Exception as e:
            logger.error(f"Failed to get papers by keywords: {e}")
            return []
    
    def search_keywords(self, query: str, available_keywords: List[Dict[str, any]]) -> List[Dict[str, any]]:
        """
        Search keywords by query string
        
        Args:
            query: Search query
            available_keywords: List of available keywords
            
        Returns:
            Filtered list of matching keywords
        """
        if not query:
            return available_keywords
        
        query_lower = query.lower()
        matching = []
        
        for kw_info in available_keywords:
            keyword = kw_info['keyword'].lower()
            
            # Check if query matches keyword
            if (query_lower in keyword or 
                keyword.startswith(query_lower) or
                any(query_lower in example['title'].lower() 
                    for example in kw_info['examples'])):
                matching.append(kw_info)
        
        return matching
    
    def get_keyword_statistics(self) -> Dict[str, any]:
        """
        Get overall keyword statistics
        
        Returns:
            Dictionary with keyword statistics
        """
        try:
            # Get total papers count using the unified adapter
            total_papers = self.db_manager.get_paper_count()
            
            # Get a sample of recent papers to estimate coverage
            recent_papers = self.db_manager.get_recent_papers(365)  # Last year
            papers_with_keywords = sum(1 for paper in recent_papers 
                                     if paper.get('categories') and paper.get('categories').strip())
            
            keywords = self.get_available_keywords()
            
            return {
                'total_papers': total_papers,
                'papers_with_keywords': papers_with_keywords,
                'unique_keywords': len(keywords),
                'coverage_percentage': (papers_with_keywords / len(recent_papers) * 100) if recent_papers else 0
            }
                
        except Exception as e:
            logger.error(f"Failed to get keyword statistics: {e}")
            return {
                'total_papers': 0,
                'papers_with_keywords': 0,
                'unique_keywords': 0,
                'coverage_percentage': 0
            }