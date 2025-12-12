from __future__ import annotations

import logging
from types import SimpleNamespace
from unittest.mock import Mock

from app.core.stores.crawler_job_store import InMemoryCrawlerJobStore
from app.services.crawler import (
    CrawlerConfigBuilder,
    CrawlerJobRunner,
    CrawlerResultAssembler,
    CrawlerRunInputs,
    CrawlerRunResult,
)
from app.services.crawler_execution_service import CrawlerExecutionService


class ImmediateExecutor:
    """Executor that runs submitted jobs synchronously (for tests)."""

    def submit(self, func, *args, **kwargs):
        func(*args, **kwargs)


class DummyConfig:
    pass


class DummyCrawler:
    pass


def test_start_crawler_runs_job_and_updates_store(monkeypatch):
    store = InMemoryCrawlerJobStore()
    executor = ImmediateExecutor()

    config_inputs = CrawlerRunInputs(
        experiment_config=DummyConfig(),
        crawler_parameters=DummyConfig(),
        keywords=["ai"],
        max_iterations=2,
    )

    builder = Mock(spec=CrawlerConfigBuilder)
    builder.build.return_value = config_inputs

    run_result = CrawlerRunResult(crawler=DummyCrawler(), papers_collected=5)
    runner = Mock(spec=CrawlerJobRunner)
    runner.run.return_value = run_result

    assembler = Mock(spec=CrawlerResultAssembler)

    dummy_uuid = SimpleNamespace(hex="1234567890abcdef1234567890abcdef")
    monkeypatch.setattr(
        "app.services.crawler_execution_service.uuid.uuid4", lambda: dummy_uuid
    )

    service = CrawlerExecutionService(
        logger=logging.getLogger("test"),
        articlecrawler_path="/tmp",
        job_store=store,
        job_executor=executor,
        config_builder=builder,
        job_runner=runner,
        result_assembler=assembler,
    )

    session_data = {"configuration": {"max_iterations": 2}}
    job_id = service.start_crawler("session-1", session_data)

    assert job_id == "job_1234567890ab"
    builder.build.assert_called_once_with(job_id, session_data)
    runner.run.assert_called_once_with(job_id, config_inputs)

    stored = store.get_job(job_id)
    assert stored["status"] == "completed"
    assert stored["papers_collected"] == 5
    assert stored["current_iteration"] == 2


def test_get_results_uses_result_assembler(monkeypatch):
    store = InMemoryCrawlerJobStore()
    job_id = "job_test"
    store.create_job(
        job_id,
        {
            "job_id": job_id,
            "status": "completed",
            "current_iteration": 1,
        },
    )
    crawler_obj = DummyCrawler()
    store.store_crawler(job_id, crawler_obj)

    builder = Mock()
    runner = Mock()
    assembler = Mock()
    assembler.assemble.return_value = {"job_id": job_id}

    service = CrawlerExecutionService(
        logger=logging.getLogger("test"),
        articlecrawler_path="/tmp",
        job_store=store,
        job_executor=ImmediateExecutor(),
        config_builder=builder,
        job_runner=runner,
        result_assembler=assembler,
    )

    payload = service.get_results(job_id)

    assembler.assemble.assert_called_once_with(job_id, crawler_obj, store.get_job(job_id))
    assert payload == {"job_id": job_id}
