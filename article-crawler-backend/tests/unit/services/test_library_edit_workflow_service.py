import logging
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from app.schemas.seed_session import SessionSeedsResponse
from app.schemas.seeds import MatchedSeed
from app.services.library.edit_workflow_service import (
    LibraryEditWorkflowService,
    LibraryEditState,
    LibraryEditStateStore,
)
from app.services.library.helpers import LibraryPathResolver, LibraryWorkflowRunner


@pytest.fixture
def workflow_service():
    logger = logging.getLogger("test")
    library_service = MagicMock()
    library_service.get_details.return_value = {
        "name": "Test Library",
        "path": "/tmp/test-library",
        "description": "Desc",
    }

    library_edit_service = MagicMock()
    library_edit_service.list_papers.return_value = [
        {
            "paper_id": "W1",
            "title": "Paper 1",
            "authors": ["Author A"],
            "year": 2020,
            "venue": "Conf",
        },
        {
            "paper_id": "W2",
            "title": "Paper 2",
            "authors": ["Author B"],
            "year": 2021,
            "venue": "Journal",
        },
    ]

    seed_session_service = MagicMock()
    staging_service = MagicMock()
    staging_service.add_rows.return_value = [object(), object()]

    workflow_runner = MagicMock(spec=LibraryWorkflowRunner)

    resolver = LibraryPathResolver("/tmp")
    state_store = LibraryEditStateStore()

    service = LibraryEditWorkflowService(
        logger=logger,
        library_service=library_service,
        library_edit_service=library_edit_service,
        seed_session_service=seed_session_service,
        staging_service=staging_service,
        workflow_runner=workflow_runner,
        path_resolver=resolver,
        state_store=state_store,
    )

    return {
        "service": service,
        "library_service": library_service,
        "library_edit_service": library_edit_service,
        "seed_session_service": seed_session_service,
        "staging_service": staging_service,
        "workflow_runner": workflow_runner,
        "state_store": state_store,
    }


def build_seed_response(session_id: str, paper_ids):
    seeds = [MatchedSeed(paper_id=pid) for pid in paper_ids]
    now = datetime.now(timezone.utc)
    return SessionSeedsResponse(
        session_id=session_id,
        use_case="library_creation",
        seeds=seeds,
        total_seeds=len(seeds),
        created_at=now,
        updated_at=now,
    )


def test_stage_library_populates_staging_and_seeds(workflow_service):
    service = workflow_service["service"]
    staging_service = workflow_service["staging_service"]
    seed_session_service = workflow_service["seed_session_service"]

    summary = service.stage_library("session-1")

    assert summary.total_seeds == 2
    assert summary.total_staged == 2
    staging_service.clear_session.assert_called_once_with("session-1")
    staging_service.add_rows.assert_called_once()
    seed_session_service.set_seeds_for_session.assert_called_once()


def test_commit_update_computes_diff_and_calls_edit_services(workflow_service):
    service = workflow_service["service"]
    state_store = workflow_service["state_store"]
    library_edit_service = workflow_service["library_edit_service"]

    state_store.save(
        "session-2",
        LibraryEditState(
            library_path="/tmp/test-library",
            api_provider="openalex",
            original_paper_ids={"W1", "W2"},
        ),
    )

    seed_response = build_seed_response("session-2", ["W1", "W3"])

    diff = service.commit_update("session-2", seed_response)

    assert diff.added_ids == ["W3"]
    assert diff.removed_ids == ["W2"]
    library_edit_service.add_seeds.assert_called_once()
    library_edit_service.remove_seeds.assert_called_once()


def test_duplicate_library_uses_runner_with_resolved_defaults(workflow_service):
    service = workflow_service["service"]
    workflow_runner = workflow_service["workflow_runner"]
    workflow_runner.create_library.return_value = {
        "name": "Test Library (Copy)",
        "base_path": "/tmp/libraries/Test Library (Copy)",
        "total_requested": 1,
        "saved_count": 1,
    }
    seed_response = build_seed_response("session-3", ["W1"])

    result = service.duplicate_library(
        "session-3",
        seed_response,
        target_path="/tmp/libraries",
        name=None,
        description=None,
    )

    workflow_runner.create_library.assert_called_once()
    assert result["name"].endswith("(Copy)")
