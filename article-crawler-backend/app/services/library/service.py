import logging
from typing import Dict, Optional

from app.core.exceptions import InvalidInputException
from app.services.library.helpers import (
    LibraryDetailsStore,
    LibraryPathResolver,
    LibraryWorkflowRunner,
)


class LibraryService:
    """Coordinate library creation using injected helpers."""

    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        details_store: Optional[LibraryDetailsStore] = None,
        path_resolver: Optional[LibraryPathResolver] = None,
        workflow_runner: Optional[LibraryWorkflowRunner] = None,
    ):
        self.logger = logger or logging.getLogger(__name__)
        self._details_store = details_store or LibraryDetailsStore()
        self._path_resolver = path_resolver or LibraryPathResolver("")
        self._workflow_runner = workflow_runner or LibraryWorkflowRunner(logger=self.logger)

    def set_details(
        self,
        session_id: str,
        name: str,
        path: Optional[str],
        description: Optional[str],
    ) -> Dict[str, Optional[str]]:
        resolved_path = self._path_resolver.resolve(path)
        normalized_name = name.strip()
        normalized_description = description.strip() if description else None
        record = self._details_store.update(
            session_id,
            name=normalized_name,
            path=str(resolved_path),
            description=normalized_description,
        )
        self.logger.info(
            "Set library details for session %s: name='%s', path='%s'",
            session_id,
            normalized_name,
            resolved_path,
        )
        return record

    def get_details(self, session_id: str) -> Dict[str, Optional[str]]:
        return self._details_store.get(session_id)

    def preview(self, session_id: str, session_service) -> Dict[str, Optional[str]]:
        details = self.get_details(session_id)
        if not details.get("name") or not details.get("path"):
            raise InvalidInputException("Library details not set. Please set name and path first.")

        session = session_service.get_session(session_id)
        total = len(session.seeds) if session and session.seeds else 0

        return {
            "name": details["name"],
            "path": details["path"],
            "description": details.get("description"),
            "total_papers": total,
        }

    def create(self, session_id: str, session_service) -> Dict[str, Optional[str]]:
        details = self.get_details(session_id)
        if not details.get("name") or not details.get("path"):
            raise InvalidInputException("Library details not set. Please set name and path first.")

        session = session_service.get_session(session_id)
        if not session or not session.seeds:
            raise InvalidInputException("No seeds selected. Please add seeds before creating a library.")

        paper_ids = [s.paper_id for s in session.seeds]
        result = self._workflow_runner.create_library(
            name=str(details["name"]),
            base_path=str(details["path"]),
            paper_ids=paper_ids,
            description=details.get("description"),
        )

        return {
            "name": result["name"],
            "base_path": result["base_path"],
            "total_requested": result["total_requested"],
            "saved_count": result["saved_count"],
            "papers": result.get("papers", []),
        }
