from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from app.core.exceptions import InvalidInputException
from app.core.storage.persistent_file_storage import PersistentFileStorage


class SourceFileRepository:
    """Thin wrapper around the persistent file storage backend."""

    def __init__(
        self,
        storage: Optional[PersistentFileStorage] = None,
        logger: Optional[logging.Logger] = None,
    ):
        self._storage = storage or PersistentFileStorage()
        self._logger = logger or logging.getLogger(__name__)

    def save(self, session_id: str, filename: str, source_path: Path) -> str:
        return self._storage.save_file(session_id, filename, source_path)

    def resolve(self, file_id: str) -> Path:
        return self._storage.resolve_path(file_id)

    def delete(self, file_id: str) -> None:
        self._storage.delete_file(file_id)

    def remove_session(self, session_id: str) -> bool:
        return self._storage.remove_session(session_id)

    def cleanup_expired(self, max_age_hours: int) -> int:
        return self._storage.cleanup_expired_sessions(max_age_hours)


class SourceFileValidator:
    """Validate inputs before persisting or retrieving stored files."""

    def normalize_session_id(self, session_id: str) -> str:
        cleaned = (session_id or "").strip()
        if not cleaned:
            raise InvalidInputException("Session id is required for file operations.")
        return cleaned

    def normalize_filename(self, filename: Optional[str], fallback: str) -> str:
        candidate = (filename or fallback).strip()
        if not candidate:
            raise InvalidInputException("A filename is required.")
        return candidate

    def ensure_source_path(self, path: Path) -> Path:
        if not path.exists() or not path.is_file():
            raise InvalidInputException("Source file does not exist.")
        return path
