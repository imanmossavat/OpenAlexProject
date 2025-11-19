

import logging
from pathlib import Path
from typing import Dict, Optional

from app.core.exceptions import InvalidInputException
from app.core.config import settings


class LibraryService:


    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self._storage: Dict[str, Dict] = {}

    def _ensure(self, session_id: str):
        if session_id not in self._storage:
            self._storage[session_id] = {
                "name": None,
                "path": None,
                "description": None,
            }

    def set_details(self, session_id: str, name: str, path: Optional[str], description: Optional[str]):
        self._ensure(session_id)
        if path is None or str(path).strip() == "":
            base = Path(settings.ARTICLECRAWLER_PATH)
            path_obj = base / "libraries"
        else:
            try:
                path_obj = Path(path)
            except Exception as e:
                raise InvalidInputException(f"Invalid path: {e}")
            if not path_obj.is_absolute():
                raise InvalidInputException("Library path must be an absolute path")

        self._storage[session_id].update({
            "name": name.strip(),
            "path": str(path_obj),
            "description": (description.strip() if description else None)
        })

        self.logger.info(f"Set library details for session {session_id}: name='{name}', path='{path_obj}'")
        return self._storage[session_id].copy()

    def get_details(self, session_id: str) -> Dict:
        self._ensure(session_id)
        return self._storage[session_id].copy()

    def preview(self, session_id: str, session_service) -> Dict:
        self._ensure(session_id)
        details = self._storage[session_id]
        if not details.get("name") or not details.get("path"):
            raise InvalidInputException("Library details not set. Please set name and path first.")

        session = session_service.get_session(session_id)
        total = len(session.seeds) if session and session.seeds else 0

        return {
            "name": details["name"],
            "path": details["path"],
            "description": details.get("description"),
            "total_papers": total
        }

    def create(self, session_id: str, session_service) -> Dict:
        details = self.get_details(session_id)
        if not details.get("name") or not details.get("path"):
            raise InvalidInputException("Library details not set. Please set name and path first.")

        session = session_service.get_session(session_id)
        if not session or not session.seeds:
            raise InvalidInputException("No seeds selected. Please add seeds before creating a library.")

        paper_ids = [s.paper_id for s in session.seeds]

        api_provider = "openalex"

        from ArticleCrawler.usecases.library_creation import LibraryCreationOrchestrator

        orchestrator = LibraryCreationOrchestrator(api_provider=api_provider, logger=self.logger)

        library_path = Path(details["path"]) / details["name"] if not Path(details["path"]).name == details["name"] else Path(details["path"]) 
        config = orchestrator.create_library(
            library_name=details["name"],
            library_path=library_path,
            paper_ids=paper_ids,
            description=details.get("description")
        )

        from ArticleCrawler.library.library_manager import LibraryManager
        from ArticleCrawler.library.paper_file_reader import PaperFileReader

        lm = LibraryManager(self.logger)
        papers_dir = lm.get_papers_directory(config.base_path)
        saved_files = lm.get_all_paper_files(config.base_path)
        saved_count = len(saved_files)

        reader = PaperFileReader(self.logger)
        paper_datas = reader.read_papers_from_directory(papers_dir)

        def _author_names(auth_list):
            if not isinstance(auth_list, list):
                return []
            names = []
            for a in auth_list:
                try:
                    if isinstance(a, dict):
                        nm = a.get('name') or a.get('authorName') or ''
                        if nm:
                            names.append(nm)
                    else:
                        s = str(a).strip()
                        if s:
                            names.append(s)
                except Exception:
                    continue
            return names

        papers_out = []
        for pd_obj in paper_datas:
            papers_out.append({
                "paper_id": pd_obj.paper_id,
                "title": getattr(pd_obj, 'title', '') or '',
                "authors": _author_names(getattr(pd_obj, 'authors', [])),
                "year": getattr(pd_obj, 'year', None),
                "venue": getattr(pd_obj, 'venue', None),
                "doi": getattr(pd_obj, 'doi', None),
                "url": getattr(pd_obj, 'url', None),
                "abstract": getattr(pd_obj, 'abstract', None),
            })

        return {
            "name": config.name,
            "base_path": str(config.base_path),
            "total_requested": len(paper_ids),
            "saved_count": saved_count,
            "papers": papers_out
        }
