from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Optional

from ArticleCrawler.DataManagement.markdown_writer import MarkdownFileGenerator
from ArticleCrawler.crawler import Crawler
from ArticleCrawler.cli.utils.config_loader import save_config

from .config_builder import CrawlerRunInputs
from .progress import CrawlerProgressSnapshot


@dataclass(frozen=True)
class CrawlerRunResult:
    """Container for a completed crawler run."""

    crawler: Crawler
    papers_collected: int


class CrawlerJobRunner:
    """Execute ArticleCrawler jobs based on prepared configuration inputs."""

    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        self._logger = logger or logging.getLogger(__name__)

    def run(
        self,
        job_id: str,
        inputs: CrawlerRunInputs,
        *,
        progress_callback: Optional[Callable[[CrawlerProgressSnapshot], None]] = None,
    ) -> CrawlerRunResult:
        crawler_configs = inputs.experiment_config.to_crawler_configs()

        api_config = crawler_configs["api_config"]
        sampling_config = crawler_configs["sampling_config"]
        text_config = crawler_configs["text_config"]
        storage_config = crawler_configs["storage_config"]
        graph_config = crawler_configs["graph_config"]
        retraction_config = crawler_configs["retraction_config"]
        stopping_config = crawler_configs["stopping_config"]

        storage_config.root_folder.mkdir(parents=True, exist_ok=True)
        self._persist_configuration(
            job_id,
            storage_config.root_folder,
            inputs.experiment_config,
        )

        generator = MarkdownFileGenerator(
            storage_and_logging_options=storage_config,
            api_provider_type=api_config.provider_type,
        )

        self._logger.info("Job %s: Initializing crawler", job_id)
        crawler = Crawler(
            crawl_initial_condition=inputs.crawler_parameters,
            stopping_criteria_config=stopping_config,
            api_config=api_config,
            sampling_config=sampling_config,
            text_config=text_config,
            storage_config=storage_config,
            graph_config=graph_config,
            retraction_config=retraction_config,
            md_generator=generator,
            progress_callback=self._build_progress_emitter(
                progress_callback, stopping_config.max_iter
            ),
        )

        self._logger.info("Job %s: Starting crawl process", job_id)
        crawler.crawl()

        papers_collected = 0
        df_meta = getattr(crawler.data_coordinator.frames, "df_paper_metadata", None)
        if df_meta is not None:
            try:
                papers_collected = len(df_meta)
            except Exception:
                papers_collected = 0

        self._logger.info(
            "Job %s: Crawling completed, generating markdown files", job_id
        )
        crawler.generate_markdown_files()

        self._logger.info("Job %s: Running analysis and reporting", job_id)
        crawler.analyze_and_report(
            save_figures=text_config.save_figures,
            num_topics=text_config.num_topics,
        )

        return CrawlerRunResult(crawler=crawler, papers_collected=papers_collected)

    def _build_progress_emitter(
        self,
        callback: Optional[Callable[[CrawlerProgressSnapshot], None]],
        max_iterations: int,
    ) -> Optional[Callable[[Dict], None]]:
        if not callback:
            return None

        def _emit(raw_payload: Dict) -> None:
            try:
                payload = dict(raw_payload or {})
                payload.setdefault("iterations_total", max_iterations)
                snapshot = CrawlerProgressSnapshot.from_payload(payload)
                callback(snapshot)
            except Exception:
                self._logger.warning(
                    "Failed to normalize crawler progress payload", exc_info=True
                )

        return _emit

    def _persist_configuration(
        self,
        job_id: str,
        root_folder: Path,
        experiment_config,
    ) -> None:
        """Write the experiment configuration to disk for reproducibility."""
        try:
            config_path = root_folder / "config.yaml"
            save_config(experiment_config, config_path)
            self._logger.info(
                "Job %s: Saved experiment configuration to %s",
                job_id,
                config_path,
            )
        except Exception:
            self._logger.warning(
                "Job %s: Failed to save experiment configuration", job_id, exc_info=True
            )
