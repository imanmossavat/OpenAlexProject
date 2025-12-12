from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from ArticleCrawler.cli.models.experiment_config import ExperimentConfig
from ArticleCrawler.config.crawler_initialization import CrawlerParameters


@dataclass(frozen=True)
class CrawlerRunInputs:
    """Configuration payload produced by ``CrawlerConfigBuilder``."""

    experiment_config: ExperimentConfig
    crawler_parameters: CrawlerParameters
    keywords: List[str]
    max_iterations: int


class CrawlerConfigBuilder:
    """Translate user session data into concrete crawler configuration objects."""

    def __init__(
        self,
        articlecrawler_path: Optional[str],
        logger: Optional[logging.Logger] = None,
    ) -> None:
        if not articlecrawler_path:
            raise ValueError("articlecrawler_path must be configured")
        self._root = Path(articlecrawler_path)
        self._logger = logger or logging.getLogger(__name__)

    def build(self, job_id: str, session_data: Dict[str, Any]) -> CrawlerRunInputs:
        """Build crawler inputs for a job."""
        config_dict = dict(session_data.get("configuration") or {})
        keywords = list(session_data.get("keywords") or [])

        seeds = self._resolve_seeds(session_data, config_dict)
        if not seeds:
            raise ValueError("No valid seeds provided for crawler execution")

        root_folder = self._root / "experiments" / f"job_{job_id}"
        experiment_config = ExperimentConfig(
            name=f"crawler_{job_id}",
            seeds=seeds,
            keywords=keywords,
            max_iterations=config_dict.get("max_iterations", 1),
            papers_per_iteration=config_dict.get("papers_per_iteration", 1),
            api_provider=config_dict.get("api_provider", "openalex"),
            api_retries=config_dict.get("api_retries", 3),
            no_keyword_lambda=config_dict.get("no_keyword_lambda", 0.2),
            sampling_hyperparams=config_dict.get(
                "sampling_hyperparams", {"year": 0.3, "centrality": 1.0}
            ),
            ignored_venues=config_dict.get(
                "ignored_venues", ["", "ArXiv", "medRxiv", "WWW"]
            ),
            min_abstract_length=config_dict.get("min_abstract_length", 120),
            num_topics=config_dict.get("num_topics", 20),
            topic_model=config_dict.get("topic_model", "NMF"),
            stemmer=config_dict.get("stemmer", "Porter"),
            language=config_dict.get("language", "en"),
            save_figures=config_dict.get("save_figures", True),
            random_state=config_dict.get("random_state", 42),
            include_author_nodes=config_dict.get("include_author_nodes", False),
            max_centrality_iterations=config_dict.get(
                "max_centrality_iterations", 1000
            ),
            enable_retraction_watch=config_dict.get("enable_retraction_watch", True),
            avoid_retraction_in_sampler=config_dict.get(
                "avoid_retraction_in_sampler", False
            ),
            avoid_retraction_in_reporting=config_dict.get(
                "avoid_retraction_in_reporting", True
            ),
            root_folder=root_folder,
            log_level=config_dict.get("log_level", "INFO"),
            open_vault_folder=False,
            library_path=self._resolve_library_path(session_data),
            library_name=session_data.get("library_name"),
        )

        crawl_params = CrawlerParameters(seed_paperid=seeds, keywords=keywords)

        return CrawlerRunInputs(
            experiment_config=experiment_config,
            crawler_parameters=crawl_params,
            keywords=keywords,
            max_iterations=int(config_dict.get("max_iterations", 1) or 1),
        )

    def _resolve_library_path(self, session_data: Dict[str, Any]) -> Optional[Path]:
        raw = session_data.get("library_path")
        if not raw:
            return None
        path = Path(raw)
        return path if path.exists() else None

    def _resolve_seeds(
        self,
        session_data: Dict[str, Any],
        config_dict: Dict[str, Any],
    ) -> List[str]:
        library_path = self._resolve_library_path(session_data)
        if library_path:
            return self._seeds_from_library(library_path, config_dict)
        seeds_payload = session_data.get("seeds") or []
        seeds = [
            seed.get("paper_id")
            for seed in seeds_payload
            if isinstance(seed, dict) and seed.get("paper_id")
        ]
        return [seed for seed in seeds if isinstance(seed, str) and seed.strip()]

    def _seeds_from_library(
        self,
        library_path: Path,
        config_dict: Dict[str, Any],
    ) -> List[str]:
        from ArticleCrawler.library.library_manager import LibraryManager
        from ArticleCrawler.library.paper_file_reader import PaperFileReader

        lib_logger = self._logger
        manager = LibraryManager(lib_logger)
        reader = PaperFileReader(lib_logger)

        papers_dir = manager.get_papers_directory(library_path)
        paper_datas = reader.read_papers_from_directory(papers_dir)
        seeds = [
            paper.paper_id
            for paper in paper_datas
            if getattr(paper, "paper_id", None)
        ]
        if not seeds:
            raise ValueError(f"No papers found in library at {library_path}")

        try:
            lib_config = manager.load_library_config(library_path)
            if lib_config and not config_dict.get("api_provider"):
                config_dict["api_provider"] = (
                    getattr(lib_config, "api_provider", None)
                    or config_dict.get("api_provider")
                )
        except Exception:
            # Library configuration is optional. Errors should not interrupt the run.
            self._logger.debug("Unable to read library config for %s", library_path)

        return seeds
