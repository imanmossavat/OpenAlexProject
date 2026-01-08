import logging
import os
import time
from typing import Dict, List, Optional, Tuple

import pyalex
import requests
from dotenv import load_dotenv
from pyalex import Authors, Works, Sources

from ..library.models import PaperData, AuthorInfo
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
        self._api_base_url = "https://api.openalex.org"
        self._mailto = email
        self._venue_lookup_cache: Dict[str, Optional[str]] = {}

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

    def _normalize_venue_id(self, venue_id: str) -> str:
        venue_id = venue_id.strip()
        if not venue_id:
            return venue_id
        if venue_id.startswith("https://openalex.org/"):
            return venue_id
        upper = venue_id.upper()
        if upper.startswith("S"):
            return f"https://openalex.org/{upper}"
        resolved = self._resolve_venue_id_by_name(venue_id)
        if resolved:
            return resolved
        clean = venue_id.lstrip("S").lstrip("s")
        if clean:
            return f"https://openalex.org/S{clean}"
        return venue_id

    def _resolve_venue_id_by_name(self, venue_name: str) -> Optional[str]:
        key = venue_name.strip().lower()
        if not key:
            return None
        if key in self._venue_lookup_cache:
            return self._venue_lookup_cache[key]
        try:
            self._rate_limit()
            results = Sources().search(venue_name).get()
            if results:
                first = results[0]
                venue_id = first.get("id")
                if venue_id:
                    self._venue_lookup_cache[key] = venue_id
                    return venue_id
        except Exception as exc:
            self.logger.warning("Unable to resolve venue id for %s: %s", venue_name, exc)
        self._venue_lookup_cache[key] = None
        return None

    def _fetch_paginated_works(
        self,
        filter_query: str,
        page: int,
        page_size: int,
    ) -> Tuple[List[Dict], Optional[int]]:
        normalized_page = max(1, int(page or 1))
        normalized_page_size = max(1, min(int(page_size or 25), 200))
        params = {
            "filter": filter_query,
            "page": normalized_page,
            "per-page": normalized_page_size,
        }
        if self._mailto:
            params["mailto"] = self._mailto

        for attempt in range(self.retries + 1):
            try:
                self._rate_limit()
                response = requests.get(
                    f"{self._api_base_url}/works",
                    params=params,
                    timeout=60,
                )
                response.raise_for_status()
                payload = response.json()
                results = payload.get("results", [])
                total = payload.get("meta", {}).get("count")
                return results, total
            except Exception as exc:
                if attempt == self.retries:
                    self.logger.error(
                        "Failed to retrieve paginated works filter=%s page=%s: %s",
                        filter_query,
                        normalized_page,
                        exc,
                    )
                    return [], None
                wait_time = 2 ** attempt
                self.logger.warning(
                    "Error retrieving paginated works (attempt %s/%s): %s",
                    attempt + 1,
                    self.retries + 1,
                    exc,
                )
                time.sleep(wait_time)
        return [], None

    def _get_paginated_entity_papers(
        self,
        filter_query: str,
        *,
        page: int,
        page_size: int,
    ) -> Tuple[List, List[str], Optional[int]]:
        works, total = self._fetch_paginated_works(filter_query, page, page_size)
        papers: List = []
        paper_ids: List[str] = []
        for work in works:
            try:
                paper_dict = self._convert_openalex_to_s2_format(work)
                papers.append(self._dict_to_object(paper_dict))
                pid = self._clean_id(work.get("id", ""))
                if pid:
                    paper_ids.append(pid)
            except Exception as exc:
                self.logger.warning("Failed to convert work to paper: %s", exc)
        return papers, paper_ids, total

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

    def get_paper_metadata_only(self, paper_id: str) -> Optional[Dict]:
        """
        Get a single paper with FULL OpenAlex metadata but WITHOUT references/citations.
        This is for LIBRARY CREATION use cases.
        
        Returns the raw OpenAlex dictionary with all fields including concepts, topics, etc.
        Does NOT fetch references or citations (much faster).
        """
        for attempt in range(self.retries + 1):
            try:
                self._rate_limit()
                normalized_id = self._normalize_paper_id(paper_id)
                
                work = Works()[normalized_id]
                
                if not work:
                    return None
                
                returned_id = self._clean_id(work['id'])
                requested_id = self._clean_id(paper_id).lstrip('W')
                
                if returned_id != f"W{requested_id}" and returned_id.lstrip('W') != requested_id:
                    self._inconsistent_api_response_paper_ids.append((paper_id, returned_id))
                    self.logger.warning(f"ID mismatch: requested {paper_id}, got {returned_id}")
                
                return work
                
            except Exception as e:
                if attempt == self.retries:
                    self._failed_paper_ids.append(paper_id)
                    self.logger.error(f"Failed to get paper {paper_id}: {e}")
                    return None
                time.sleep(2 ** attempt)
        
        return None

    def get_papers_batch(self, paper_ids: List[str]) -> List[Dict]:
        """
        Get multiple papers in batches with FULL OpenAlex metadata.
        For LIBRARY CREATION - returns raw OpenAlex dictionaries.
        Does NOT fetch references or citations.
        
        Args:
            paper_ids: List of paper IDs to fetch
            
        Returns:
            List of OpenAlex work dictionaries
        """
        if not paper_ids:
            return []
        
        all_works = []
        batch_size = 25
        
        for i in range(0, len(paper_ids), batch_size):
            batch_ids = paper_ids[i:i + batch_size]
            
            clean_ids = []
            for pid in batch_ids:
                clean_id = self._clean_id(pid)
                if not clean_id.startswith('W'):
                    clean_id = f"W{clean_id}"
                clean_ids.append(clean_id)
            
            for attempt in range(self.retries + 1):
                try:
                    self._rate_limit()
                    
                    batch_works = Works().filter(openalex_id='|'.join(clean_ids)).get()
                    
                    all_works.extend(batch_works)
                    
                    self.logger.info(f"Fetched batch {i//batch_size + 1}: {len(batch_works)}/{len(clean_ids)} papers")
                    
                    break
                    
                except Exception as e:
                    if attempt == self.retries:
                        self.logger.error(f"Failed to fetch batch {i//batch_size + 1} after {self.retries + 1} attempts: {e}")
                        break
                    time.sleep(2 ** attempt)
            
            if i + batch_size < len(paper_ids):
                time.sleep(0.5)
        
        self.logger.info(f"Total fetched: {len(all_works)}/{len(paper_ids)} papers")
        return all_works
    
    def get_papers_batch_as_paper_data(self, paper_ids: List[str]) -> Dict[str, 'PaperData']:
        """Fetch a batch of papers and return PaperData objects keyed by normalized ID."""
        works = self.get_papers_batch(paper_ids)
        paper_data_map: Dict[str, 'PaperData'] = {}
        for work in works:
            try:
                paper_data = self._convert_work_to_paper_data(work)
                if not paper_data:
                    continue
                normalized = self._clean_id(paper_data.paper_id)
                if normalized:
                    paper_data_map[normalized] = paper_data
            except Exception as exc:
                self.logger.warning("Failed to convert work %s to PaperData: %s", work.get('id'), exc)
        return paper_data_map
    


    def get_paper_as_paper_data(self, paper_id: str) -> Optional['PaperData']:
        """
        Get a single paper as PaperData object with full OpenAlex metadata.
        This is the main method for library creation - returns ready-to-use PaperData.
        
        Args:
            paper_id: Paper identifier (can be W12345, 12345, or full URL)
            
        Returns:
            PaperData object or None if fetch fails
        """
        work = self.get_paper_metadata_only(paper_id)
        
        if not work:
            return None
        
        return self._convert_work_to_paper_data(work)


    def _convert_work_to_paper_data(self, work: Dict) -> 'PaperData':
        """
        Convert OpenAlex work dictionary to PaperData object.
        
        Args:
            work: OpenAlex work dictionary
            
        Returns:
            PaperData object
        """
        from ..library.models import PaperData
        
        paper_id = self._clean_id(work['id'])
        title = work.get('title', '') or work.get('display_name', '')
        year = work.get('publication_year')
        
        doi = work.get('doi', '')
        if doi and doi.startswith('https://doi.org/'):
            doi = doi.replace('https://doi.org/', '')
        
        venue = None
        if work.get('primary_location') and work['primary_location'].get('source'):
            venue = work['primary_location']['source'].get('display_name')
        
        abstract = work.get('abstract')
        if not abstract and work.get('abstract_inverted_index'):
            abstract = self._reconstruct_abstract(work['abstract_inverted_index'])
        
        authors = []
        for authorship in work.get('authorships', []):
            author = authorship.get('author', {})
            author_id = author.get('id', '')
            if author_id.startswith('https://openalex.org/'):
                author_id = author_id.split('/')[-1]
            author_name = author.get('display_name', '')
            if author_name:
                authors.append({
                    'authorId': author_id,
                    'name': author_name
                })
        
        concepts = []
        for concept in work.get('concepts', []):
            concepts.append({
                'id': concept.get('id', ''),
                'display_name': concept.get('display_name', ''),
                'level': concept.get('level', 0),
                'score': concept.get('score', 0.0)
            })
        
        topics_data = self._extract_hierarchy_from_concepts(concepts)
        
        url = f"https://openalex.org/{paper_id}"
        
        return PaperData(
            paper_id=paper_id,
            title=title,
            authors=authors,
            year=year,
            venue=venue,
            venue_raw=venue,
            doi=doi,
            abstract=abstract,
            url=url,
            concepts=concepts,
            topics=topics_data['topics'],
            subfields=topics_data['subfields'],
            fields=topics_data['fields'],
            domains=topics_data['domains']
        )


    def _extract_hierarchy_from_concepts(self, concepts: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Extract hierarchical concept data from concepts list.
        
        Based on concept levels:
        - level 0: Domain
        - level 1: Field
        - level 2: Subfield
        - level 3+: Topic
        
        Args:
            concepts: List of concept dictionaries
            
        Returns:
            Dictionary with 'topics', 'subfields', 'fields', 'domains' keys
        """
        topics = []
        subfields = []
        fields = []
        domains = []
        
        for concept in concepts:
            level = concept.get('level', 0)
            display_name = concept.get('display_name', '')
            concept_id = concept.get('id', '')
            score = concept.get('score', 0.0)
            
            if not display_name:
                continue
            
            item = {
                'id': concept_id,
                'display_name': display_name,
                'score': score
            }
            
            if level == 0:
                domains.append(item)
            elif level == 1:
                fields.append(item)
            elif level == 2:
                subfields.append(item)
            elif level >= 3:
                topics.append(item)
        
        return {
            'topics': topics,
            'subfields': subfields,
            'fields': fields,
            'domains': domains
        }


    def _reconstruct_abstract(self, inverted_index: Dict[str, List[int]]) -> str:
        """
        Reconstruct abstract text from OpenAlex inverted index.
        
        Args:
            inverted_index: Dictionary mapping words to position lists
            
        Returns:
            Reconstructed abstract text
        """
        if not inverted_index:
            return ""
        
        max_pos = max(max(positions) for positions in inverted_index.values())
        
        words = [''] * (max_pos + 1)
        
        for word, positions in inverted_index.items():
            for pos in positions:
                words[pos] = word
        
        return ' '.join(words)

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

    def get_author_papers(
        self,
        author_id: str,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List, List[str], Optional[int]]:
        normalized_id = self._normalize_author_id(author_id)
        filter_query = f"authorships.author.id:{normalized_id}"
        return self._get_paginated_entity_papers(filter_query, page=page, page_size=page_size)

    def get_venue_papers(
        self,
        venue_id: str,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List, List[str], Optional[int]]:
        normalized_id = self._normalize_venue_id(venue_id)
        filter_query = f"primary_location.source.id:{normalized_id}"
        return self._get_paginated_entity_papers(filter_query, page=page, page_size=page_size)

    def _convert_openalex_to_s2_format(self, openalex_work: Dict) -> Dict:
        paper_id = self._clean_id(openalex_work['id'])
        
        abstract = openalex_work.get('abstract')
        if not abstract and openalex_work.get('abstract_inverted_index'):
            abstract = self._reconstruct_abstract_from_inverted_index(
                openalex_work['abstract_inverted_index']
            )
        
        venue = self._extract_venue_with_fallbacks(openalex_work)
        authors = self._convert_authorships_to_s2_authors(openalex_work.get('authorships', []))
        concepts = []
        for concept in openalex_work.get('concepts', []):
            concepts.append({
                'id': concept.get('id', ''),
                'display_name': concept.get('display_name', ''),
                'level': concept.get('level', 0),
                'score': concept.get('score', 0.0)
            })
        hierarchy = self._extract_hierarchy_from_concepts(concepts)
        
        return {
            'paperId': paper_id,
            'title': openalex_work.get('title', ''),
            'abstract': abstract,
            'venue': venue,
            'year': openalex_work.get('publication_year'),
            'doi': self._clean_doi(openalex_work.get('doi', '')),
            'url': f"https://openalex.org/{paper_id}",
            'concepts': concepts,
            'topics': hierarchy.get('topics', []),
            'subfields': hierarchy.get('subfields', []),
            'fields': hierarchy.get('fields', []),
            'domains': hierarchy.get('domains', []),
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
    
    def search_authors(self, author_name: str, limit: int = 10) -> List[AuthorInfo]:
        """
        Search for authors by name using OpenAlex API.
        
        Args:
            author_name: Name to search for
            limit: Maximum number of results
            
        Returns:
            List of AuthorInfo objects
        """
        try:
            self._rate_limit()
            
            authors = Authors().search(author_name).get()
            
            if not authors:
                self.logger.info(f"No authors found for query: {author_name}")
                return []
            
            authors = authors[:limit]
            
            author_infos = []
            for author in authors:
                institutions = []
                if author.get('affiliations'):
                    for aff in author['affiliations'][:3]:
                        if aff.get('institution') and aff['institution'].get('display_name'):
                            institutions.append(aff['institution']['display_name'])
                
                author_info = AuthorInfo(
                    id=self._clean_id(author['id']),
                    name=author.get('display_name', ''),
                    works_count=author.get('works_count', 0),
                    cited_by_count=author.get('cited_by_count', 0),
                    institutions=institutions,
                    orcid=author.get('orcid')
                )
                author_infos.append(author_info)
            
            self.logger.info(f"Found {len(author_infos)} authors for query: {author_name}")
            return author_infos
            
        except Exception as e:
            self.logger.error(f"Error searching for authors '{author_name}': {e}")
            return []


    def get_author_papers_as_paper_data(
    self, 
    author_id: str,
    max_papers: Optional[int] = None
) -> List[PaperData]:
        """
        Get all papers by an author as full PaperData objects with complete metadata.
        
        This is the ENHANCED version that returns full PaperData objects with
        concepts, fields, subfields, and domains.
        
        Args:
            author_id: Author identifier (can be A12345 or full URL)
            max_papers: Optional limit on number of papers to retrieve
            
        Returns:
            List of PaperData objects with full OpenAlex metadata
        """
        try:
            from itertools import chain
            
            self._rate_limit()
            normalized_id = self._normalize_author_id(author_id)
            
            # Build the query
            query = Works().filter(**{"authorships.author.id": normalized_id})
            
            # Set up pagination parameters
            per_page = 200  # Max allowed by OpenAlex
            
            # Calculate n_max for paginate (max number of results to retrieve)
            n_max = max_papers if max_papers else None
            
            # Use paginate to get all results (or up to max_papers)
            pager = query.paginate(per_page=per_page, n_max=n_max)
            
            # Convert paginator to list of all works using chain
            # This iterates through all pages and flattens into a single list
            all_works = list(chain(*pager))
            
            if not all_works:
                self.logger.info(f"No papers found for author {author_id}")
                return []
            
            self.logger.info(f"Fetched {len(all_works)} works for author {author_id}")
            
            # Convert each work to PaperData with full metadata
            papers = []
            for i, work in enumerate(all_works, 1):
                try:
                    paper_data = self._convert_work_to_paper_data(work)
                    papers.append(paper_data)
                    
                    if i % 50 == 0:
                        self.logger.debug(f"Converted {i}/{len(all_works)} papers to PaperData")
                        
                except Exception as e:
                    self.logger.warning(f"Failed to convert work {work.get('id')}: {e}")
                    continue
            
            self.logger.info(f"Retrieved {len(papers)} papers with full metadata for author {author_id}")
            return papers
            
        except Exception as e:
            self.logger.error(f"Error retrieving papers for author {author_id}: {e}")
            return []
