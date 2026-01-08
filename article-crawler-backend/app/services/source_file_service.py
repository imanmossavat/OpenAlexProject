from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from app.core.exceptions import InvalidInputException
from app.core.storage.persistent_file_storage import PersistentFileStorage
from app.services.source_files.helpers import SourceFileRepository, SourceFileValidator


class SourceFileService:
    """Manages persisted copies of uploaded files."""

    def __init__(
        self,
        logger: logging.Logger,
        storage: Optional[PersistentFileStorage] = None,
        repository: Optional[SourceFileRepository] = None,
        validator: Optional[SourceFileValidator] = None,
    ):
        self.logger = logger
        self._repository = repository or SourceFileRepository(storage=storage, logger=logger)
        self._validator = validator or SourceFileValidator()

    def persist_file(self, session_id: str, filename: str, source_path: Path) -> Optional[str]:
        """Copy a temp upload into persistent storage and return its file id."""
        try:
            normalized_session = self._validator.normalize_session_id(session_id)
            normalized_path = self._validator.ensure_source_path(source_path)
            normalized_name = self._validator.normalize_filename(filename, normalized_path.name)
            file_id = self._repository.save(normalized_session, normalized_name, normalized_path)
            self.logger.debug("Persisted source file %s for session %s", filename, session_id)
            return file_id
        except (InvalidInputException, Exception) as exc:
            self.logger.warning("Failed to persist file %s: %s", filename, exc)
            return None

    def get_file_path(self, file_id: str) -> Path:
        """Resolve a stored file id into a filesystem path."""
        return self._repository.resolve(file_id)

    def delete_file(self, file_id: str) -> None:
        """Remove a stored file."""
        self._repository.delete(file_id)

    def cleanup_session_files(self, session_id: str) -> bool:
        """Remove all persisted files for a session."""
        removed = self._repository.remove_session(session_id)
        if removed:
            self.logger.info("Removed persisted files for session %s", session_id)
        else:
            self.logger.debug("No persisted files to remove for session %s", session_id)
        return removed

    def cleanup_expired_sessions(self, max_age_hours: int) -> int:
        """Delete stale session folders based on last access time."""
        removed = self._repository.cleanup_expired(max_age_hours)
        if removed:
            self.logger.info("Cleaned up %d expired staged file session(s)", removed)
        else:
            self.logger.debug("No expired staged file sessions found for cleanup")
        return removed
