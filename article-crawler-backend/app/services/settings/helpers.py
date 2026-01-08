from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from dotenv import dotenv_values, set_key

from app.core.exceptions import InvalidInputException


class IntegrationSettingsRepository:
    """Read/write key-value pairs stored across one or more .env files."""

    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        primary_env_path: Optional[str | Path] = None,
        replica_env_paths: Optional[Iterable[str | Path]] = None,
    ):
        self._logger = logger or logging.getLogger(__name__)
        project_root = Path(__file__).resolve().parents[2]
        default_primary = project_root / ".env"
        default_replica = project_root.parent / "fakenewscitationnetwork" / ".env"

        candidate_paths: List[Path] = [Path(primary_env_path) if primary_env_path else default_primary]
        replicas = list(replica_env_paths or [])
        if replicas:
            candidate_paths.extend(Path(path) for path in replicas)
        elif default_replica not in candidate_paths:
            candidate_paths.append(default_replica)

        self.env_paths: List[Path] = []
        seen = set()
        for path in candidate_paths:
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            resolved.parent.mkdir(parents=True, exist_ok=True)
            resolved.touch(exist_ok=True)
            self.env_paths.append(resolved)

        if not self.env_paths:
            raise InvalidInputException("No configuration files available for integration settings.")

        self.primary_env_path = self.env_paths[0]

    def load_values(self) -> Dict[str, str]:
        try:
            return dotenv_values(self.primary_env_path)
        except Exception as exc:
            self._logger.error("Failed to read environment file %s: %s", self.primary_env_path, exc)
            raise InvalidInputException("Unable to read configuration file.")

    def set_value(self, key: str, value: str) -> None:
        for path in self.env_paths:
            set_key(str(path), key, value, quote_mode="never")
        os.environ[key] = value

    def remove_key(self, key: str) -> None:
        for path in self.env_paths:
            if not path.exists():
                continue
            try:
                lines = path.read_text().splitlines()
            except Exception as exc:
                self._logger.error("Failed to read env file for removal: %s", exc)
                raise InvalidInputException("Unable to update configuration file.")

            updated = []
            removed = False
            for line in lines:
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    updated.append(line)
                    continue
                key_part = line.split("=", 1)[0].strip()
                if key_part == key:
                    removed = True
                    continue
                updated.append(line)

            if removed:
                try:
                    content = "\n".join(updated)
                    if content and not content.endswith("\n"):
                        content += "\n"
                    path.write_text(content)
                except Exception as exc:
                    self._logger.error("Failed to write env file when removing key: %s", exc)
                    raise InvalidInputException("Unable to update configuration file.")
        os.environ.pop(key, None)


class IntegrationSettingsValidator:
    """Normalize and validate incoming integration settings payloads."""

    def normalize_openalex(self, email: Optional[str]) -> str:
        return (email or "").strip()

    def normalize_zotero(
        self,
        library_id: str,
        library_type: Optional[str],
        api_key: Optional[str],
    ) -> Dict[str, Optional[str]]:
        cleaned_id = (library_id or "").strip()
        if not cleaned_id:
            raise InvalidInputException("Zotero library id cannot be empty.")
        cleaned_type = (library_type or "user").strip().lower()
        if cleaned_type not in {"user", "group"}:
            raise InvalidInputException("Zotero library type must be 'user' or 'group'.")
        cleaned_key = api_key.strip() if isinstance(api_key, str) else None
        return {"library_id": cleaned_id, "library_type": cleaned_type, "api_key": cleaned_key}

    def normalize_library_root(self, path_value: Optional[str]) -> Optional[Path]:
        raw_value = path_value.strip() if isinstance(path_value, str) else ""
        if not raw_value:
            return None
        path = Path(raw_value).expanduser()
        if not path.is_absolute():
            raise InvalidInputException("Library discovery path must be an absolute path.")
        if not path.exists() or not path.is_dir():
            raise InvalidInputException("Library discovery path must be an existing directory.")
        return path.resolve()
