from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import polars as pl


class PaperCatalogRepository:
    """Provides read-only access to crawler output catalogs stored as Parquet."""

    def __init__(self, articlecrawler_path: str, logger: Optional[logging.Logger] = None):
        if not articlecrawler_path:
            raise ValueError("articlecrawler_path must be configured")
        self._root = Path(articlecrawler_path)
        self._logger = logger or logging.getLogger(__name__)

    def scan_catalog(self, job_id: str) -> pl.LazyFrame:
        """Return a LazyFrame pointing to the Parquet catalog for the given job."""
        catalog_path = self._catalog_path(job_id)
        if not catalog_path.exists():
            raise FileNotFoundError(
                f"Catalog not found for job {job_id}: expected {catalog_path}"
            )
        self._logger.debug("Scanning catalog parquet at %s", catalog_path)
        return pl.scan_parquet(str(catalog_path))

    def catalog_exists(self, job_id: str) -> bool:
        """Quick existence check (used for status validation before querying)."""
        return self._catalog_path(job_id).exists()

    def _catalog_path(self, job_id: str) -> Path:
        """Resolve the Parquet path for a crawler job."""
        experiments_root = self._root / "experiments"
        job_dir = _job_directory(experiments_root, job_id)
        crawler_dir = job_dir / f"crawler_{job_id}"
        return crawler_dir / "vault" / "parquet" / "papers.parquet"


def _job_directory(experiments_root: Path, job_id: str) -> Path:
    """
    ArticleCrawler stores each run in experiments/job_{job_id}/crawler_{job_id}.

    job_id already contains the `job_` prefix, but the folder name repeats it
    (e.g. job_id="job_abcd" -> experiments/job_job_abcd/...). This helper keeps
    the naming logic in one location and tolerates already-prefixed values.
    """
    if job_id.startswith("job_job_"):
        job_folder_name = job_id
    else:
        job_folder_name = f"job_{job_id}"
    return experiments_root / job_folder_name
