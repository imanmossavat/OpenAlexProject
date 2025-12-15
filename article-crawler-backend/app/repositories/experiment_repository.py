from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from ArticleCrawler.cli.models.experiment_config import ExperimentConfig
from ArticleCrawler.cli.utils.config_loader import load_config


@dataclass(frozen=True)
class StoredExperiment:
    """Metadata for a persisted crawler experiment."""

    job_id: str
    config: ExperimentConfig
    config_path: Path
    updated_at: datetime


class ExperimentConfigRepository:
    """Discover and load saved experiment configurations from disk."""

    def __init__(self, articlecrawler_path: str, logger: Optional[logging.Logger] = None) -> None:
        if not articlecrawler_path:
            raise ValueError("articlecrawler_path must be configured")
        self._default_root = Path(articlecrawler_path) / "experiments"
        self._logger = logger or logging.getLogger(__name__)

    def list_experiments(self, base_path: Optional[str] = None) -> List[StoredExperiment]:
        root = self._resolve_root(base_path)
        records: List[StoredExperiment] = []
        if not root.exists():
            return records
        for job_dir in sorted(root.iterdir()):
            if not job_dir.is_dir():
                continue
            job_id = self._extract_job_id(job_dir.name)
            config_path = job_dir / "config.yaml"
            if not config_path.exists():
                continue
            try:
                config = load_config(config_path)
                updated_at = datetime.fromtimestamp(config_path.stat().st_mtime)
                records.append(
                    StoredExperiment(
                        job_id=job_id,
                        config=config,
                        config_path=config_path,
                        updated_at=updated_at,
                    )
                )
            except Exception as exc:
                self._logger.warning("Skipping experiment at %s due to load error: %s", config_path, exc)
                continue
        return records

    def get_experiment(self, job_id: str, base_path: Optional[str] = None) -> StoredExperiment:
        config_path = self._config_path(job_id, base_path=base_path)
        if not config_path.exists():
            raise FileNotFoundError(f"Experiment config not found for job {job_id}: {config_path}")
        config = load_config(config_path)
        updated_at = datetime.fromtimestamp(config_path.stat().st_mtime)
        return StoredExperiment(job_id=job_id, config=config, config_path=config_path, updated_at=updated_at)

    def load_from_path(self, experiment_path: str) -> StoredExperiment:
        candidate = Path(experiment_path)
        config_path = candidate / "config.yaml" if candidate.is_dir() else candidate
        if not config_path.exists():
            raise FileNotFoundError(f"No config.yaml found at {config_path}")
        config = load_config(config_path)
        updated_at = datetime.fromtimestamp(config_path.stat().st_mtime)
        job_id = self._extract_job_id(config_path.parent.name)
        return StoredExperiment(job_id=job_id, config=config, config_path=config_path, updated_at=updated_at)

    def _config_path(self, job_id: str, base_path: Optional[str]) -> Path:
        root = self._resolve_root(base_path)
        job_dir = root / self._folder_name(job_id)
        return job_dir / "config.yaml"

    def _resolve_root(self, override_path: Optional[str]) -> Path:
        if override_path:
            try:
                return Path(override_path)
            except Exception:
                self._logger.warning("Invalid experiments root override: %s", override_path)
        return self._default_root

    def _extract_job_id(self, folder_name: str) -> str:
        return folder_name[4:] if folder_name.startswith("job_") else folder_name

    def _folder_name(self, job_id: str) -> str:
        if job_id.startswith("job_job_"):
            return job_id
        if job_id.startswith("job_"):
            return f"job_{job_id}"
        return job_id
