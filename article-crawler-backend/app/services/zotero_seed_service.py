

import logging
from typing import List, Dict, Optional
from datetime import datetime

from ArticleCrawler.api.zotero.client import ZoteroClient
from ArticleCrawler.api.zotero.metadata_extractor import ZoteroMetadataExtractor
from ArticleCrawler.api.zotero.matching.matcher import ZoteroMatcher, MatchResult
from ArticleCrawler.api.api_factory import create_api_provider

from app.schemas.zotero_seeds import (
    ZoteroCollection,
    ZoteroItemMetadata,
    ZoteroMatchResult,
    ZoteroMatchCandidate
)
from app.schemas.seeds import MatchedSeed
from app.core.exceptions import InvalidInputException


class ZoteroSeedService:

    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.metadata_extractor = ZoteroMetadataExtractor()
        

        self._staging_storage: Dict[str, Dict] = {}

        self._match_results_storage: Dict[str, List[ZoteroMatchResult]] = {}
        

        self._collections_cache: Dict[str, Dict[str, str]] = {}
    
    def check_zotero_availability(self) -> tuple[bool, Optional[str]]:

        try:
            ZoteroClient(logger=self.logger)
            return True, None
        except ValueError as e:
            return False, str(e)
        except Exception as e:
            self.logger.error(f"Unexpected error checking Zotero availability: {e}")
            return False, f"Zotero error: {str(e)}"
    
    def get_collections(self, session_id: str) -> List[ZoteroCollection]:

        try:
            client = ZoteroClient(logger=self.logger)
            collections = client.get_collections()
            
            self._collections_cache[session_id] = {
                col['key']: col['name'] for col in collections
            }
            
            result = []
            for col in collections:
                parent = col['data'].get('parentCollection')
                if parent is False or parent == '':
                    parent = None
                    
                result.append(ZoteroCollection(
                    key=col['key'],
                    name=col['name'],
                    parent_collection=parent
                ))
            
            self.logger.info(f"Retrieved {len(result)} Zotero collections for session {session_id}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error retrieving Zotero collections: {e}")
            raise InvalidInputException(f"Failed to retrieve Zotero collections: {str(e)}")
    
    def get_collection_items(
        self,
        session_id: str,
        collection_key: str
    ) -> tuple[str, List[ZoteroItemMetadata]]:

        try:
            client = ZoteroClient(logger=self.logger)
            
            collection_name = self._collections_cache.get(session_id, {}).get(
                collection_key, 
                "Unknown Collection"
            )
            
            items = client.get_collection_items(collection_key)
            
            items_metadata = []
            for item in items:
                metadata_dict = self.metadata_extractor.extract(item)
                
                metadata_dict['collection_key'] = collection_key
                
                item_metadata = ZoteroItemMetadata(**metadata_dict)
                items_metadata.append(item_metadata)
            
            self.logger.info(
                f"Retrieved {len(items_metadata)} items from collection '{collection_name}'"
            )
            return collection_name, items_metadata
            
        except Exception as e:
            self.logger.error(f"Error retrieving collection items: {e}")
            raise InvalidInputException(f"Failed to retrieve collection items: {str(e)}")
    
    def initialize_staging(self, session_id: str):
        """Initialize staging area for a session if not exists."""
        if session_id not in self._staging_storage:
            self._staging_storage[session_id] = {
                'items': {},
                'created_at': datetime.now()
            }
    
    def stage_items(
        self,
        session_id: str,
        items: List[ZoteroItemMetadata]
    ) -> int:

        self.initialize_staging(session_id)
        
        staged_count = 0
        for item in items:
            if item.zotero_key not in self._staging_storage[session_id]['items']:
                self._staging_storage[session_id]['items'][item.zotero_key] = item
                staged_count += 1
        
        self.logger.info(f"Staged {staged_count} new items for session {session_id}")
        return staged_count
    
    def get_staged_items(self, session_id: str) -> List[ZoteroItemMetadata]:

        self.initialize_staging(session_id)
        items = list(self._staging_storage[session_id]['items'].values())
        
        self.logger.info(f"Retrieved {len(items)} staged items for session {session_id}")
        return items
    
    def remove_staged_item(self, session_id: str, zotero_key: str):

        self.initialize_staging(session_id)
        
        if zotero_key in self._staging_storage[session_id]['items']:
            del self._staging_storage[session_id]['items'][zotero_key]
            self.logger.info(f"Removed item {zotero_key} from staging for session {session_id}")
        else:
            raise InvalidInputException(f"Item {zotero_key} not found in staging area")
    
    def match_staged_items(
        self,
        session_id: str,
        api_provider: str = "openalex"
    ) -> List[ZoteroMatchResult]:

        staged_items = self.get_staged_items(session_id)
        
        if not staged_items:
            self.logger.warning(f"No staged items to match for session {session_id}")
            return []
        
        try:
            api = create_api_provider(api_provider)
            
            matcher = ZoteroMatcher(api, logger=self.logger)
            
            items_metadata = [item.model_dump() for item in staged_items]
            
            match_results: List[MatchResult] = matcher.match_items(items_metadata)
            
            results = []
            for match_result in match_results:
                candidates = []
                for cand in match_result.candidates:
                    candidates.append(ZoteroMatchCandidate(
                        paper_id=cand.paper_id,
                        title=cand.title,
                        similarity=cand.similarity,
                        year=cand.year,
                        venue=cand.venue,
                        doi=cand.doi
                    ))
                
                results.append(ZoteroMatchResult(
                    zotero_key=match_result.zotero_key,
                    title=match_result.title,
                    matched=match_result.matched,
                    paper_id=match_result.paper_id,
                    confidence=match_result.confidence,
                    match_method=match_result.match_method,
                    error=match_result.error,
                    candidates=candidates
                ))
            
            self.logger.info(
                f"Matched {len(results)} items for session {session_id}. "
                f"Successful: {sum(1 for r in results if r.matched)}"
            )
            
            self._match_results_storage[session_id] = results
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error matching staged items: {e}")
            raise InvalidInputException(f"Failed to match items: {str(e)}")
    
    def get_confirmed_seeds(
        self,
        session_id: str,
        action: str,
        manual_selections: List[Dict]
    ) -> List[MatchedSeed]:

        if action == "skip_all":
            self.logger.info("User chose to skip all matches")
            return []
        
        match_results = self._match_results_storage.get(session_id, [])
        if not match_results:
            raise InvalidInputException("No match results found. Please run match first.")
        
        staged_items = self.get_staged_items(session_id)
        items_by_key = {item.zotero_key: item for item in staged_items}
        collections_cache = self._collections_cache.get(session_id, {})
        
        matches_by_key = {match.zotero_key: match for match in match_results}
        
        seeds = []

        try:
            api = create_api_provider("openalex")
        except Exception:
            api = None

        def _extract_enrichments(paper) -> Dict:
            """Extract optional enrichment fields from OpenAlex paper (dict or object)."""
            extras: Dict = {
                "doi": None,
                "url": None,
                "abstract": None,
                "cited_by_count": None,
                "references_count": None,
                "institutions": None,
            }
            try:
                if isinstance(paper, dict):
                    cited_by = paper.get('cited_by_count')
                    if isinstance(cited_by, int):
                        extras["cited_by_count"] = cited_by
                    refs = paper.get('referenced_works')
                    extras["references_count"] = len(refs) if isinstance(refs, list) else None
                    extras["doi"] = paper.get('doi') or None
                    pl = paper.get('primary_location') or {}
                    if isinstance(pl, dict):
                        extras["url"] = pl.get('landing_page_url') or None
                    abstract = paper.get('abstract') or None
                    if not abstract:
                        inv = paper.get('abstract_inverted_index')
                        if isinstance(inv, dict):
                            try:
                                max_pos = 0
                                for _, positions in inv.items():
                                    if positions:
                                        max_pos = max(max_pos, max(positions))
                                tokens = [''] * (max_pos + 1)
                                for word, positions in inv.items():
                                    for pos in positions:
                                        tokens[pos] = word
                                abstract = ' '.join([t for t in tokens if t]) or None
                            except Exception:
                                abstract = None
                    extras["abstract"] = abstract
                    inst_names = []
                    for auth in (paper.get('authorships') or []):
                        for inst in (auth.get('institutions') or []):
                            name = inst.get('display_name') or inst.get('name')
                            if name:
                                inst_names.append(name)
                    if inst_names:
                        seen = set()
                        dedup = []
                        for n in inst_names:
                            if n not in seen:
                                seen.add(n)
                                dedup.append(n)
                        extras["institutions"] = dedup
                else:
                    cited_by = getattr(paper, 'cited_by_count', None)
                    if isinstance(cited_by, int):
                        extras["cited_by_count"] = cited_by
                    refs = getattr(paper, 'referenced_works', None)
                    extras["references_count"] = len(refs) if isinstance(refs, list) else None
                    extras["doi"] = getattr(paper, 'doi', None) if hasattr(paper, 'doi') else None
                    url = None
                    try:
                        pl = getattr(paper, 'primary_location', None)
                        if pl and hasattr(pl, 'landing_page_url'):
                            url = pl.landing_page_url or None
                    except Exception:
                        url = None
                    extras["url"] = url
                    abstract = None
                    if hasattr(paper, 'abstract'):
                        abstract = getattr(paper, 'abstract') or None
                    elif hasattr(paper, 'abstract_inverted_index'):
                        inv = getattr(paper, 'abstract_inverted_index')
                        if isinstance(inv, dict):
                            try:
                                max_pos = 0
                                for _, positions in inv.items():
                                    if positions:
                                        max_pos = max(max_pos, max(positions))
                                tokens = [''] * (max_pos + 1)
                                for word, positions in inv.items():
                                    for pos in positions:
                                        tokens[pos] = word
                                abstract = ' '.join([t for t in tokens if t]) or None
                            except Exception:
                                abstract = None
                    extras["abstract"] = abstract
                    inst_names = []
                    try:
                        auths = getattr(paper, 'authorships', None)
                        if auths:
                            for auth in auths:
                                if hasattr(auth, 'institutions') and auth.institutions:
                                    for inst in auth.institutions:
                                        nm = None
                                        if hasattr(inst, 'display_name'):
                                            nm = inst.display_name
                                        elif hasattr(inst, 'name'):
                                            nm = inst.name
                                        if nm:
                                            inst_names.append(nm)
                    except Exception:
                        pass
                    if inst_names:
                        seen = set()
                        dedup = []
                        for n in inst_names:
                            if n not in seen:
                                seen.add(n)
                                dedup.append(n)
                        extras["institutions"] = dedup
            except Exception:
                pass
            return extras
        
        for match_result in match_results:
            if match_result.matched:
                zotero_key = match_result.zotero_key
                
                if zotero_key not in items_by_key:
                    self.logger.warning(f"Zotero item {zotero_key} not found in staging")
                    continue
                
                item = items_by_key[zotero_key]
                
                authors_str = None
                if item.authors:
                    authors_str = ', '.join(item.authors[:3])
                    if len(item.authors) > 3:
                        authors_str += ' et al.'
                
                enrich = {}
                if api and match_result.paper_id:
                    try:
                        paper = api.get_paper_metadata_only(match_result.paper_id) if hasattr(api, 'get_paper_metadata_only') else api.get_paper(match_result.paper_id)
                        enrich = _extract_enrichments(paper)
                    except Exception:
                        enrich = {}

                collection_label = collections_cache.get(item.collection_key)
                source_label = f"Zotero - {collection_label}" if collection_label else "Zotero"

                seed = MatchedSeed(
                    paper_id=match_result.paper_id,
                    title=item.title,
                    authors=authors_str,
                    year=item.year,
                    venue=item.publication or None,
                    confidence=match_result.confidence,
                    match_method=match_result.match_method or "auto",
                    doi=enrich.get("doi"),
                    url=enrich.get("url"),
                    abstract=enrich.get("abstract"),
                    cited_by_count=enrich.get("cited_by_count"),
                    references_count=enrich.get("references_count"),
                    institutions=enrich.get("institutions"),
                    source=source_label,
                    source_type="zotero",
                    source_id=zotero_key,
                )
                seeds.append(seed)
        
        for selection in manual_selections:
            if selection.get('action') == 'select':
                zotero_key = selection['zotero_key']
                selected_paper_id = selection.get('selected_paper_id')
                
                if not selected_paper_id:
                    self.logger.warning(f"No paper_id provided for manual selection {zotero_key}")
                    continue
                
                match_result = matches_by_key.get(zotero_key)
                if not match_result:
                    self.logger.warning(f"Match result not found for {zotero_key}")
                    continue
                
                selected_candidate = None
                for candidate in match_result.candidates:
                    if candidate.paper_id == selected_paper_id:
                        selected_candidate = candidate
                        break
                
                if not selected_candidate:
                    self.logger.warning(
                        f"Selected paper_id {selected_paper_id} not found in candidates for {zotero_key}"
                    )
                    continue
                

                try:
                    paper = None
                    if api:
                        paper = api.get_paper_metadata_only(selected_paper_id) if hasattr(api, 'get_paper_metadata_only') else api.get_paper(selected_paper_id)
                    
                    authors_str = None
                    if isinstance(paper, dict):
                        authors_list = paper.get('authorships', [])
                        if authors_list:
                            author_names = [a.get('author', {}).get('display_name', '') for a in authors_list[:3]]
                            authors_str = ', '.join([a for a in author_names if a])
                            if len(authors_list) > 3:
                                authors_str += ' et al.'
                    else:
                        if hasattr(paper, 'authorships') and paper.authorships:
                            author_names = [a.author.display_name for a in paper.authorships[:3] if hasattr(a, 'author')]
                            authors_str = ', '.join([a for a in author_names if a])
                            if len(paper.authorships) > 3:
                                authors_str += ' et al.'
                    enrich = _extract_enrichments(paper) if paper is not None else {}
                
                except Exception as e:
                    self.logger.warning(f"Failed to fetch authors for {selected_paper_id}: {e}")
                    authors_str = None
                    enrich = {}
                
                item = items_by_key.get(zotero_key)
                collection_label = None
                if item:
                    collection_label = collections_cache.get(item.collection_key)
                source_label = f"Zotero - {collection_label}" if collection_label else "Zotero"

                seed = MatchedSeed(
                    paper_id=selected_candidate.paper_id,
                    title=selected_candidate.title,
                    authors=authors_str,
                    year=selected_candidate.year,
                    venue=selected_candidate.venue,
                    confidence=selected_candidate.similarity,
                    match_method="manual_selection",
                    doi=enrich.get("doi"),
                    url=enrich.get("url"),
                    abstract=enrich.get("abstract"),
                    cited_by_count=enrich.get("cited_by_count"),
                    references_count=enrich.get("references_count"),
                    institutions=enrich.get("institutions"),
                    source=source_label,
                    source_type="zotero",
                    source_id=zotero_key,
                )
                seeds.append(seed)
        
        self.logger.info(
            f"Created {len(seeds)} MatchedSeed objects "
            f"({sum(1 for s in seeds if s.match_method != 'manual_selection')} auto, "
            f"{sum(1 for s in seeds if s.match_method == 'manual_selection')} manual)"
        )
        return seeds
    
    def clear_staging(self, session_id: str):

        if session_id in self._staging_storage:
            del self._staging_storage[session_id]
        if session_id in self._match_results_storage:
            del self._match_results_storage[session_id]
        self.logger.info(f"Cleared staging area and match results for session {session_id}")
    
    def cleanup_session(self, session_id: str):

        self.clear_staging(session_id)
        
        if session_id in self._collections_cache:
            del self._collections_cache[session_id]
        
        self.logger.info(f"Cleaned up Zotero session data for {session_id}")
