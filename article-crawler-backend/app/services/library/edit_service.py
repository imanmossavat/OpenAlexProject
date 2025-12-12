import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from app.core.exceptions import InvalidInputException
from app.services.library.helpers import LibraryMetadataFormatter, LibraryPathResolver


class LibraryEditService:
    """Coordinate edit operations on an existing library."""

    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        metadata_formatter: Optional[LibraryMetadataFormatter] = None,
        path_resolver: Optional[LibraryPathResolver] = None,
        orchestrator_factory: Optional[Callable[[], Any]] = None,
    ):
        self.logger = logger or logging.getLogger(__name__)
        self._metadata_formatter = metadata_formatter or LibraryMetadataFormatter()
        self._path_resolver = path_resolver or LibraryPathResolver("")
        self._orchestrator_factory = orchestrator_factory or self._default_orchestrator

    def list_papers(self, library_details: Dict) -> List[Dict]:
        library_path = self._ensure_selected(library_details)
        orchestrator = self._orchestrator_factory()
        papers = orchestrator.list_papers(library_path)
        return self._metadata_formatter.format(papers)

    def add_seeds(
        self,
        library_details: Dict,
        paper_ids: List[str],
        api_provider: Optional[str] = None,
    ) -> Dict:
        library_path = self._ensure_selected(library_details)
        orchestrator = self._orchestrator_factory()
        return orchestrator.add_papers(library_path, paper_ids, api_provider=api_provider)

    def remove_seeds(self, library_details: Dict, paper_ids: List[str]) -> Dict:
        library_path = self._ensure_selected(library_details)
        orchestrator = self._orchestrator_factory()
        return orchestrator.remove_papers(library_path, paper_ids)

    def _ensure_selected(self, library_details: Dict) -> Path:
        path = library_details.get("path") if library_details else None
        if not path:
            raise ValueError(
                "No library selected for this session. Use /library/{session_id}/select or provide path."
            )
        try:
            resolved = self._path_resolver.ensure_absolute(path)
        except InvalidInputException as exc:
            raise ValueError(str(exc))
        return resolved

    def _default_orchestrator(self):
        from ArticleCrawler.usecases.library_editing import LibraryEditOrchestrator

        return LibraryEditOrchestrator(logger=self.logger)
