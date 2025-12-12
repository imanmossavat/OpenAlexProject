from __future__ import annotations

import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from app.core.executors.background import BackgroundJobExecutor
from app.core.stores.crawler_job_store import (
    CrawlerJobStore,
    InMemoryCrawlerJobStore,
)
from app.services.crawler import (
    CrawlerConfigBuilder,
    CrawlerJobRunner,
    CrawlerResultAssembler,
    CrawlerRunInputs,
    CrawlerRunResult,
)


class CrawlerExecutionService:
    """Coordinate crawler jobs and expose their results to the API layer."""

    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        articlecrawler_path: Optional[str] = None,
        job_store: Optional[CrawlerJobStore] = None,
        job_executor: Optional[BackgroundJobExecutor] = None,
        config_builder: Optional[CrawlerConfigBuilder] = None,
        job_runner: Optional[CrawlerJobRunner] = None,
        result_assembler: Optional[CrawlerResultAssembler] = None,
    ):
        self.logger = logger or logging.getLogger(__name__)

        self._job_store = job_store or InMemoryCrawlerJobStore()
        self._executor = job_executor or BackgroundJobExecutor()

        self.articlecrawler_path: Optional[Path] = (
            Path(articlecrawler_path) if articlecrawler_path else None
        )

        builder_path = str(self.articlecrawler_path) if self.articlecrawler_path else None
        self._config_builder = config_builder or CrawlerConfigBuilder(
            articlecrawler_path=builder_path,
            logger=self.logger,
        )
        self._job_runner = job_runner or CrawlerJobRunner(logger=self.logger)
        self._result_assembler = result_assembler or CrawlerResultAssembler(
            logger=self.logger
        )

    def start_crawler(
        self,
        session_id: str,
        session_data: Dict,
    ) -> str:
        """Start a crawler job with configuration from session."""
        if not self.articlecrawler_path:
            raise ValueError("ArticleCrawler path not configured")

        job_id = f"job_{uuid.uuid4().hex[:12]}"
        self.logger.info("Starting crawler job %s for session %s", job_id, session_id)

        run_inputs = self._config_builder.build(job_id, session_data)

        job_data = {
            "job_id": job_id,
            "session_id": session_id,
            "status": "running",
            "current_iteration": 0,
            "max_iterations": run_inputs.max_iterations,
            "papers_collected": 0,
            "started_at": datetime.utcnow(),
            "completed_at": None,
            "error_message": None,
            "experiment_name": session_data.get("experiment_name"),
        }
        self._job_store.create_job(job_id, job_data)

        self._executor.submit(self._run_crawler, job_id, run_inputs)

        return job_id

    def _run_crawler(
        self,
        job_id: str,
        run_inputs: CrawlerRunInputs,
    ) -> None:
        try:
            run_result = self._job_runner.run(job_id, run_inputs)
            self._record_success(job_id, run_inputs, run_result)
            self.logger.info("Job %s: Completed successfully", job_id)
        except Exception as exc:
            logging.LoggerAdapter(self.logger, {"job_id": job_id}).error(
                "Job %s: Failed with error: %s", job_id, exc, exc_info=True
            )
            self._job_store.update_job(
                job_id,
                status="failed",
                error_message=str(exc),
                completed_at=datetime.utcnow(),
            )

    def _record_success(
        self,
        job_id: str,
        run_inputs: CrawlerRunInputs,
        run_result: CrawlerRunResult,
    ) -> None:
        self._job_store.store_crawler(job_id, run_result.crawler)
        self._job_store.update_job(
            job_id,
            current_iteration=run_inputs.max_iterations,
            papers_collected=run_result.papers_collected,
            status="completed",
            completed_at=datetime.utcnow(),
        )

    def get_job_status(self, job_id: str) -> Optional[Dict]:
        return self._job_store.get_job(job_id)

    def get_results(self, job_id: str) -> Optional[Dict]:
        job = self._job_store.get_job(job_id)
        if not job or job.get("status") != "completed":
            return None

        crawler = self._job_store.get_crawler(job_id)
        if not crawler:
            return None

        return self._result_assembler.assemble(job_id, crawler, job)

    def get_topic_papers(
        self,
        job_id: str,
        topic_id: int,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> Optional[Dict]:
        job = self._job_store.get_job(job_id)
        if not job or job.get("status") != "completed":
            return None

        crawler = self._job_store.get_crawler(job_id)
        if not crawler:
            return None

        return self._result_assembler.build_topic_papers(
            crawler,
            topic_id,
            page=page,
            page_size=page_size,
        )
