"""
Core matching logic using Strategy pattern.
Single Responsibility: Coordinate matching process.
"""

import logging
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from ...base_api import BaseAPIProvider
from .strategies import TitleMatchStrategy, OpenAlexTitleMatchStrategy, SemanticScholarTitleMatchStrategy, TitleSimilarityCalculator
import time


@dataclass
class MatchCandidate:
    """A candidate match for manual review."""
    paper_id: str
    title: str
    similarity: float
    year: Optional[int] = None
    venue: Optional[str] = None
    doi: Optional[str] = None


@dataclass
class MatchResult:
    """Result of matching a Zotero item to an API paper."""
    zotero_key: str
    title: str
    matched: bool
    paper_id: Optional[str] = None
    confidence: float = 0.0
    match_method: Optional[str] = None
    error: Optional[str] = None
    candidates: List[MatchCandidate] = field(default_factory=list)


class ZoteroMatcher:
    """
    Matches Zotero metadata to paper IDs.
    Single Responsibility: Coordinate the matching process using strategies.
    """
    
    MIN_AUTO_MATCH_SIMILARITY = 0.85
    MIN_CANDIDATE_SIMILARITY = 0.60
    
    def __init__(
        self, 
        api_provider: BaseAPIProvider,
        title_strategy: Optional[TitleMatchStrategy] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize matcher with API provider and optional strategy.
        
        Args:
            api_provider: API provider for DOI lookups
            title_strategy: Optional custom title matching strategy
            logger: Optional logger instance
        """
        self.api = api_provider
        self.logger = logger or logging.getLogger(__name__)
        
        if title_strategy is None:
            api_type = self._detect_api_type()
            if api_type == 'openalex':
                self.title_strategy = OpenAlexTitleMatchStrategy()
            elif api_type == 'semantic_scholar':
                self.title_strategy = SemanticScholarTitleMatchStrategy()
            else:
                raise ValueError(f"No title strategy available for API type: {api_type}")
        else:
            self.title_strategy = title_strategy
        
        self.similarity_calculator = TitleSimilarityCalculator()
        
        self.last_request_time = 0
        self.min_delay = 0.6
    
    def _detect_api_type(self) -> str:
        """Detect which API provider is being used."""
        class_name = self.api.__class__.__name__
        if 'OpenAlex' in class_name:
            return 'openalex'
        elif 'SemanticScholar' in class_name or 'S2' in class_name:
            return 'semantic_scholar'
        else:
            return 'unknown'
    
    def _rate_limit(self):
        """Enforce rate limiting."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_delay:
            time.sleep(self.min_delay - elapsed)
        self.last_request_time = time.time()
    
    def match_items(self, items_metadata: List[Dict]) -> List[MatchResult]:
        """
        Match multiple Zotero items to paper IDs.
        
        Args:
            items_metadata: List of metadata dictionaries
            
        Returns:
            List of MatchResult objects
        """
        results = []
        
        for i, metadata in enumerate(items_metadata, 1):
            self.logger.info(f"Matching paper {i}/{len(items_metadata)}: {metadata['title'][:60]}...")
            result = self.match_single_item(metadata)
            results.append(result)
        
        matched_count = sum(1 for r in results if r.matched)
        self.logger.info(f"Matched {matched_count}/{len(results)} Zotero items")
        
        return results
    
    def match_single_item(self, metadata: Dict) -> MatchResult:
        """
        Match a single Zotero item to a paper ID.
        
        Args:
            metadata: Metadata dictionary
            
        Returns:
            MatchResult object
        """
        zotero_key = metadata['zotero_key']
        title = metadata['title']
        
        if metadata.get('doi'):
            result = self._match_by_doi(metadata)
            if result.matched:
                return result
            self.logger.debug("DOI lookup failed, trying title search")
        
        return self._match_by_title(metadata)
    
    def _match_by_doi(self, metadata: Dict) -> MatchResult:
        """Match by DOI lookup."""
        doi = metadata['doi']
        zotero_key = metadata['zotero_key']
        title = metadata['title']
        
        self._rate_limit()
        
        try:
            api_type = self._detect_api_type()
            
            if api_type == 'openalex':
                from pyalex import Works
                results = Works().filter(doi=doi).get()
                
                if results and len(results) > 0:
                    paper = results[0]
                    paper_id = paper.get('id', '').replace('https://openalex.org/', '')
                    
                    if paper_id:
                        self.logger.info(f"DOI match: {doi} -> {paper_id}")
                        return MatchResult(
                            zotero_key=zotero_key,
                            title=title,
                            matched=True,
                            paper_id=paper_id,
                            confidence=1.0,
                            match_method='doi'
                        )
            
            elif api_type == 'semantic_scholar':
                import requests
                url = f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}"
                params = {'fields': 'paperId,title'}
                
                response = requests.get(url, params=params, timeout=10)
                
                if response.status_code == 200:
                    paper = response.json()
                    paper_id = paper.get('paperId')
                    
                    if paper_id:
                        self.logger.info(f"DOI match: {doi} -> {paper_id}")
                        return MatchResult(
                            zotero_key=zotero_key,
                            title=title,
                            matched=True,
                            paper_id=paper_id,
                            confidence=1.0,
                            match_method='doi'
                        )
        
        except Exception as e:
            self.logger.debug(f"DOI lookup failed for {doi}: {e}")
        
        return MatchResult(
            zotero_key=zotero_key,
            title=title,
            matched=False,
            error=f"DOI not found: {doi}"
        )
    
    def _match_by_title(self, metadata: Dict) -> MatchResult:
        """Match by title search using the configured strategy."""
        title = metadata['title']
        zotero_key = metadata['zotero_key']
        
        try:
            search_results = self.title_strategy.search(title, max_results=10)
            
            if not search_results:
                return MatchResult(
                    zotero_key=zotero_key,
                    title=title,
                    matched=False,
                    error="No results found"
                )
            
            candidates = []
            best_similarity = 0.0
            auto_match = None
            
            for result in search_results:
                similarity = self.similarity_calculator.calculate(title, result['title'])
                
                if similarity >= self.MIN_CANDIDATE_SIMILARITY:
                    candidate = MatchCandidate(
                        paper_id=result['paper_id'],
                        title=result['title'],
                        similarity=similarity,
                        year=result.get('year'),
                        venue=result.get('venue'),
                        doi=result.get('doi')
                    )
                    candidates.append(candidate)
                    
                    if similarity >= self.MIN_AUTO_MATCH_SIMILARITY and auto_match is None:
                        auto_match = candidate
                    
                    best_similarity = max(best_similarity, similarity)
            
            if auto_match:
                self.logger.info(
                    f"Title match: '{title[:60]}...' -> {auto_match.paper_id} "
                    f"(similarity: {auto_match.similarity:.2f})"
                )
                return MatchResult(
                    zotero_key=zotero_key,
                    title=title,
                    matched=True,
                    paper_id=auto_match.paper_id,
                    confidence=auto_match.similarity,
                    match_method='title_search'
                )
            
            return MatchResult(
                zotero_key=zotero_key,
                title=title,
                matched=False,
                confidence=best_similarity,
                error=f"No auto-match found (best: {best_similarity:.2f})",
                candidates=candidates
            )
        
        except Exception as e:
            self.logger.warning(f"Title search failed: {e}")
            return MatchResult(
                zotero_key=zotero_key,
                title=title,
                matched=False,
                error=f"Search error: {str(e)}"
            )