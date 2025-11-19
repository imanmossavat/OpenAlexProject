import logging
from typing import List, Optional

from ArticleCrawler.api.api_factory import create_api_provider
from ArticleCrawler.api.base_api import BaseAPIProvider

from app.schemas.seeds import (
    MatchedSeed,
    UnmatchedSeed,
    SeedMatchResult
)


class SeedSelectionService:

    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def match_paper_ids(
        self, 
        paper_ids: List[str],
        api_provider: str = "openalex"
    ) -> SeedMatchResult:

        self.logger.info(f"Matching {len(paper_ids)} paper IDs with {api_provider}")
        
        api = self._get_api_client(api_provider)
        
        matched_seeds = []
        unmatched_seeds = []
        
        for paper_id in paper_ids:
            try:
                paper_data = self._fetch_paper_metadata(api, paper_id, api_provider)
                
                if paper_data:
                    matched_seed = self._create_matched_seed(paper_data, paper_id, api_provider)
                    matched_seeds.append(matched_seed)
                    self.logger.debug(f"Matched: {paper_id} -> {matched_seed.paper_id}")
                else:
                    unmatched_seeds.append(UnmatchedSeed(
                        input_id=paper_id,
                        error="Paper not found in API"
                    ))
                    self.logger.warning(f"Not found: {paper_id}")
            
            except Exception as e:
                self.logger.error(f"Error processing paper ID {paper_id}: {e}")
                unmatched_seeds.append(UnmatchedSeed(
                    input_id=paper_id,
                    error=str(e)
                ))
        
        self.logger.info(
            f"Matching complete: {len(matched_seeds)} matched, "
            f"{len(unmatched_seeds)} unmatched"
        )
        
        return SeedMatchResult(
            matched_seeds=matched_seeds,
            unmatched_seeds=unmatched_seeds,
            total_matched=len(matched_seeds),
            total_unmatched=len(unmatched_seeds)
        )
    
    def validate_paper_id(self, paper_id: str) -> bool:

        try:
            from ArticleCrawler.cli.ui.validators import validate_paper_id
            return validate_paper_id(paper_id)
        except ImportError:
            return bool(paper_id and len(paper_id) > 0)
    
    def aggregate_seeds(self, match_results: List[SeedMatchResult]) -> List[MatchedSeed]:

        all_seeds = []
        seen_ids = set()
        
        for result in match_results:
            for seed in result.matched_seeds:
                if seed.paper_id not in seen_ids:
                    all_seeds.append(seed)
                    seen_ids.add(seed.paper_id)
        
        self.logger.info(f"Aggregated {len(all_seeds)} unique seeds from {len(match_results)} sources")
        return all_seeds
    
    def _get_api_client(self, provider: str) -> BaseAPIProvider:
        """Get API client for the specified provider using ArticleCrawler factory."""
        return create_api_provider(provider)
    
    def _fetch_paper_metadata(self, api: BaseAPIProvider, paper_id: str, provider: str):

        try:
            if provider == "openalex":
                if hasattr(api, 'get_paper_metadata_only'):
                    paper_data = api.get_paper_metadata_only(paper_id)
                    return paper_data
                else:
                    paper = api.get_paper(paper_id)
                    return paper
            else:
                paper = api.get_paper(paper_id)
                return paper
                
        except Exception as e:
            self.logger.warning(f"Failed to fetch paper {paper_id}: {e}")
            return None
    
    def _create_matched_seed(self, paper_data, original_id: str, provider: str) -> MatchedSeed:

        if provider == "openalex":
            return self._create_seed_from_openalex(paper_data, original_id)
        elif provider == "semantic_scholar":
            return self._create_seed_from_s2(paper_data, original_id)
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    def _create_seed_from_openalex(self, paper_data, original_id: str) -> MatchedSeed:
 
        if isinstance(paper_data, dict):
            paper_id = paper_data.get('id', '')
            if '/' in paper_id:
                paper_id = paper_id.split('/')[-1]
            
            title = paper_data.get('title')
            
            authors = None
            authorships = paper_data.get('authorships', [])
            if authorships:
                author_names = []
                for authorship in authorships[:3]:
                    author = authorship.get('author', {})
                    name = author.get('display_name', '')
                    if name:
                        author_names.append(name)
                
                if author_names:
                    authors = ', '.join(author_names)
                    if len(authorships) > 3:
                        authors += ' et al.'
            
            year = paper_data.get('publication_year')
            
            venue = None
            primary_location = paper_data.get('primary_location', {})
            if primary_location:
                source = primary_location.get('source', {})
                if source:
                    venue = source.get('display_name')
            
            cited_by = paper_data.get('cited_by_count') if isinstance(paper_data.get('cited_by_count'), int) else None
            refs = paper_data.get('referenced_works')
            references_count = len(refs) if isinstance(refs, list) else None
            doi = paper_data.get('doi') or None
            landing_url = None
            try:
                if primary_location:
                    landing_url = primary_location.get('landing_page_url') or None
            except Exception:
                landing_url = None
            abstract = paper_data.get('abstract') or None
            if not abstract:
                inv = paper_data.get('abstract_inverted_index')
                if isinstance(inv, dict):
                    try:
                        max_pos = 0
                        for word, positions in inv.items():
                            if positions:
                                max_pos = max(max_pos, max(positions))
                        tokens = [''] * (max_pos + 1)
                        for word, positions in inv.items():
                            for pos in positions:
                                tokens[pos] = word
                        abstract = ' '.join([t for t in tokens if t]) or None
                    except Exception:
                        abstract = None
            institutions = None
            try:
                if authorships:
                    names = []
                    for auth in authorships:
                        for inst in (auth.get('institutions') or []):
                            n = inst.get('display_name') or inst.get('name')
                            if n:
                                names.append(n)
                    if names:
                        seen = set()
                        dedup = []
                        for n in names:
                            if n not in seen:
                                seen.add(n)
                                dedup.append(n)
                        institutions = dedup
            except Exception:
                institutions = None
            return MatchedSeed(
                paper_id=paper_id,
                title=title,
                authors=authors,
                year=year,
                venue=venue,
                confidence=1.0,
                match_method="Direct ID" if original_id == paper_id else "API Lookup",
                cited_by_count=cited_by,
                references_count=references_count,
                doi=doi,
                url=landing_url,
                abstract=abstract,
                institutions=institutions,
            )
        
        else:
            paper_id = paper_data.id if hasattr(paper_data, 'id') else str(paper_data)
            if '/' in paper_id:
                paper_id = paper_id.split('/')[-1]
            
            title = paper_data.title if hasattr(paper_data, 'title') else None
            
            authors = None
            if hasattr(paper_data, 'authorships') and paper_data.authorships:
                author_names = []
                for authorship in paper_data.authorships[:3]:
                    if hasattr(authorship, 'author') and hasattr(authorship.author, 'display_name'):
                        author_names.append(authorship.author.display_name)
                
                if author_names:
                    authors = ', '.join(author_names)
                    if len(paper_data.authorships) > 3:
                        authors += ' et al.'
            
            year = paper_data.publication_year if hasattr(paper_data, 'publication_year') else None
            
            venue = None
            if hasattr(paper_data, 'primary_location') and paper_data.primary_location:
                if hasattr(paper_data.primary_location, 'source') and paper_data.primary_location.source:
                    if hasattr(paper_data.primary_location.source, 'display_name'):
                        venue = paper_data.primary_location.source.display_name
            
            cited_by = getattr(paper_data, 'cited_by_count', None) if hasattr(paper_data, 'cited_by_count') else None
            references_count = None
            if hasattr(paper_data, 'referenced_works'):
                refs = getattr(paper_data, 'referenced_works')
                references_count = len(refs) if isinstance(refs, list) else None
            doi = getattr(paper_data, 'doi', None) if hasattr(paper_data, 'doi') else None
            landing_url = None
            try:
                pl = getattr(paper_data, 'primary_location', None)
                if pl and hasattr(pl, 'landing_page_url'):
                    landing_url = pl.landing_page_url or None
            except Exception:
                landing_url = None
            abstract = None
            if hasattr(paper_data, 'abstract'):
                abstract = getattr(paper_data, 'abstract') or None
            elif hasattr(paper_data, 'abstract_inverted_index'):
                inv = getattr(paper_data, 'abstract_inverted_index')
                if isinstance(inv, dict):
                    try:
                        max_pos = 0
                        for word, positions in inv.items():
                            if positions:
                                max_pos = max(max_pos, max(positions))
                        tokens = [''] * (max_pos + 1)
                        for word, positions in inv.items():
                            for pos in positions:
                                tokens[pos] = word
                        abstract = ' '.join([t for t in tokens if t]) or None
                    except Exception:
                        abstract = None
            institutions = None
            try:
                if hasattr(paper_data, 'authorships') and paper_data.authorships:
                    names = []
                    for auth in paper_data.authorships:
                        if hasattr(auth, 'institutions') and auth.institutions:
                            for inst in auth.institutions:
                                nm = None
                                if hasattr(inst, 'display_name'):
                                    nm = inst.display_name
                                elif hasattr(inst, 'name'):
                                    nm = inst.name
                                if nm:
                                    names.append(nm)
                    if names:
                        seen = set()
                        dedup = []
                        for n in names:
                            if n not in seen:
                                seen.add(n)
                                dedup.append(n)
                        institutions = dedup
            except Exception:
                institutions = None
            return MatchedSeed(
                paper_id=paper_id,
                title=title,
                authors=authors,
                year=year,
                venue=venue,
                confidence=1.0,
                match_method="Direct ID" if original_id == paper_id else "API Lookup",
                cited_by_count=cited_by if isinstance(cited_by, int) else None,
                references_count=references_count,
                doi=doi,
                url=landing_url,
                abstract=abstract,
                institutions=institutions,
            )
    
    def _create_seed_from_s2(self, paper_data, original_id: str) -> MatchedSeed:
        """Create MatchedSeed from Semantic Scholar paper data."""
        if isinstance(paper_data, dict):
            paper_id = paper_data.get('paperId', '')
            title = paper_data.get('title')
            
            authors = None
            authors_list = paper_data.get('authors', [])
            if authors_list:
                author_names = [a.get('name', '') for a in authors_list[:3] if a.get('name')]
                if author_names:
                    authors = ', '.join(author_names)
                    if len(authors_list) > 3:
                        authors += ' et al.'
            
            year = paper_data.get('year')
            venue = paper_data.get('venue')
            
            return MatchedSeed(
                paper_id=paper_id,
                title=title,
                authors=authors,
                year=year,
                venue=venue,
                confidence=1.0,
                match_method="Direct ID" if original_id == paper_id else "API Lookup"
            )
        
        else:
            paper_id = paper_data.paperId if hasattr(paper_data, 'paperId') else str(paper_data)
            title = paper_data.title if hasattr(paper_data, 'title') else None
            
            authors = None
            if hasattr(paper_data, 'authors') and paper_data.authors:
                author_names = [a.name for a in paper_data.authors[:3] if hasattr(a, 'name')]
                if author_names:
                    authors = ', '.join(author_names)
                    if len(paper_data.authors) > 3:
                        authors += ' et al.'
            
            year = paper_data.year if hasattr(paper_data, 'year') else None
            venue = paper_data.venue if hasattr(paper_data, 'venue') else None
            
            return MatchedSeed(
                paper_id=paper_id,
                title=title,
                authors=authors,
                year=year,
                venue=venue,
                confidence=1.0,
                match_method="Direct ID" if original_id == paper_id else "API Lookup"
            )
