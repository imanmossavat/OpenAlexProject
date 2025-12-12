from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.schemas.staging import StagingMatchRow, StagingPaperCreate, StagingPaperUpdate
from app.services.staging.query_service import StagingQueryService
from app.services.staging.query_utils import StagingQueryHelper
from app.services.staging.repository import StagingRepository
from app.services.staging.retraction_updater import StagingRetractionUpdater
from app.services.staging.row_manager import StagingRowManager
from app.services.staging.session_store import StagingSessionStore


def _base_session():
    return {"rows": [], "next_id": 1, "match_rows": []}


def test_staging_repository_persists_sessions():
    store = StagingSessionStore()
    repository = StagingRepository(store)

    session = repository.get_session("abc")
    assert session["rows"] == []
    assert session["next_id"] == 1

    session["rows"].append({"staging_id": 1, "title": "Paper"})
    session["next_id"] = 2
    repository.save_session("abc", session)

    stored = repository.get_session("abc")
    assert stored["next_id"] == 2
    assert len(stored["rows"]) == 1

    repository.delete_session("abc")
    reset = repository.get_session("abc")
    assert reset["rows"] == []
    assert reset["next_id"] == 1


def test_row_manager_adds_updates_and_removes_rows():
    manager = StagingRowManager(logger=logging.getLogger("test"))
    session = _base_session()

    created = manager.add_rows(
        session,
        [
            StagingPaperCreate(source="Manual", source_type="manual", title="Paper 1", doi="10.1/abc"),
            StagingPaperCreate(source="Manual", source_type="manual", title="Duplicate", doi="10.1/abc"),
        ],
    )
    assert len(created) == 1
    assert session["next_id"] == 2

    session["rows"][0]["is_retracted"] = True
    session["rows"][0]["retraction_reason"] = "Old"
    session["rows"][0]["retraction_checked_at"] = datetime.now(timezone.utc)

    updated = manager.update_row(
        session,
        1,
        StagingPaperUpdate(title="Updated Title", doi="10.1/xyz"),
    )
    assert updated.title == "Updated Title"
    assert session["rows"][0]["is_retracted"] is False
    assert session["rows"][0]["retraction_reason"] is None

    manager.add_rows(
        session,
        [
            StagingPaperCreate(source="Manual", source_type="manual", title="Paper 2", source_id="id-2"),
        ],
    )
    count = manager.set_selection(session, [1, 2], True)
    assert count == 2
    assert all(row["is_selected"] for row in session["rows"])

    removed = manager.remove_rows(session, [1])
    assert removed == 1
    assert len(session["rows"]) == 1

    manager.store_match_rows(
        session,
        [
            StagingMatchRow(
                staging_id=2,
                staging=created[0],
                matched=False,
                match_method=None,
            )
        ],
    )
    assert len(session["match_rows"]) == 1


def test_query_service_filters_and_paginates():
    query_service = StagingQueryService(StagingQueryHelper())
    rows = [
        {
            "staging_id": 1,
            "source": "Manual",
            "source_type": "manual",
            "title": "Alpha",
            "authors": "Doe",
            "year": 2020,
            "venue": "Conf",
            "doi": "10.1/abc",
            "url": None,
            "abstract": None,
            "is_retracted": False,
            "is_selected": True,
        },
        {
            "staging_id": 2,
            "source": "Manual",
            "source_type": "manual",
            "title": "Beta",
            "authors": "Smith",
            "year": 2021,
            "venue": "Conf",
            "doi": None,
            "url": None,
            "abstract": None,
            "is_retracted": False,
            "is_selected": False,
        },
    ]

    response = query_service.list_rows(
        "session-1",
        rows,
        page=1,
        page_size=1,
        sort_by="title",
        sort_dir="asc",
        source_values=None,
        year_min=None,
        year_max=None,
        title_search=None,
        venue_search=None,
        author_search=None,
        keyword_search=None,
        doi_presence=None,
        selected_only=True,
        retraction_status=None,
        title_values=None,
        author_values=None,
        venue_values=None,
        year_values=None,
        identifier_filters=None,
        custom_filters=None,
    )

    assert response.total_rows == 2
    assert response.filtered_rows == 1
    assert response.page_size == 1
    assert response.rows[0].title == "Alpha"


def test_retraction_updater_marks_retracted_rows():
    store = StagingSessionStore()
    repository = StagingRepository(store)
    manager = StagingRowManager(logger=logging.getLogger("test"))
    session = repository.get_session("session-retraction")

    manager.add_rows(
        session,
        [
            StagingPaperCreate(source="Manual", source_type="manual", title="Paper 1", doi="10.1/abc"),
            StagingPaperCreate(source="Manual", source_type="manual", title="Paper 2", doi=None),
        ],
    )
    repository.save_session("session-retraction", session)

    updater = StagingRetractionUpdater(
        repository=repository,
        query_helper=StagingQueryHelper(),
        logger=logging.getLogger("test"),
    )

    checked_at = datetime.now(timezone.utc)
    stats = updater.apply(
        "session-retraction",
        retracted_dois={"10.1/abc"},
        checked_at=checked_at,
        reason="Test",
        metadata={"10.1/abc": {"reason": "Duplicate", "date": "2020-01-01"}},
    )

    assert stats["eligible_rows"] == 1
    assert stats["retracted_rows"] == 1

    updated_session = repository.get_session("session-retraction")
    row = updated_session["rows"][0]
    assert row["is_retracted"] is True
    assert row["retraction_reason"] == "Duplicate"
    assert row["retraction_date"] == "2020-01-01"
    assert row["retraction_checked_at"] == checked_at

    second_row = updated_session["rows"][1]
    assert second_row["is_retracted"] is False
    assert second_row["retraction_reason"] is None
