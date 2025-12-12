from pathlib import Path as FSPath
from typing import List, Optional

from fastapi import HTTPException

from ArticleCrawler.cli.utils.library_discovery import LibraryDiscovery
from ArticleCrawler.library.library_manager import LibraryManager

from app.schemas.library import (
    AddLibrarySeedsRequest,
    AddLibrarySeedsResponse,
    ApplySessionSeedsRequest,
    ApplySessionSeedsResponse,
    LibraryInfo,
    LibraryListResponse,
    LibrarySelectRequest,
    LibrarySelectionResponse,
)


class LibraryRouteHelper:
    """Encapsulates orchestration logic for library-related API routes."""

    def __init__(
        self,
        library_service,
        library_edit_service,
        seed_selection_service,
        seed_session_service,
    ):
        self.library_service = library_service
        self.library_edit_service = library_edit_service
        self.seed_selection_service = seed_selection_service
        self.seed_session_service = seed_session_service

    def discover_libraries(self, query: Optional[str], page: int, page_size: int) -> LibraryListResponse:
        discovery = LibraryDiscovery()
        found = discovery.find_libraries()

        normalized_query = query.strip().lower() if query else None
        if normalized_query:
            matched = [
                lib
                for lib in found
                if normalized_query in str(lib.get("name", "") or "").lower()
                or normalized_query in str(lib.get("description", "") or "").lower()
            ]
        else:
            matched = found

        total = len(matched)
        start = (page - 1) * page_size
        end = start + page_size
        page_items = matched[start:end] if start < total else []

        items: List[LibraryInfo] = []
        for lib in page_items:
            items.append(
                LibraryInfo(
                    name=str(lib.get("name", "")),
                    path=str(lib.get("path")),
                    description=lib.get("description"),
                    paper_count=int(lib.get("paper_count", 0) or 0),
                    api_provider=lib.get("api_provider"),
                    created_at=str(lib.get("created_at")) if lib.get("created_at") is not None else None,
                )
            )

        return LibraryListResponse(libraries=items, total=total, page=page, page_size=page_size)

    def select_existing_library(self, session_id: str, request: LibrarySelectRequest) -> LibrarySelectionResponse:
        library_path = FSPath(request.path)
        if not library_path.is_absolute():
            raise HTTPException(status_code=400, detail="Library path must be absolute")
        if not (library_path / "library_config.yaml").exists():
            raise HTTPException(status_code=400, detail=f"Not a valid library: {library_path}")

        manager = LibraryManager()
        config = manager.load_library_config(library_path)

        papers_dir = manager.get_papers_directory(library_path)
        paper_count = len(list(papers_dir.glob("*.md"))) if papers_dir.exists() else 0

        name = request.name or config.name or library_path.name
        details = self.library_service.set_details(
            session_id=session_id,
            name=name,
            path=str(library_path),
            description=getattr(config, "description", None),
        )

        return LibrarySelectionResponse(
            session_id=session_id,
            name=details["name"],
            path=details["path"],
            description=details.get("description"),
            paper_count=paper_count,
        )

    def add_library_seeds(self, session_id: str, request: AddLibrarySeedsRequest) -> AddLibrarySeedsResponse:
        details = self.library_service.get_details(session_id)
        provider: Optional[str] = request.api_provider

        paper_ids: List[str]
        if request.seeds:
            paper_ids = [seed.paper_id for seed in request.seeds]
        elif request.paper_ids:
            match_result = self.seed_selection_service.match_paper_ids(
                paper_ids=request.paper_ids,
                api_provider=request.api_provider,
            )
            paper_ids = [seed.paper_id for seed in match_result.matched_seeds]
        else:
            raise HTTPException(status_code=400, detail="Provide either 'seeds' or 'paper_ids' in the request body")

        deduped = list(dict.fromkeys(paper_ids))
        result = self.library_edit_service.add_seeds(details, deduped, api_provider=provider)
        return AddLibrarySeedsResponse(
            session_id=session_id,
            api_provider=result["api_provider"],
            requested=result["requested"],
            added_count=result["added_count"],
            skipped_existing=result.get("skipped_existing", []),
            failed=result.get("failed", []),
            added_ids=result.get("added_ids", []),
        )

    def add_session_seeds(
        self,
        session_id: str,
        request: ApplySessionSeedsRequest,
    ) -> ApplySessionSeedsResponse:
        details = self.library_service.get_details(session_id)
        session = self.seed_session_service.get_session(session_id)
        paper_ids = [seed.paper_id for seed in session.seeds]
        deduped = list(dict.fromkeys(paper_ids))
        result = self.library_edit_service.add_seeds(details, deduped, api_provider=request.api_provider)
        return ApplySessionSeedsResponse(
            session_id=session_id,
            api_provider=result["api_provider"],
            requested=result["requested"],
            added_count=result["added_count"],
            skipped_existing=result.get("skipped_existing", []),
            failed=result.get("failed", []),
            added_ids=result.get("added_ids", []),
        )
