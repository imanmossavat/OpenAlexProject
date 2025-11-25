from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
import shutil
import uuid
from typing import Optional


class PersistentFileStorage:
    """Stores uploaded files in a stable location so they can be served later."""

    METADATA_FILENAME = ".session_metadata.json"

    def __init__(self, base_dir: Optional[str | Path] = None, logger: Optional[logging.Logger] = None):
        base = Path(base_dir) if base_dir else Path.cwd() / "uploaded_files"
        self._base_dir = base.resolve()
        self._base_dir.mkdir(parents=True, exist_ok=True)
        self._logger = logger or logging.getLogger(__name__)

    @property
    def base_dir(self) -> Path:
        return self._base_dir

    def save_file(self, session_id: str, filename: str, source_path: Path) -> str:
        """Copy an uploaded file into the persistent storage directory.

        Returns an opaque identifier that can be used to fetch the file later.
        """
        safe_filename = Path(filename or source_path.name).name or "uploaded_file"
        token = f"{uuid.uuid4().hex}_{safe_filename}"
        session_dir = self._base_dir / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        self._ensure_metadata(session_dir)
        destination = session_dir / token
        shutil.copy2(source_path, destination)
        self._touch_last_accessed(session_dir)
        return destination.relative_to(self._base_dir).as_posix()

    def resolve_path(self, file_id: str) -> Path:
        """Return the absolute path for a previously stored file id."""
        candidate = (self._base_dir / file_id).resolve()
        try:
            candidate.relative_to(self._base_dir)
        except ValueError:
            raise FileNotFoundError(file_id)
        if not candidate.is_file():
            raise FileNotFoundError(file_id)
        self._touch_last_accessed(candidate.parent)
        return candidate

    def delete_file(self, file_id: str) -> None:
        """Remove a stored file, ignoring missing files."""
        try:
            path = self.resolve_path(file_id)
        except FileNotFoundError:
            return
        path.unlink(missing_ok=True)
        self._cleanup_empty_parents(path.parent)

    def remove_session(self, session_id: str) -> bool:
        """Remove an entire session directory."""
        session_dir = (self._base_dir / session_id).resolve()
        try:
            session_dir.relative_to(self._base_dir)
        except ValueError:
            return False
        if not session_dir.exists():
            return False
        try:
            shutil.rmtree(session_dir)
            return True
        except Exception as exc:
            self._logger.warning("Failed to remove session directory %s: %s", session_dir, exc)
            return False

    def cleanup_expired_sessions(self, max_age_hours: int) -> int:
        """Delete session directories that have not been accessed within the TTL."""
        now = datetime.now(timezone.utc)
        removed = 0
        for session_dir in self._base_dir.iterdir():
            if not session_dir.is_dir():
                continue
            last_seen = self._last_activity(session_dir)
            if last_seen is None:
                continue
            age_hours = (now - last_seen).total_seconds() / 3600
            if age_hours >= max_age_hours:
                try:
                    shutil.rmtree(session_dir)
                    removed += 1
                except Exception as exc:
                    self._logger.warning("Failed to cleanup session directory %s: %s", session_dir, exc)
        return removed

    def _cleanup_empty_parents(self, start_dir: Path) -> None:
        """Remove empty session directories after deleting files."""
        current = start_dir
        while current != self._base_dir:
            try:
                remaining = [p for p in current.iterdir() if p.name != self.METADATA_FILENAME]
            except OSError:
                break
            if remaining:
                break
            meta_path = current / self.METADATA_FILENAME
            try:
                meta_path.unlink(missing_ok=True)
            except OSError:
                pass
            try:
                current.rmdir()
            except OSError:
                break
            current = current.parent

    def _ensure_metadata(self, session_dir: Path) -> None:
        """Create metadata file if missing."""
        meta_path = session_dir / self.METADATA_FILENAME
        if meta_path.exists():
            return
        now = datetime.now(timezone.utc)
        metadata = {
            "created_at": now.isoformat(),
            "last_accessed": now.isoformat(),
        }
        try:
            meta_path.write_text(json.dumps(metadata, ensure_ascii=True))
        except Exception as exc:
            self._logger.warning("Unable to write metadata for %s: %s", session_dir, exc)

    def _touch_last_accessed(self, session_dir: Path) -> None:
        """Update the last accessed timestamp for a session directory."""
        meta_path = session_dir / self.METADATA_FILENAME
        now = datetime.now(timezone.utc).isoformat()
        metadata = {}
        if meta_path.exists():
            try:
                metadata = json.loads(meta_path.read_text())
            except Exception:
                metadata = {}
        metadata.setdefault("created_at", now)
        metadata["last_accessed"] = now
        try:
            meta_path.write_text(json.dumps(metadata, ensure_ascii=True))
        except Exception as exc:
            self._logger.warning("Unable to update metadata for %s: %s", session_dir, exc)

    def _last_activity(self, session_dir: Path) -> Optional[datetime]:
        """Return the last activity timestamp for a session directory."""
        meta_path = session_dir / self.METADATA_FILENAME
        if meta_path.exists():
            try:
                metadata = json.loads(meta_path.read_text())
                ts = metadata.get("last_accessed") or metadata.get("created_at")
                if ts:
                    return self._parse_timestamp(ts)
            except Exception:
                pass
        try:
            stat = session_dir.stat()
            return datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
        except OSError:
            return None

    def _parse_timestamp(self, value: str) -> Optional[datetime]:
        """Parse an ISO formatted timestamp string into a datetime."""
        try:
            dt = datetime.fromisoformat(value)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception:
            return None
