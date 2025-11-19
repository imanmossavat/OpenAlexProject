import logging
import os
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from dotenv import dotenv_values, set_key

from app.schemas.settings import (
    IntegrationSettingsResponse,
    OpenAlexSettings,
    UpdateOpenAlexSettingsRequest,
    UpdateZoteroSettingsRequest,
    ZoteroSettings,
)
from app.core.exceptions import InvalidInputException


class IntegrationSettingsService:
    """Manage external integration credentials stored in project .env files."""

    def __init__(
        self,
        logger: logging.Logger,
        primary_env_path: Optional[str] = None,
        replica_env_paths: Optional[Iterable[str]] = None,
    ):
        self.logger = logger

        project_root = Path(__file__).resolve().parents[2]
        default_primary = project_root / ".env"
        default_replica = project_root.parent / "fakenewscitationnetwork" / ".env"

        candidate_paths: List[Path] = [Path(primary_env_path) if primary_env_path else default_primary]
        if replica_env_paths:
            candidate_paths.extend(Path(path) for path in replica_env_paths)
        else:
            if default_replica != candidate_paths[0]:
                candidate_paths.append(default_replica)

        seen = set()
        self.env_paths: List[Path] = []
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

    def get_settings(self) -> IntegrationSettingsResponse:
        """Return the current integration configuration state."""
        values = self._load_env(self.primary_env_path)
        return IntegrationSettingsResponse(
            openalex=self._build_openalex_settings(values),
            zotero=self._build_zotero_settings(values),
        )

    def update_openalex(self, payload: UpdateOpenAlexSettingsRequest) -> IntegrationSettingsResponse:
        """Persist the OpenAlex polite email."""
        email = payload.email.strip()
        self._set_env_value("OPENALEX_EMAIL", email)
        self.logger.info("Updated OpenAlex contact email for polite API usage.")
        return self.get_settings()

    def update_zotero(self, payload: UpdateZoteroSettingsRequest) -> IntegrationSettingsResponse:
        """Persist Zotero credentials."""
        library_id = payload.library_id.strip()
        if not library_id:
            raise InvalidInputException("Zotero library id cannot be empty.")

        library_type = (payload.library_type or "user").strip().lower()
        if library_type not in {"user", "group"}:
            raise InvalidInputException("Zotero library type must be 'user' or 'group'.")

        self._set_env_value("ZOTERO_LIBRARY_ID", library_id)
        self._set_env_value("ZOTERO_LIBRARY_TYPE", library_type)

        if payload.api_key is not None:
            cleaned_key = payload.api_key.strip()
            if cleaned_key:
                self._set_env_value("ZOTERO_API_KEY", cleaned_key)
            else:
                self._remove_env_key("ZOTERO_API_KEY")

        self.logger.info("Updated Zotero credentials.")
        return self.get_settings()

    def _load_env(self, path: Path) -> Dict[str, str]:
        """Load environment values from the primary .env file."""
        try:
            return dotenv_values(path)
        except Exception as exc:
            self.logger.error(f"Failed to read environment file {path}: {exc}")
            raise InvalidInputException("Unable to read configuration file.")

    def _set_env_value(self, key: str, value: str) -> None:
        """Set (or overwrite) an environment key."""
        for path in self.env_paths:
            set_key(str(path), key, value, quote_mode="never")
        os.environ[key] = value

    def _remove_env_key(self, key: str) -> None:
        """Remove a key from the env file and current process."""
        for path in self.env_paths:
            if not path.exists():
                continue
            try:
                lines = path.read_text().splitlines()
            except Exception as exc:
                self.logger.error(f"Failed to read env file for removal: {exc}")
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
                    self.logger.error(f"Failed to write env file when removing key: {exc}")
                    raise InvalidInputException("Unable to update configuration file.")

        os.environ.pop(key, None)

    def _build_openalex_settings(self, values: Dict[str, str]) -> OpenAlexSettings:
        email = values.get("OPENALEX_EMAIL") or os.environ.get("OPENALEX_EMAIL")
        return OpenAlexSettings(configured=bool(email), email=email)

    def _build_zotero_settings(self, values: Dict[str, str]) -> ZoteroSettings:
        library_id = values.get("ZOTERO_LIBRARY_ID") or os.environ.get("ZOTERO_LIBRARY_ID")
        library_type = values.get("ZOTERO_LIBRARY_TYPE") or os.environ.get("ZOTERO_LIBRARY_TYPE") or "user"
        api_key = values.get("ZOTERO_API_KEY") or os.environ.get("ZOTERO_API_KEY")
        configured = bool(library_id and api_key)
        return ZoteroSettings(
            configured=configured,
            library_id=library_id,
            library_type=library_type,
            has_api_key=bool(api_key),
        )
