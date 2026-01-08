import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set

from app.core.exceptions import InvalidInputException
from app.schemas.seeds import MatchedSeed
from app.schemas.seed_session import SessionSeedsResponse
from app.schemas.staging import StagingPaperCreate
from app.services.library.edit_service import LibraryEditService
from app.services.library.helpers import LibraryPathResolver, LibraryWorkflowRunner
from app.services.library.service import LibraryService
from app.services.seeds.session_service import SeedSessionService
from app.services.staging.service import StagingService


@dataclass
class LibraryEditState:
    library_path: str
    api_provider: str
    original_paper_ids: Set[str] = field(default_factory=set)


class LibraryEditStateStore:
    """Keep track of edit state per session."""

    def __init__(self):
        self._storage: Dict[str, LibraryEditState] = {}

    def get(self, session_id: str) -> Optional[LibraryEditState]:
        return self._storage.get(session_id)

    def save(self, session_id: str, state: LibraryEditState) -> LibraryEditState:
        self._storage[session_id] = state
        return state

    def delete(self, session_id: str) -> None:
        self._storage.pop(session_id, None)


@dataclass
class LibraryEditSelectionSummary:
    session_id: str
    total_staged: int
    total_seeds: int


@dataclass
class LibraryEditDiff:
    session_id: str
    added_ids: List[str]
    removed_ids: List[str]
    api_provider: str
    library_path: str


