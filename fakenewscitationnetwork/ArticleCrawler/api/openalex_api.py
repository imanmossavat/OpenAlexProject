import pyalex
from pyalex import Works, Authors
import time
import os
from dotenv import load_dotenv
import logging
from typing import List, Dict, Optional, Tuple
from .base_api import BaseAPIProvider

class OpenAlexAPIProvider(BaseAPIProvider):
    
    def __init__(self, wait=None, retries=3, logger=None):
        load_dotenv()
        email = os.getenv('OPENALEX_EMAIL')
        if not email:
            raise ValueError("OPENALEX_EMAIL must be set in .env file")
        
        pyalex.config.email = email
        
        self.requests_per_second = 2
        self.min_delay = 1.0 / self.requests_per_second
        self.last_request_time = 0
        
        self.retries = retries
        self._failed_paper_ids = []
        self._inconsistent_api_response_paper_ids = []
        self.logger = logger or logging.getLogger(__name__)
        
        self.logger.info("OpenAlex API initialized with rate limiting at 2 req/sec")

    @property
    def failed_paper_ids(self) -> List[str]:
        return self._failed_paper_ids

    @property
    def inconsistent_api_response_paper_ids(self) -> List[tuple]:
        return self._inconsistent_api_response_paper_ids

    def _rate_limit(self):
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_delay:
            time.sleep(self.min_delay - elapsed)
        self.last_request_time = time.time()

    def _normalize_paper_id(self, paper_id: str) -> str:
        paper_id = paper_id.strip()
        
        if paper_id.startswith('https://openalex.org/'):
            return paper_id
        elif paper_id.startswith('W'):
            return f"https://openalex.org/{paper_id}"
        else:
            clean_id = paper_id.lstrip('W').lstrip('w')
            return f"https://openalex.org/W{clean_id}"

    def _normalize_author_id(self, author_id: str) -> str:
        if author_id.startswith('https://openalex.org/'):
            return author_id
        elif author_id.startswith('A'):
            return f"https://openalex.org/{author_id}"
        else:
            return f"https://openalex.org/A{author_id}"

    def _clean_id(self, full_id: str) -> str:
        return full_id.split('/')[-1] if '/' in full_id else full_id

    def get_paper(self, paper_id: str):
        for attempt in range(self.retries + 1):
            try:
                self._rate_limit()
                normalized_id = self._normalize_paper_id(paper_id)
                
                paper = Works()[normalized_id]
                
                returned_id = self._clean_id(paper['id'])
                requested_id = self._clean_id(paper_id).lstrip('W')
                
                if returned_id != f"W{requested_id}" and returned_id.lstrip('W') != requested_id:
                    self._inconsistent_api_response_paper_ids.append((paper_id, returned_id))
                    self.logger.warning(f"ID mismatch: requested {paper_id}, got {returned_id}")
                
                s2_paper = self._convert_to_s2_format_with_enrichment(paper)
                
                time.sleep(0.5)
                
                return s2_paper
                
            except Exception as e:
                if attempt == self.retries:
                    self._failed_paper_ids.append(paper_id)
                    self.logger.error(f"Failed to get paper {paper_id}: {e}")
                    return None
                time.sleep(2 ** attempt)

    def get_papers(self, paper_id_list: List[str]):
        results = []
        for paper_id in paper_id_list:
            paper = self.get_paper(paper_id)
            results.append(paper)
        return results

    def _convert_to_s2_format_with_enrichment(self, openalex_work: Dict):
        paper_id = self._clean_id(openalex_work['id'])
        
        s2_paper = self._convert_openalex_to_s2_format(openalex_work)
        
        if openalex_work.get('referenced_works'):
            self.logger.info(f"Enriching {len(openalex_work['referenced_works'])} references for paper {paper_id}")
            enriched_refs = self._get_references_with_metadata(openalex_work['referenced_works'])
            s2_paper['references'] = enriched_refs
        
        self.logger.info(f"Fetching citations for paper {paper_id}")
        citations = self._get_citations_for_paper(paper_id)
        s2_paper['citations'] = citations
        
        return self._dict_to_object(s2_paper)

    def _get_references_with_metadata(self, reference_ids: List[str]) -> List[Dict]:
        if not reference_ids:
            return []
        
        enriched_refs = []
        batch_size = 25
        
        for i in range(0, len(reference_ids), batch_size):
            batch_ids = reference_ids[i:i + batch_size]
            clean_ids = [self._clean_id(ref_id) for ref_id in batch_ids]
            
            for retry in range(3):
                try:
                    self._rate_limit()
                    
                    batch_works = Works().filter(openalex_id='|'.join(clean_ids)).get()
                    
                    for work in batch_works:
                        ref_paper = self._convert_openalex_to_s2_format(work)
                        enriched_refs.append(ref_paper)
                    
                    self.logger.info(f"Enriched batch {i//batch_size + 1}: {len(batch_works)} references")
                    
                    break
                    
                except Exception as e:
                    if "429" in str(e) and retry < 2:
                        wait_time = (2 ** retry) * 2
                        self.logger.warning(f"Rate limited on batch {i//batch_size + 1}, waiting {wait_time}s (retry {retry + 1}/3)")
                        time.sleep(wait_time)
                    else:
                        self.logger.error(f"Error enriching reference batch after {retry + 1} attempts: {e}")
                        break
            
            if i + batch_size < len(reference_ids):
                time.sleep(0.5)
        
        return enriched_refs

    def _get_citations_for_paper(self, paper_id: str) -> List[Dict]:
        for retry in range(3):
            try:
                self._rate_limit()
                clean_id = self._clean_id(paper_id)
                
                citing_works = []
                pager = Works().filter(cites=clean_id).paginate(per_page=200)
                
                for page_num, page in enumerate(pager):
                    citing_works.extend(page)
                    
                    if len(citing_works) % 1000 == 0:
                        self.logger.info(f"Fetched {len(citing_works)} citing papers so far...")
                    
                    self._rate_limit()
                
                citations = [self._convert_openalex_to_s2_format(work) for work in citing_works]
                self.logger.info(f"Retrieved {len(citations)} citations for paper {paper_id}")
                return citations
                
            except Exception as e:
                if "429" in str(e) and retry < 2:
                    wait_time = (2 ** retry) * 2
                    self.logger.warning(f"Rate limited fetching citations for {paper_id}, waiting {wait_time}s (retry {retry + 1}/3)")
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"Error getting citations for {paper_id}: {e}")
                    return []
        
        return []

    def get_author_papers(self, author_id: str) -> Tuple[List, List[str]]:
        try:
            self._rate_limit()
            normalized_id = self._normalize_author_id(author_id)
            
            works = Works().filter(**{"authorships.author.id": normalized_id}).get()
            papers = [self._dict_to_object(self._convert_openalex_to_s2_format(work)) for work in works]
            paper_ids = [self._clean_id(work['id']) for work in works]
            
            self.logger.info(f"Retrieved {len(papers)} papers for author {author_id}")
            return papers, paper_ids
            
        except Exception as e:
            self.logger.error(f"Error retrieving papers for author {author_id}: {e}")
            return [], []

    def _convert_openalex_to_s2_format(self, openalex_work: Dict) -> Dict:
        paper_id = self._clean_id(openalex_work['id'])
        
        abstract = openalex_work.get('abstract')
        if not abstract and openalex_work.get('abstract_inverted_index'):
            abstract = self._reconstruct_abstract_from_inverted_index(
                openalex_work['abstract_inverted_index']
            )
        
        venue = self._extract_venue_with_fallbacks(openalex_work)
        authors = self._convert_authorships_to_s2_authors(openalex_work.get('authorships', []))
        
        return {
            'paperId': paper_id,
            'title': openalex_work.get('title', ''),
            'abstract': abstract,
            'venue': venue,
            'year': openalex_work.get('publication_year'),
            'doi': self._clean_doi(openalex_work.get('doi', '')),
            'authors': authors,
            'references': [],
            'citations': []
        }

    def _reconstruct_abstract_from_inverted_index(self, inverted_index):
        if not inverted_index or not isinstance(inverted_index, dict):
            return None
        
        try:
            word_positions = []
            for word, positions in inverted_index.items():
                for pos in positions:
                    word_positions.append((pos, word))
            
            word_positions.sort(key=lambda x: x[0])
            abstract = ' '.join([word for pos, word in word_positions])
            
            return abstract.strip() if abstract.strip() else None
            
        except Exception as e:
            self.logger.warning(f"Error reconstructing abstract: {e}")
            return None

    def _extract_venue_with_fallbacks(self, work: Dict) -> str:
        if (work.get('primary_location') and 
            work['primary_location'].get('source') and 
            work['primary_location']['source'].get('display_name')):
            return work['primary_location']['source']['display_name']
        
        for location in work.get('locations', []):
            if (location.get('source') and 
                location['source'].get('display_name')):
                return location['source']['display_name']
        
        if (work.get('best_oa_location') and 
            work['best_oa_location'].get('source') and 
            work['best_oa_location']['source'].get('display_name')):
            return work['best_oa_location']['source']['display_name']
        
        return ''

    def _convert_authorships_to_s2_authors(self, authorships: List[Dict]) -> List[Dict]:
        authors = []
        for authorship in authorships:
            author = authorship.get('author', {})
            authors.append({
                'authorId': self._clean_id(author.get('id', '')),
                'name': author.get('display_name', '')
            })
        return authors

    def _clean_doi(self, doi: str) -> str:
        if not doi:
            return ''
        return doi.replace('https://doi.org/', '') if doi.startswith('https://doi.org/') else doi

    def _dict_to_object(self, data: Dict):
        class PaperObject:
            def __init__(self, data_dict):
                for key, value in data_dict.items():
                    if isinstance(value, list) and value and isinstance(value[0], dict):
                        setattr(self, key, [PaperObject(item) if isinstance(item, dict) else item for item in value])
                    elif isinstance(value, dict):
                        setattr(self, key, PaperObject(value))
                    else:
                        setattr(self, key, value)
        
        return PaperObject(data)

    def get_failed_and_inconsistent_papers(self) -> Dict:
        return {
            'failed': self._failed_paper_ids,
            'inconsistent': self._inconsistent_api_response_paper_ids
        }