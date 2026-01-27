from __future__ import annotations

import json
import logging
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import warnings

warnings.filterwarnings(
    "ignore",
    category=FutureWarning,
    message="Downcasting behavior in `replace` is deprecated",
)


@dataclass
class ResumeState:
    """Structured state restored from a checkpoint."""

    iteration: int
    total_papers: int
    frames: Dict[str, pd.DataFrame]
    manual_frontier: Optional[List[str]] = None
    sampler_flags: Dict[str, object] = field(default_factory=dict)


class CheckpointManager:
    """
    Handle checkpoint persistence for ArticleCrawler runs.

    Responsibilities:
        - Serialize crawler frames and metadata after each iteration
        - Promote completed checkpoints to a canonical "final" snapshot
        - Restore frames/state when resuming a crawl
    """

    _FRAME_ARTIFACTS = {
        "df_paper_metadata": "papers_full.parquet",
        "df_paper_citations": "paper_citations.parquet",
        "df_paper_references": "paper_references.parquet",
        "df_paper_author": "paper_author.parquet",
        "df_author": "authors.parquet",
        "df_citations": "citations.parquet",
        "df_abstract": "abstracts.parquet",
        "df_derived_features": "derived_features.parquet",
        "df_venue_features": "venue_features.parquet",
        "df_forbidden_entries": "forbidden_entries.parquet",
    }

    _CONTROL_STATE_FILE = "control_state.json"
    _SAMPLER_STATE_FILE = "sampler_state.json"
    _META_FILE = "resume_meta.json"
    _MANUAL_FRONTIER_FILE = "manual_frontier.json"
    _SCHEMA_VERSION = "1.0"

    def __init__(self, storage_config, logger: Optional[logging.Logger] = None) -> None:
        self._storage_config = storage_config
        self._logger = logger or logging.getLogger(__name__)
        self._root = self._storage_config.experiment_folder / "checkpoints"
        self._latest_path = self._root / "checkpoint_latest"
        self._final_path = self._root / "checkpoint_final"
        self._tmp_path = self._root / "checkpoint_tmp"
        self._ensure_root()

    def _ensure_root(self) -> None:
        try:
            self._root.mkdir(parents=True, exist_ok=True)
        except Exception:
            self._logger.warning("Unable to create checkpoint root at %s", self._root, exc_info=True)

    def save(self, crawler, iteration_idx: int, total_papers: Optional[int] = None) -> None:
        """
        Persist the crawler state after an iteration completes.

        Args:
            crawler: Active crawler instance
            iteration_idx: Iteration count that has just completed
            total_papers: Optional explicit paper count
        """
        if not self._root.exists():
            # Storage config might not allow writing; skip silently.
            return

        total = total_papers
        if total is None:
            total = getattr(crawler.data_coordinator.frames, "df_paper_metadata", pd.DataFrame()).shape[0]

        try:
            if self._tmp_path.exists():
                shutil.rmtree(self._tmp_path)
            self._tmp_path.mkdir(parents=True, exist_ok=True)

            self._write_frames(crawler, self._tmp_path)
            control_state = {
                "iteration": int(iteration_idx),
                "total_papers": int(total),
                "max_iterations": int(getattr(crawler.stopping_config, "max_iter", 0)),
                "timestamp": datetime.utcnow().isoformat(),
            }
            self._write_json(control_state, self._tmp_path / self._CONTROL_STATE_FILE)

            sampler_state = {
                "no_papers_available": bool(getattr(crawler.sampler, "no_papers_available", False)),
                "data_retrieval_empty": bool(getattr(crawler.data_coordinator, "no_papers_retrieved", False)),
            }
            self._write_json(sampler_state, self._tmp_path / self._SAMPLER_STATE_FILE)

            resume_meta = {
                "schema_version": self._SCHEMA_VERSION,
                "created_at": datetime.utcnow().isoformat(),
                "iteration": int(iteration_idx),
            }
            self._write_json(resume_meta, self._tmp_path / self._META_FILE)

            self._replace_directory(self._tmp_path, self._latest_path)
        except Exception:
            self._logger.error("Failed to save checkpoint at iteration %s", iteration_idx, exc_info=True)

    def promote_final(self) -> None:
        """Persist the latest checkpoint as the canonical final snapshot."""
        if not self._latest_path.exists():
            return
        try:
            if self._final_path.exists():
                shutil.rmtree(self._final_path)
            shutil.copytree(self._latest_path, self._final_path)
        except Exception:
            self._logger.error("Unable to promote checkpoint to final state", exc_info=True)

    def load(self, manual_frontier: Optional[List[str]] = None) -> Optional[ResumeState]:
        """Load a checkpoint from disk."""
        source = self._resolve_checkpoint_source()
        if not source:
            return None

        try:
            frames = self._read_frames(source)
            control_state = self._read_json(source / self._CONTROL_STATE_FILE, default={})
            sampler_state = self._read_json(source / self._SAMPLER_STATE_FILE, default={})
            stored_manual_frontier = self._read_json(
                source / self._MANUAL_FRONTIER_FILE, default=None
            ) or []

            cleaned_manual_frontier = self._clean_manual_frontier(
                manual_frontier or stored_manual_frontier,
                frames.get("df_paper_metadata"),
            )

            return ResumeState(
                iteration=int(control_state.get("iteration", 0)),
                total_papers=int(control_state.get("total_papers", 0)),
                frames=frames,
                manual_frontier=cleaned_manual_frontier,
                sampler_flags=sampler_state,
            )
        except Exception:
            self._logger.error("Failed to load checkpoint from %s", source, exc_info=True)
            return None

    def persist_manual_frontier(self, paper_ids: List[str]) -> None:
        """Persist an incoming manual frontier selection for future resumes."""
        if not self._latest_path.exists():
            return
        try:
            payload = list(dict.fromkeys([pid for pid in paper_ids if isinstance(pid, str) and pid.strip()]))
            self._write_json(payload, self._latest_path / self._MANUAL_FRONTIER_FILE)
        except Exception:
            self._logger.warning("Unable to persist manual frontier selection", exc_info=True)

    def _write_frames(self, crawler, target_dir: Path) -> None:
        frames = crawler.data_coordinator.frames
        for attr, filename in self._FRAME_ARTIFACTS.items():
            dataframe = getattr(frames, attr, None)
            path = target_dir / filename
            if dataframe is None:
                if path.exists():
                    path.unlink()
                continue
            normalized = self._normalize_frame(attr, dataframe)
            normalized.to_parquet(path, index=False)

    def _read_frames(self, source: Path) -> Dict[str, pd.DataFrame]:
        frames: Dict[str, pd.DataFrame] = {}
        for attr, filename in self._FRAME_ARTIFACTS.items():
            path = source / filename
            if path.exists():
                frames[attr] = pd.read_parquet(path)
            else:
                frames[attr] = pd.DataFrame()
        return frames
    def _normalize_frame(self, name: str, dataframe: pd.DataFrame) -> pd.DataFrame:
        if dataframe is None:
            return pd.DataFrame()
        df = dataframe.copy()
        bool_columns = {
            "df_paper_metadata": ["processed", "isSeed", "isKeyAuthor", "selected", "retracted"],
            "df_forbidden_entries": ["sampler", "textProcessing"],
        }
        for column in bool_columns.get(name, []):
            if column in df.columns:
                column_series = (
                    df[column]
                    .astype(object)
                    .replace({"": False, None: False})
                    .fillna(False)
                    .astype(bool, copy=False)
                )
                df[column] = column_series
        return df

    def _write_json(self, payload, path: Path) -> None:
        with open(path, "w", encoding="utf-8") as fp:
            json.dump(payload, fp, indent=2)

    def _read_json(self, path: Path, default=None):
        if not path.exists():
            return default
        try:
            with open(path, "r", encoding="utf-8") as fp:
                return json.load(fp)
        except Exception:
            self._logger.warning("Unable to read JSON from %s", path, exc_info=True)
            return default

    def _replace_directory(self, source: Path, target: Path) -> None:
        if target.exists():
            shutil.rmtree(target)
        shutil.move(str(source), str(target))

    def _resolve_checkpoint_source(self) -> Optional[Path]:
        if self._final_path.exists():
            return self._final_path
        if self._latest_path.exists():
            return self._latest_path
        return None

    def _clean_manual_frontier(
        self, candidates: Optional[List[str]], df_meta: Optional[pd.DataFrame]
    ) -> Optional[List[str]]:
        if not candidates:
            return None
        unique_ids = []
        seen = set()
        valid_ids = set(df_meta["paperId"].tolist()) if df_meta is not None and "paperId" in df_meta.columns else None
        for candidate in candidates:
            if not isinstance(candidate, str):
                continue
            normalized = candidate.strip()
            if not normalized or normalized in seen:
                continue
            if valid_ids is not None and normalized not in valid_ids:
                continue
            seen.add(normalized)
            unique_ids.append(normalized)
        return unique_ids or None
