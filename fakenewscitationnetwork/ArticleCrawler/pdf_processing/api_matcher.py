
from typing import List, Optional
import logging
import time
from difflib import SequenceMatcher
from .models import PDFMetadata, APIMatchResult


class APIMetadataMatcher:
    
    def __init__(self, api_provider, logger: Optional[logging.Logger] = None):
        self.api_provider = api_provider
        self.logger = logger or logging.getLogger(__name__)
        self.request_delay = 0.5
        self.max_retries = 3
    
    def match_metadata(self, metadata_list: List[PDFMetadata]) -> List[APIMatchResult]:
        results = []
        
        for i, metadata in enumerate(metadata_list, 1):
            self.logger.info(f"Matching paper {i}/{len(metadata_list)}: {metadata.filename}")
            
            result = self._match_single(metadata)
            results.append(result)
            
            if i < len(metadata_list):
                time.sleep(self.request_delay)
        
        return results
    
    def _match_single(self, metadata: PDFMetadata) -> APIMatchResult:
        if metadata.doi:
            result = self._match_by_doi(metadata)
            if result.matched:
                return result
        
        if metadata.title:
            result = self._match_by_title(metadata)
            if result.matched:
                return result
        
        return APIMatchResult(metadata=metadata, matched=False)
    
    def _match_by_doi(self, metadata: PDFMetadata) -> APIMatchResult:
        for attempt in range(self.max_retries):
            try:
                doi = metadata.doi.replace('https://doi.org/', '').replace('http://doi.org/', '')
                
                from pyalex import Works
                works = Works().filter(doi=doi).get()
                
                if works and len(works) > 0:
                    work = works[0]
                    paper_id = self._extract_paper_id(work)
                    
                    return APIMatchResult(
                        metadata=metadata,
                        matched=True,
                        paper_id=paper_id,
                        confidence=1.0,
                        match_method="DOI"
                    )
                
                return APIMatchResult(metadata=metadata, matched=False)
                
            except Exception as e:
                error_str = str(e)
                if '429' in error_str or 'too many' in error_str.lower():
                    wait_time = (2 ** attempt) * 2
                    self.logger.warning(f"Rate limited on DOI match (attempt {attempt + 1}/{self.max_retries}), waiting {wait_time}s")
                    if attempt < self.max_retries - 1:
                        time.sleep(wait_time)
                        continue
                
                self.logger.warning(f"DOI match failed for {metadata.filename}: {e}")
                return APIMatchResult(metadata=metadata, matched=False)
        
        return APIMatchResult(metadata=metadata, matched=False)
    
    def _match_by_title(self, metadata: PDFMetadata) -> APIMatchResult:
        for attempt in range(self.max_retries):
            try:
                from pyalex import Works
                
                search_results = Works().search(metadata.title).get()
                
                if not search_results:
                    return APIMatchResult(metadata=metadata, matched=False)
                
                best_match = None
                best_similarity = 0.0
                
                for work in search_results[:5]:
                    title = work.get('title', '').lower()
                    similarity = self._calculate_similarity(metadata.title.lower(), title)
                    
                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_match = work
                
                if best_similarity >= 0.85:
                    paper_id = self._extract_paper_id(best_match)
                    
                    return APIMatchResult(
                        metadata=metadata,
                        matched=True,
                        paper_id=paper_id,
                        confidence=best_similarity,
                        match_method="Title"
                    )
                
                return APIMatchResult(metadata=metadata, matched=False)
                
            except Exception as e:
                error_str = str(e)
                if '429' in error_str or 'too many' in error_str.lower():
                    wait_time = (2 ** attempt) * 2
                    self.logger.warning(f"Rate limited on title match (attempt {attempt + 1}/{self.max_retries}), waiting {wait_time}s")
                    if attempt < self.max_retries - 1:
                        time.sleep(wait_time)
                        continue
                
                self.logger.warning(f"Title match failed for {metadata.filename}: {e}")
                return APIMatchResult(metadata=metadata, matched=False)
        
        return APIMatchResult(metadata=metadata, matched=False)
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        return SequenceMatcher(None, str1, str2).ratio()
    
    def _extract_paper_id(self, work: dict) -> str:
        work_id = work.get('id', '')
        return work_id.split('/')[-1] if '/' in work_id else work_id