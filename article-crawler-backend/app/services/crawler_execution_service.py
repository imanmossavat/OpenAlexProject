from __future__ import annotations

import logging
import uuid
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

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
    CrawlerProgressSnapshot,
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
        config_snapshot = self._create_config_snapshot(run_inputs)

        now = datetime.utcnow()
        job_data = {
            "job_id": job_id,
            "session_id": session_id,
            "status": "running",
            "current_iteration": 0,
            "max_iterations": run_inputs.max_iterations,
            "papers_collected": 0,
            "iterations_completed": 0,
            "iterations_remaining": run_inputs.max_iterations,
            "seed_papers": len(session_data.get("seeds") or []),
            "citations_collected": 0,
            "references_collected": 0,
            "papers_added_this_iteration": 0,
            "started_at": now,
            "completed_at": None,
            "last_progress_at": now,
            "error_message": None,
            "experiment_name": session_data.get("experiment_name"),
            "session_data": deepcopy(session_data),
            "config_snapshot": config_snapshot,
        }
        self._job_store.create_job(job_id, job_data)

        self._executor.submit(
            self._run_crawler,
            job_id,
            run_inputs,
            None,
        )

        return job_id

    def _run_crawler(
        self,
        job_id: str,
        run_inputs: CrawlerRunInputs,
        resume_payload: Optional[Dict] = None,
    ) -> None:
        try:
            run_kwargs = {
                "progress_callback": self._build_progress_handler(job_id),
            }
            if resume_payload is not None:
                run_kwargs["resume"] = resume_payload
            run_result = self._job_runner.run(
                job_id,
                run_inputs,
                **run_kwargs,
            )
            self._job_store.update_job(
                job_id,
                status="saving",
                last_progress_at=datetime.utcnow(),
            )
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

    def _build_progress_handler(self, job_id: str):
        def _handle(snapshot: CrawlerProgressSnapshot) -> None:
            try:
                updates = snapshot.as_job_updates()
                if updates.get("iterations_remaining", 0) == 0:
                    updates["status"] = "saving"
                self._job_store.update_job(job_id, **updates)
            except Exception:
                self.logger.warning(
                    "Job %s: Failed to persist progress update", job_id, exc_info=True
                )

        return _handle

    def _create_config_snapshot(self, run_inputs: CrawlerRunInputs) -> Dict[str, Any]:
        """Build a sanitized configuration payload for API consumers."""

        def _normalize_path(value: Optional[Any]) -> Optional[str]:
            if value is None:
                return None
            return str(value)

        def _safe_get(obj: Any, attr: str, default: Any = None) -> Any:
            return getattr(obj, attr, default)

        exp = run_inputs.experiment_config
        params = run_inputs.crawler_parameters
        snapshot: Dict[str, Any] = {
            "job_name": _safe_get(exp, "name"),
            "display_name": _safe_get(exp, "display_name"),
            "library": {
                "name": _safe_get(exp, "library_name"),
                "path": _normalize_path(_safe_get(exp, "library_path")),
            },
            "keywords": list(run_inputs.keywords or []),
            "seeds": list(_safe_get(exp, "seeds", []) or []),
            "crawler": {
                "max_iterations": _safe_get(exp, "max_iterations"),
                "papers_per_iteration": _safe_get(exp, "papers_per_iteration"),
            },
            "api": {
                "provider": _safe_get(exp, "api_provider"),
                "retries": _safe_get(exp, "api_retries"),
            },
            "sampling": {
                "no_keyword_lambda": _safe_get(exp, "no_keyword_lambda"),
                "hyperparams": dict(_safe_get(exp, "sampling_hyperparams", {}) or {}),
                "ignored_venues": list(_safe_get(exp, "ignored_venues", []) or []),
            },
            "text_processing": {
                "min_abstract_length": _safe_get(exp, "min_abstract_length"),
                "num_topics": _safe_get(exp, "num_topics"),
                "topic_model": _safe_get(exp, "topic_model"),
                "stemmer": _safe_get(exp, "stemmer"),
                "language": _safe_get(exp, "language"),
                "save_figures": _safe_get(exp, "save_figures"),
                "random_state": _safe_get(exp, "random_state"),
            },
            "graph": {
                "include_author_nodes": _safe_get(exp, "include_author_nodes"),
                "max_centrality_iterations": _safe_get(exp, "max_centrality_iterations"),
            },
            "retraction": {
                "enable_retraction_watch": _safe_get(exp, "enable_retraction_watch"),
                "avoid_retraction_in_sampler": _safe_get(exp, "avoid_retraction_in_sampler"),
                "avoid_retraction_in_reporting": _safe_get(exp, "avoid_retraction_in_reporting"),
            },
            "output": {
                "root_folder": _normalize_path(_safe_get(exp, "root_folder")),
                "log_level": _safe_get(exp, "log_level"),
                "open_vault_folder": _safe_get(exp, "open_vault_folder"),
            },
            "crawler_parameters": {
                "seed_paperid_file": _normalize_path(getattr(params, "seed_paperid_file", None)),
                "seed_count": len(getattr(params, "seed_paperid", []) or []),
            },
        }
        return snapshot

    def _record_success(
        self,
        job_id: str,
        run_inputs: CrawlerRunInputs,
        run_result: CrawlerRunResult,
    ) -> None:
        self._job_store.store_crawler(job_id, run_result.crawler)
        self._job_store.update_job(
            job_id,
            iterations_remaining=0,
            papers_collected=run_result.papers_collected,
            current_iteration=run_inputs.max_iterations,
            iterations_completed=run_inputs.max_iterations,
            status="completed",
            completed_at=datetime.utcnow(),
            last_progress_at=datetime.utcnow(),
        )

    def list_jobs(self) -> List[Dict]:
        jobs = self._job_store.list_jobs()
        return [self._sanitize_job_payload(job) for job in jobs]

    def get_job_status(self, job_id: str) -> Optional[Dict]:
        job = self._job_store.get_job(job_id)
        return self._sanitize_job_payload(job)

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

    def get_author_papers(
        self,
        job_id: str,
        author_id: str,
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

        return self._result_assembler.build_author_papers(
            crawler,
            author_id,
            page=page,
            page_size=page_size,
        )

    def resume_job(
        self,
        job_id: str,
        *,
        manual_frontier: Optional[List[str]] = None,
    ) -> str:
        """Resume a previously completed crawler job."""
        if not self.articlecrawler_path:
            raise ValueError("ArticleCrawler path not configured")

        job = self._job_store.get_job(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")
        if job.get("status") != "completed":
            raise ValueError("Only completed jobs can be resumed")

        session_data = job.get("session_data")
        if not session_data:
            raise ValueError("Original session data missing; cannot resume")

        session_data_copy = deepcopy(session_data)
        config_dict = dict(session_data_copy.get("configuration") or {})
        completed_iterations = max(int(job.get("iterations_completed") or 0), 0)
        current_max = max(int(config_dict.get("max_iterations") or 0), completed_iterations)
        manual_iterations_requested = 1 if manual_frontier else 0
        target_max = current_max + manual_iterations_requested
        if target_max <= completed_iterations:
            target_max = completed_iterations + 1
        config_dict["max_iterations"] = target_max
        session_data_copy["configuration"] = config_dict
        self._job_store.update_job(job_id, session_data=session_data_copy)

        run_inputs = self._config_builder.build(job_id, session_data_copy)
        config_snapshot = self._create_config_snapshot(run_inputs)
        now = datetime.utcnow()
        self._job_store.update_job(
            job_id,
            status="running",
            completed_at=None,
            error_message=None,
            last_progress_at=now,
            max_iterations=target_max,
            iterations_remaining=max(target_max - completed_iterations, 0),
            config_snapshot=config_snapshot,
        )

        resume_payload = {"manual_frontier": manual_frontier or None}
        self._executor.submit(
            self._run_crawler,
            job_id,
            run_inputs,
            resume_payload,
        )
        return job_id

    def _sanitize_job_payload(self, job: Optional[Dict]) -> Optional[Dict]:
        if not job:
            return None
        cleaned = dict(job)
        cleaned.pop("session_data", None)
        return cleaned

    def get_venue_papers(
        self,
        job_id: str,
        venue_id: str,
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

        return self._result_assembler.build_venue_papers(
            crawler,
            venue_id,
            page=page,
            page_size=page_size,
        )
