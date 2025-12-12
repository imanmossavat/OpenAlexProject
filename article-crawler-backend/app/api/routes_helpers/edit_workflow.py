from fastapi import HTTPException

from app.schemas.library import (
    LibraryEditSelectionResponse,
    LibraryEditCommitRequest,
    LibraryEditCommitResponse,
)
from app.schemas.seed_session import SessionSeedsResponse


class LibraryEditWorkflowRouteHelper:
    """Orchestrate edit workflow endpoints."""

    def __init__(
        self,
        library_service,
        seed_session_service,
        workflow_service,
    ):
        self.library_service = library_service
        self.seed_session_service = seed_session_service
        self.workflow_service = workflow_service

    def stage_library(self, session_id: str) -> LibraryEditSelectionResponse:
        selection = self.workflow_service.stage_library(session_id)
        details = self.library_service.get_details(session_id)
        if not details:
            raise HTTPException(status_code=400, detail="Library details missing for session")
        return LibraryEditSelectionResponse(
            session_id=session_id,
            name=details.get("name") or "",
            path=details.get("path") or "",
            staged_count=selection.total_staged,
            seed_count=selection.total_seeds,
        )

    def summarize(self, session_id: str) -> SessionSeedsResponse:
        return self.seed_session_service.get_session(session_id)

    def commit(self, session_id: str, request: LibraryEditCommitRequest) -> LibraryEditCommitResponse:
        seed_response = self.seed_session_service.get_session(session_id)
        total_selected = seed_response.total_seeds
        current_seed_ids = [
            seed.paper_id for seed in (seed_response.seeds or []) if getattr(seed, "paper_id", None)
        ]
        if request.mode == "duplicate":
            if not request.duplicate_path:
                raise HTTPException(status_code=400, detail="duplicate_path required when mode=duplicate")
            result = self.workflow_service.duplicate_library(
                session_id,
                seed_response,
                target_path=request.duplicate_path,
                name=request.duplicate_name,
                description=request.duplicate_description,
            )
            return LibraryEditCommitResponse(
                session_id=session_id,
                mode="duplicate",
                total_selected=total_selected,
                library_path=result["base_path"],
                added_ids=current_seed_ids,
                removed_ids=[],
                duplicate_library_path=result["base_path"],
                duplicate_library_name=result["name"],
            )

        diff = self.workflow_service.commit_update(session_id, seed_response)
        return LibraryEditCommitResponse(
            session_id=session_id,
            mode="update",
            total_selected=total_selected,
            library_path=diff.library_path,
            added_ids=diff.added_ids,
            removed_ids=diff.removed_ids,
        )
