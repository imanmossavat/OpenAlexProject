from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, Optional

from .paper_catalog_repository import _job_directory


class PaperAnnotationRepository:
    """Handles persistence of user annotations (marks) per crawler job."""

    def __init__(self, articlecrawler_path: str, logger: Optional[logging.Logger] = None):
        if not articlecrawler_path:
            raise ValueError("articlecrawler_path must be configured")
        self._root = Path(articlecrawler_path)
        self._logger = logger or logging.getLogger(__name__)

    def load_marks(self, job_id: str) -> Dict[str, str]:
        """Load the mark dictionary for the given job."""
        path = self._annotations_path(job_id)
        if not path.exists():
            self._logger.debug("No annotations store found for job %s at %s", job_id, path)
            return {}
        try:
            with open(path, "r", encoding="utf-8") as handle:
                data = json.load(handle) or {}
                return {str(k): str(v) for k, v in data.items()}
        except Exception as exc:
            self._logger.error("Failed to load annotations for %s: %s", job_id, exc)
            raise

    def save_mark(self, job_id: str, paper_id: str, mark: str) -> Dict[str, str]:
        """
        Persist a mark update for a paper. Returns the updated mapping.

        Passing mark="standard" removes the explicit entry (falling back to default).
        """
        annotations_dir = self._annotations_dir(job_id)
        annotations_dir.mkdir(parents=True, exist_ok=True)
        path = annotations_dir / "paper_marks.json"
        marks = self.load_marks(job_id)
        if mark == "standard":
            marks.pop(paper_id, None)
        else:
            marks[paper_id] = mark
        try:
            with open(path, "w", encoding="utf-8") as handle:
                json.dump(marks, handle, ensure_ascii=False, indent=2)
        except Exception as exc:
            self._logger.error("Failed to save annotation for %s in %s: %s", paper_id, job_id, exc)
            raise
        return marks

    def _annotations_path(self, job_id: str) -> Path:
        return self._annotations_dir(job_id) / "paper_marks.json"

    def _annotations_dir(self, job_id: str) -> Path:
        experiments_root = self._root / "experiments"
        job_dir = _job_directory(experiments_root, job_id)
        crawler_dir = job_dir / f"crawler_{job_id}"
        return crawler_dir / "vault" / "annotations"
