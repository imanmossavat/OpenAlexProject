from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Dict, Iterable, Optional

from app.schemas.settings import (
    ExperimentRootSettings,
    IntegrationSettingsResponse,
    LibraryRootSettings,
    OpenAlexSettings,
    UpdateExperimentRootRequest,
    UpdateLibraryRootRequest,
    UpdateOpenAlexSettingsRequest,
    UpdateZoteroSettingsRequest,
    ZoteroSettings,
)
from app.core.exceptions import InvalidInputException
from app.services.settings.helpers import (
    IntegrationSettingsRepository,
    IntegrationSettingsValidator,
)


class IntegrationSettingsService:
    """Manage external integration credentials stored in project .env files."""

    LIBRARY_ROOT_KEY = "ARTICLECRAWLER_LIBRARY_ROOT"
    EXPERIMENTS_ROOT_KEY = "ARTICLECRAWLER_EXPERIMENTS_ROOT"

    def __init__(
        self,
        logger: logging.Logger,
        repository: Optional[IntegrationSettingsRepository] = None,
        validator: Optional[IntegrationSettingsValidator] = None,
        primary_env_path: Optional[str | Path] = None,
        replica_env_paths: Optional[Iterable[str | Path]] = None,
    ):
        self.logger = logger
        self._repository = repository or IntegrationSettingsRepository(
            logger=logger,
            primary_env_path=primary_env_path,
            replica_env_paths=replica_env_paths,
        )
        self._validator = validator or IntegrationSettingsValidator()
        self.primary_env_path = self._repository.primary_env_path

    def get_settings(self) -> IntegrationSettingsResponse:
        """Return the current integration configuration state."""
        values = self._repository.load_values()
        return IntegrationSettingsResponse(
            openalex=self._build_openalex_settings(values),
            zotero=self._build_zotero_settings(values),
        )

    def update_openalex(self, payload: UpdateOpenAlexSettingsRequest) -> IntegrationSettingsResponse:
        """Persist the OpenAlex polite email."""
        email = self._validator.normalize_openalex(payload.email)
        self._repository.set_value("OPENALEX_EMAIL", email)
        self.logger.info("Updated OpenAlex contact email for polite API usage.")
        return self.get_settings()

    def update_zotero(self, payload: UpdateZoteroSettingsRequest) -> IntegrationSettingsResponse:
        """Persist Zotero credentials."""
        normalized = self._validator.normalize_zotero(
            payload.library_id,
            payload.library_type,
            payload.api_key,
        )

        self._repository.set_value("ZOTERO_LIBRARY_ID", normalized["library_id"])
        self._repository.set_value("ZOTERO_LIBRARY_TYPE", normalized["library_type"])
        api_key = normalized.get("api_key")
        if api_key:
            self._repository.set_value("ZOTERO_API_KEY", api_key)
        else:
            self._repository.remove_key("ZOTERO_API_KEY")

        self.logger.info("Updated Zotero credentials.")
        return self.get_settings()

    def get_library_root(self) -> LibraryRootSettings:
        """Return the currently configured library discovery root (if any)."""
        values = self._repository.load_values()
        raw_path = values.get(self.LIBRARY_ROOT_KEY) or os.environ.get(self.LIBRARY_ROOT_KEY)
        path = raw_path.strip() if isinstance(raw_path, str) else None
        return LibraryRootSettings(path=path or None)

    def update_library_root(self, payload: UpdateLibraryRootRequest) -> LibraryRootSettings:
        """Persist a new library discovery root or reset to defaults."""
        normalized = self._validator.normalize_library_root(payload.path)
        if normalized is None:
            self._repository.remove_key(self.LIBRARY_ROOT_KEY)
            self.logger.info("Cleared configured library discovery root. Using built-in defaults.")
            return self.get_library_root()

        normalized_str = str(normalized)
        self._repository.set_value(self.LIBRARY_ROOT_KEY, normalized_str)
        self.logger.info("Set library discovery root to %s", normalized_str)
        return self.get_library_root()

    def get_experiment_root(self) -> ExperimentRootSettings:
        """Return the currently configured experiment discovery root (if any)."""
        values = self._repository.load_values()
        raw_path = values.get(self.EXPERIMENTS_ROOT_KEY) or os.environ.get(self.EXPERIMENTS_ROOT_KEY)
        path = raw_path.strip() if isinstance(raw_path, str) else None
        return ExperimentRootSettings(path=path or None)

    def update_experiment_root(self, payload: UpdateExperimentRootRequest) -> ExperimentRootSettings:
        """Persist a new experiment discovery root or reset to defaults."""
        normalized = self._validator.normalize_library_root(payload.path)
        if normalized is None:
            self._repository.remove_key(self.EXPERIMENTS_ROOT_KEY)
            self.logger.info("Cleared configured experiment root. Using built-in defaults.")
            return self.get_experiment_root()

        normalized_str = str(normalized)
        self._repository.set_value(self.EXPERIMENTS_ROOT_KEY, normalized_str)
        self.logger.info("Set crawler experiment root to %s", normalized_str)
        return self.get_experiment_root()

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
