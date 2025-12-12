from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, Iterable, Optional, Set

import pandas as pd

from ArticleCrawler.config.retraction_config import RetractionConfig
from ArticleCrawler.config.storage_config import StorageAndLoggingConfig
from ArticleCrawler.papervalidation.retraction_watch_manager import RetractionWatchManager


class RetractionDOINormalizer:
    """Normalize DOI values for consistent comparisons."""

    _PREFIXES = (
        "https://doi.org/",
        "http://doi.org/",
        "http://dx.doi.org/",
        "https://dx.doi.org/",
        "doi:",
    )

    def normalize(self, value: Optional[str]) -> Optional[str]:
        if not value:
            return None
        normalized = str(value).strip().lower()
        for prefix in self._PREFIXES:
            if normalized.startswith(prefix):
                normalized = normalized[len(prefix):]
        normalized = normalized.strip()
        return normalized or None

    def normalize_frame(self, frame: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
        if frame is None or not hasattr(frame, "copy"):
            return frame
        normalized = frame.copy()
        for column in columns:
            if column in normalized.columns:
                normalized[column] = normalized[column].apply(self.normalize)
        return normalized


class RetractionCacheRepository:
    """Manage access to the Retraction Watch cache via ArticleCrawler utilities."""

    def __init__(
        self,
        cache_dir: Optional[str],
        logger: logging.Logger,
        normalizer: Optional[RetractionDOINormalizer] = None,
    ) -> None:
        self._logger = logger
        self._cache_dir = Path(cache_dir or "retraction_cache").resolve()
        self._normalizer = normalizer or RetractionDOINormalizer()
        self._manager: Optional[RetractionWatchManager] = None

    def get_manager(self) -> RetractionWatchManager:
        if self._manager is None:
            self._cache_dir.mkdir(parents=True, exist_ok=True)
            storage_config = StorageAndLoggingConfig(
                experiment_file_name="retraction_watch_cache",
                root_folder=self._cache_dir,
            )
            retraction_config = RetractionConfig(enable_retraction_watch=True)
            manager = RetractionWatchManager(
                storage_and_logging_options=storage_config,
                retraction_options=retraction_config,
                logger=self._logger,
            )
            retraction_data = getattr(manager, "retraction_data", None)
            if retraction_data is not None:
                manager.retraction_data = self._normalizer.normalize_frame(
                    retraction_data,
                    columns=("RetractionDOI", "OriginalPaperDOI"),
                )
            self._manager = manager
        return self._manager


class RetractionMetadataBuilder:
    """Build DOI sets and metadata response payloads for retraction results."""

    def __init__(self, normalizer: RetractionDOINormalizer):
        self._normalizer = normalizer

    def extract_retracted_dois(self, retracted_df) -> Set[str]:
        if retracted_df is None or getattr(retracted_df, "empty", True):
            return set()
        values: Set[str] = set()
        try:
            for raw in retracted_df.get("doi", []):
                normalized = self._normalizer.normalize(str(raw))
                if normalized:
                    values.add(normalized)
        except Exception:
            return values
        return values

    def build_metadata_map(
        self,
        retracted_dois: Set[str],
        source_frame,
    ) -> Dict[str, Dict[str, Optional[str]]]:
        metadata: Dict[str, Dict[str, Optional[str]]] = {}
        if source_frame is None or not hasattr(source_frame, "iterrows") or not retracted_dois:
            return metadata

        try:
            doi_mask = False
            for column in ("RetractionDOI", "OriginalPaperDOI"):
                if column not in source_frame.columns:
                    continue
                doi_mask = doi_mask | source_frame[column].isin(retracted_dois)

            subset = source_frame[doi_mask] if doi_mask is not False else source_frame.iloc[0:0]
            for _, row in subset.iterrows():
                reason = row.get("Reason") or row.get("RetractionNature")
                date = row.get("RetractionDate")
                original = self._normalizer.normalize(row.get("OriginalPaperDOI"))
                retraction = self._normalizer.normalize(row.get("RetractionDOI"))
                payload = {"reason": reason, "date": date}

                if original and original not in metadata:
                    metadata[original] = payload
                if retraction and retraction not in metadata:
                    metadata[retraction] = payload
        except Exception:
            return metadata

        return metadata
