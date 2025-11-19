

import logging
from typing import List, Optional, Dict
from pathlib import Path


class LibraryEditService:
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)

    def _get_orchestrator(self):
        from ArticleCrawler.usecases.library_editing import LibraryEditOrchestrator
        return LibraryEditOrchestrator(logger=self.logger)

    def _ensure_selected(self, library_details: Dict) -> Path:
        path = library_details.get('path') if library_details else None
        if not path:
            raise ValueError("No library selected for this session. Use /library/{session_id}/select or provide path.")
        p = Path(path)
        if not p.is_absolute():
            raise ValueError("Library path must be absolute")
        return p

    def list_papers(self, library_details: Dict) -> List[Dict]:
        p = self._ensure_selected(library_details)
        orch = self._get_orchestrator()
        papers = orch.list_papers(p)
        out = []
        for pd in papers:
            raw_authors = getattr(pd, 'authors', []) or []
            authors: List[str] = []
            try:
                for a in raw_authors:
                    if isinstance(a, dict):
                        nm = a.get('name') or a.get('authorName') or ''
                        if nm:
                            authors.append(nm)
                    else:
                        s = str(a).strip()
                        if s:
                            authors.append(s)
            except Exception:
                authors = []

            out.append({
                'paper_id': pd.paper_id,
                'title': getattr(pd, 'title', '') or '',
                'authors': authors,
                'year': getattr(pd, 'year', None),
                'venue': getattr(pd, 'venue', None),
                'doi': getattr(pd, 'doi', None),
                'url': getattr(pd, 'url', None),
                'abstract': getattr(pd, 'abstract', None),
            })
        return out

    def add_seeds(self, library_details: Dict, paper_ids: List[str], api_provider: Optional[str] = None) -> Dict:
        p = self._ensure_selected(library_details)
        orch = self._get_orchestrator()
        return orch.add_papers(p, paper_ids, api_provider=api_provider)

    def remove_seeds(self, library_details: Dict, paper_ids: List[str]) -> Dict:
        p = self._ensure_selected(library_details)
        orch = self._get_orchestrator()
        return orch.remove_papers(p, paper_ids)