class LibraryEditWorkflowService:
    """Coordinate the edit workflow between library, staging, and seed sessions."""

    def __init__(
        self,
        *,
        logger: logging.Logger,
        library_service: LibraryService,
        library_edit_service: LibraryEditService,
        seed_session_service: SeedSessionService,
        staging_service: StagingService,
        workflow_runner: LibraryWorkflowRunner,
        path_resolver: LibraryPathResolver,
        state_store: Optional[LibraryEditStateStore] = None,
        library_manager_factory=None,
    ):
        self._logger = logger
        self._library_service = library_service
        self._library_edit_service = library_edit_service
        self._seed_session_service = seed_session_service
        self._staging_service = staging_service
        self._workflow_runner = workflow_runner
        self._path_resolver = path_resolver
        self._state_store = state_store or LibraryEditStateStore()
        self._library_manager_factory = library_manager_factory

    def stage_library(self, session_id: str) -> LibraryEditSelectionSummary:
        details = self._library_service.get_details(session_id)
        library_path = details.get("path") if details else None
        if not library_path:
            raise InvalidInputException("Library path not selected. Use /library/{session}/select first.")

        papers = self._library_edit_service.list_papers(details)
        seeds = self._build_seeds_from_entries(papers)
        staging_payloads = self._build_staging_rows(details, papers)

        self._staging_service.clear_session(session_id)
        created_rows = self._staging_service.add_rows(session_id, staging_payloads)
        self._seed_session_service.set_seeds_for_session(session_id, seeds)

        api_provider = self._resolve_api_provider(Path(library_path))
        state = LibraryEditState(
            library_path=str(library_path),
            api_provider=api_provider,
            original_paper_ids={seed.paper_id for seed in seeds},
        )
        self._state_store.save(session_id, state)

        return LibraryEditSelectionSummary(
            session_id=session_id,
            total_staged=len(created_rows),
            total_seeds=len(seeds),
        )

    def summarize_changes(self, session_id: str, seed_response: SessionSeedsResponse) -> LibraryEditDiff:
        state = self._state_store.get(session_id)
        if not state:
            raise InvalidInputException("Library edit session state not found. Stage a library first.")

        selected_ids = {seed.paper_id for seed in (seed_response.seeds or []) if seed.paper_id}
        added = sorted(selected_ids - state.original_paper_ids)
        removed = sorted(state.original_paper_ids - selected_ids)

        return LibraryEditDiff(
            session_id=session_id,
            added_ids=added,
            removed_ids=removed,
            api_provider=state.api_provider,
            library_path=state.library_path,
        )

    def commit_update(
        self,
        session_id: str,
        seed_response: SessionSeedsResponse,
    ) -> LibraryEditDiff:
        diff = self.summarize_changes(session_id, seed_response)
        details = self._library_service.get_details(session_id)
        if not details.get("path"):
            raise InvalidInputException("Library path missing for this session.")

        if diff.added_ids:
            self._library_edit_service.add_seeds(details, diff.added_ids, api_provider=diff.api_provider)
        if diff.removed_ids:
            self._library_edit_service.remove_seeds(details, diff.removed_ids)

        state = self._state_store.get(session_id)
        if state:
            new_ids = {seed.paper_id for seed in (seed_response.seeds or []) if seed.paper_id}
            state.original_paper_ids = new_ids
            self._state_store.save(session_id, state)

        return diff

    def duplicate_library(
        self,
        session_id: str,
        seed_response: SessionSeedsResponse,
        *,
        target_path: str,
        name: Optional[str],
        description: Optional[str],
    ) -> Dict:
        seeds = [seed for seed in (seed_response.seeds or []) if seed.paper_id]
        if not seeds:
            raise InvalidInputException("No seeds selected to duplicate into a new library.")

        resolved_target = self._path_resolver.ensure_absolute(target_path)
        details = self._library_service.get_details(session_id)
        resolved_name = self._resolve_duplicate_name(details, name)
        description = description or details.get("description") if details else description
        resolved_description = description or (details.get("description") if details else None)
        result = self._workflow_runner.create_library(
            name=resolved_name,
            base_path=str(resolved_target),
            paper_ids=[seed.paper_id for seed in seeds],
            description=resolved_description,
        )
        return result

    def get_state(self, session_id: str) -> Optional[LibraryEditState]:
        return self._state_store.get(session_id)

    def clear_state(self, session_id: str) -> None:
        self._state_store.delete(session_id)

    def _build_seeds_from_entries(self, entries: List[Dict]) -> List[MatchedSeed]:
        seeds: List[MatchedSeed] = []
        for entry in entries or []:
            paper_id = entry.get("paper_id")
            if not paper_id:
                continue
            authors = entry.get("authors")
            author_str = ", ".join(authors) if isinstance(authors, list) else authors
            seeds.append(
                MatchedSeed(
                    paper_id=paper_id,
                    title=entry.get("title"),
                    authors=author_str,
                    year=entry.get("year"),
                    venue=entry.get("venue"),
                    doi=entry.get("doi"),
                    url=entry.get("url"),
                    abstract=entry.get("abstract"),
                    source="Existing Library",
                    source_type="manual",
                    source_id=paper_id,
                )
            )
        return seeds

    def _build_staging_rows(self, details: Dict, entries: List[Dict]) -> List[StagingPaperCreate]:
        label = details.get("name") or "Library"
        rows: List[StagingPaperCreate] = []
        for entry in entries or []:
            paper_id = entry.get("paper_id")
            if not paper_id:
                continue
            authors = entry.get("authors")
            author_str = ", ".join(authors) if isinstance(authors, list) else authors
            rows.append(
                StagingPaperCreate(
                    source=f"Library: {label}",
                    source_type="manual",
                    is_library_seed=True,
                    title=entry.get("title"),
                    authors=author_str,
                    year=entry.get("year"),
                    venue=entry.get("venue"),
                    doi=entry.get("doi"),
                    url=entry.get("url"),
                    abstract=entry.get("abstract"),
                    source_id=paper_id,
                    is_selected=True,
                )
            )
        return rows

    def _resolve_api_provider(self, library_path: Path) -> str:
        try:
            manager_factory = self._library_manager_factory or self._default_library_manager
            manager = manager_factory()
            config = manager.load_library_config(library_path)
            return getattr(config, "api_provider", "openalex") or "openalex"
        except Exception:
            return "openalex"

    def _resolve_duplicate_name(self, details: Optional[Dict], override: Optional[str]) -> str:
        if override and override.strip():
            return override.strip()
        base_name = (details or {}).get("name") or "Library"
        return f"{base_name} (Copy)"

    def _default_library_manager(self):
        from ArticleCrawler.library.library_manager import LibraryManager

        return LibraryManager(self._logger)
