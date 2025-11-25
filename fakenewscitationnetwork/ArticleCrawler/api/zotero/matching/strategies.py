"""
Title matching strategies.
Strategy Pattern for different matching approaches.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import time
from difflib import SequenceMatcher
import re

from ArticleCrawler.normalization import normalize_venue

class TitleMatchStrategy(ABC):
    """Abstract base for title matching strategies."""
    
    @abstractmethod
    def search(self, title: str, max_results: int = 10) -> List[Dict]:
        """
        Search for papers by title.
        
        Returns:
            List of result dictionaries with 'paper_id', 'title', 'year', 'venue', 'doi'
        """
        pass


class OpenAlexTitleMatchStrategy(TitleMatchStrategy):
    """OpenAlex-specific title matching."""
    
    def __init__(self):
        self.last_request_time = 0
        self.min_delay = 0.6
    
    def _rate_limit(self):
        """Enforce rate limiting."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_delay:
            time.sleep(self.min_delay - elapsed)
        self.last_request_time = time.time()
    
    def search(self, title: str, max_results: int = 10) -> List[Dict]:
        """Search OpenAlex for papers by title."""
        self._rate_limit()
        
        from pyalex import Works
        
        search_results = Works().search(title).get()
        
        if not search_results:
            return []
        
        results = []
        for result in search_results[:max_results]:
            api_title = result.get('title', '')
            if not api_title:
                continue
            
            paper_id = result.get('id', '').replace('https://openalex.org/', '')
            venue_raw = self._extract_venue(result)
            venue = normalize_venue(venue_raw) or venue_raw
            doi = result.get('doi', '').replace('https://doi.org/', '') if result.get('doi') else None
            
            results.append({
                'paper_id': paper_id,
                'title': api_title,
                'year': result.get('publication_year'),
                'venue': venue,
                'doi': doi
            })
        
        return results
    
    def _extract_venue(self, result: Dict) -> Optional[str]:
        """Extract venue from OpenAlex result."""
        if result.get('primary_location'):
            source = result['primary_location'].get('source')
            if source and source.get('display_name'):
                return source['display_name']
        
        if result.get('host_venue'):
            return result['host_venue'].get('display_name')
        
        return None


class SemanticScholarTitleMatchStrategy(TitleMatchStrategy):
    """Semantic Scholar-specific title matching."""
    
    def __init__(self):
        self.last_request_time = 0
        self.min_delay = 0.6
    
    def _rate_limit(self):
        """Enforce rate limiting."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_delay:
            time.sleep(self.min_delay - elapsed)
        self.last_request_time = time.time()
    
    def search(self, title: str, max_results: int = 10) -> List[Dict]:
        """Search Semantic Scholar for papers by title."""
        import requests
        
        self._rate_limit()
        
        url = "https://api.semanticscholar.org/graph/v1/paper/search"
        params = {
            'query': title,
            'limit': max_results,
            'fields': 'paperId,title,year,venue'
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        papers = data.get('data', [])
        
        results = []
        for paper in papers:
            api_title = paper.get('title', '')
            if not api_title:
                continue
            
            venue_field = paper.get('venue', {}).get('name') if isinstance(paper.get('venue'), dict) else paper.get('venue')
            venue = normalize_venue(venue_field) or venue_field
            
            results.append({
                'paper_id': paper.get('paperId'),
                'title': api_title,
                'year': paper.get('year'),
                'venue': venue,
                'doi': None
            })
        
        return results


class TitleSimilarityCalculator:
    """Calculates similarity between titles."""
    
    @staticmethod
    def calculate(title1: str, title2: str) -> float:
        """
        Calculate similarity between two titles.
        
        Returns:
            Similarity score between 0 and 1
        """
        if not title1 or not title2:
            return 0.0
        
        norm1 = TitleSimilarityCalculator._normalize(title1)
        norm2 = TitleSimilarityCalculator._normalize(title2)
        
        return SequenceMatcher(None, norm1, norm2).ratio()
    
    @staticmethod
    def _normalize(title: str) -> str:
        """Normalize title for comparison."""
        normalized = title.lower()
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        normalized = re.sub(r'\s+', ' ', normalized)
        return normalized.strip()
