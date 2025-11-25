from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from app.core.storage.persistent_file_storage import PersistentFileStorage


class SourceFileService:
    """Manages persisted copies of uploaded files."""

    def __init__(
        self,
        logger: logging.Logger,
        storage: Optional[PersistentFileStorage] = None,
    ):
        self.logger = logger
        self._storage = storage or PersistentFileStorage()

    def persist_file(self, session_id: str, filename: str, source_path: Path) -> Optional[str]:
        """Copy a temp upload into persistent storage and return its file id."""
        try:
            file_id = self._storage.save_file(session_id, filename, source_path)
            self.logger.debug("Persisted source file %s for session %s", filename, session_id)
            return file_id
        except Exception as exc:
            self.logger.warning("Failed to persist file %s: %s", filename, exc)
            return None

    def get_file_path(self, file_id: str) -> Path:
        """Resolve a stored file id into a filesystem path."""
        return self._storage.resolve_path(file_id)

    def delete_file(self, file_id: str) -> None:
        """Remove a stored file."""
        self._storage.delete_file(file_id)

    def cleanup_session_files(self, session_id: str) -> bool:
        """Remove all persisted files for a session."""
        removed = self._storage.remove_session(session_id)
        if removed:
            self.logger.info("Removed persisted files for session %s", session_id)
        else:
            self.logger.debug("No persisted files to remove for session %s", session_id)
        return removed

    def cleanup_expired_sessions(self, max_age_hours: int) -> int:
        """Delete stale session folders based on last access time."""
        removed = self._storage.cleanup_expired_sessions(max_age_hours)
        if removed:
            self.logger.info("Cleaned up %d expired staged file session(s)", removed)
        else:
            self.logger.debug("No expired staged file sessions found for cleanup")
        return removed
