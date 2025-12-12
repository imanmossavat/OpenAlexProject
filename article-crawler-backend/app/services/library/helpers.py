from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from app.core.exceptions import InvalidInputException


class LibraryDetailsStore:
    """In-memory persistence for library details per session."""

    def __init__(self):
        self._storage: Dict[str, Dict[str, Optional[str]]] = {}

    def _default_record(self) -> Dict[str, Optional[str]]:
        return {"name": None, "path": None, "description": None}

    def get(self, session_id: str) -> Dict[str, Optional[str]]:
        record = self._storage.setdefault(session_id, self._default_record().copy())
        return dict(record)

    def update(
        self,
        session_id: str,
        *,
        name: str,
        path: str,
        description: Optional[str],
    ) -> Dict[str, Optional[str]]:
        record = self._storage.setdefault(session_id, self._default_record().copy())
        record.update({"name": name, "path": path, "description": description})
        return dict(record)


class LibraryPathResolver:
    """Resolve and validate library paths based on API configuration."""

    def __init__(self, articlecrawler_path: str):
        self._base = Path(articlecrawler_path)

    def resolve(self, raw_path: Optional[str]) -> Path:
        """Resolve a library path, defaulting to ArticleCrawler/libraries."""
        if raw_path is None or not str(raw_path).strip():
            return self._base / "libraries"
        return self.ensure_absolute(raw_path)

    def ensure_absolute(self, raw_path: str) -> Path:
        try:
            candidate = Path(raw_path)
        except Exception as exc:
            raise InvalidInputException(f"Invalid path: {exc}")
        if not candidate.is_absolute():
            raise InvalidInputException("Library path must be an absolute path")
        return candidate


class LibraryMetadataFormatter:
    """Normalize ArticleCrawler paper objects into API payloads."""

    def format(self, entries: Optional[List[Any]]) -> List[Dict[str, Any]]:
        payload: List[Dict[str, Any]] = []
        for entry in entries or []:
            payload.append(
                {
                    "paper_id": getattr(entry, "paper_id", None),
                    "title": getattr(entry, "title", "") or "",
                    "authors": self._author_names(getattr(entry, "authors", [])),
                    "year": getattr(entry, "year", None),
                    "venue": getattr(entry, "venue", None),
                    "doi": getattr(entry, "doi", None),
                    "url": getattr(entry, "url", None),
                    "abstract": getattr(entry, "abstract", None),
                }
            )
        return payload

    def _author_names(self, authors) -> List[str]:
        names: List[str] = []
        if not isinstance(authors, list):
            return names
        for author in authors:
            try:
                if isinstance(author, dict):
                    name = author.get("name") or author.get("authorName") or ""
                else:
                    name = str(author).strip()
                if name:
                    names.append(name)
            except Exception:
                continue
        return names


class LibraryWorkflowRunner:
    """Coordinate the ArticleCrawler library creation workflow."""

    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        metadata_formatter: Optional[LibraryMetadataFormatter] = None,
        orchestrator_factory: Optional[Callable[[], Any]] = None,
        library_manager_factory: Optional[Callable[[], Any]] = None,
        paper_reader_factory: Optional[Callable[[], Any]] = None,
        api_provider: str = "openalex",
    ):
        self._logger = logger or logging.getLogger(__name__)
        self._metadata_formatter = metadata_formatter or LibraryMetadataFormatter()
        self._orchestrator_factory = orchestrator_factory or (
            lambda: self._default_orchestrator(api_provider)
        )
        self._library_manager_factory = library_manager_factory or self._default_library_manager
        self._paper_reader_factory = paper_reader_factory or self._default_paper_reader

    def create_library(
        self,
        *,
        name: str,
        base_path: str,
        paper_ids: List[str],
        description: Optional[str],
    ) -> Dict[str, Any]:
        orchestrator = self._orchestrator_factory()
        library_root = Path(base_path)
        target_path = library_root / name if library_root.name != name else library_root
        config = orchestrator.create_library(
            library_name=name,
            library_path=target_path,
            paper_ids=paper_ids,
            description=description,
        )

        manager = self._library_manager_factory()
        reader = self._paper_reader_factory()

        papers_dir = manager.get_papers_directory(config.base_path)
        saved_files = manager.get_all_paper_files(config.base_path)
        paper_entries = reader.read_papers_from_directory(papers_dir)
        formatted = self._metadata_formatter.format(paper_entries)

        return {
            "name": config.name,
            "base_path": str(config.base_path),
            "total_requested": len(paper_ids),
            "saved_count": len(saved_files),
            "papers": formatted,
        }

    def _default_orchestrator(self, api_provider: str):
        from ArticleCrawler.usecases.library_creation import (
            LibraryCreationOrchestrator,
        )

        return LibraryCreationOrchestrator(api_provider=api_provider, logger=self._logger)

    def _default_library_manager(self):
        from ArticleCrawler.library.library_manager import LibraryManager

        return LibraryManager(self._logger)

    def _default_paper_reader(self):
        from ArticleCrawler.library.paper_file_reader import PaperFileReader

        return PaperFileReader(self._logger)
