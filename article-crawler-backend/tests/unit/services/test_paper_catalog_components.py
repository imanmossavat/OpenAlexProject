from __future__ import annotations

import logging
from typing import Dict, List, Optional

import polars as pl

from app.services.catalog import (
    CatalogLazyFrameBuilder,
    CatalogQuery,
    ColumnOptionsBuilder,
)
from app.services.catalog.query_builder import CatalogFrame
from app.services.catalog.service import PaperCatalogService


class StubCatalogRepository:
    def __init__(self, frame: pl.DataFrame):
        self._frame = frame.lazy()
        self.calls: List[str] = []

    def scan_catalog(self, job_id: str):
        self.calls.append(job_id)
        return self._frame


class StubAnnotationRepository:
    def __init__(self, marks: Optional[Dict[str, str]] = None):
        self._marks = marks or {}
        self.calls: List[str] = []

    def load_marks(self, job_id: str):
        self.calls.append(job_id)
        return self._marks

    def save_mark(self, job_id: str, paper_id: str, mark: str):
        self._marks[paper_id] = mark


def test_catalog_lazy_frame_builder_filters_search_and_marks():
    df = pl.DataFrame(
        {
            "paperId": ["W1", "W2"],
            "title": ["Graph Mining Advances", "Other Topic"],
            "doi": ["10.123/abc", ""],
            "year": [2021, 2019],
            "nmf_topic": [3, 7],
            "isSeed": [True, False],
        }
    )
    catalog_repo = StubCatalogRepository(df)
    annotation_repo = StubAnnotationRepository({"W1": "good", "W2": "bad"})

    builder = CatalogLazyFrameBuilder(
        catalog_repo,
        annotation_repo,
        mark_column="__mark",
        allowed_marks=["standard", "good", "neutral", "bad"],
        identifier_fields=["doi"],
    )

    query = CatalogQuery(
        search="graph",
        doi_filter="with",
        mark_filters=["good"],
    )
    frame = builder.build("job-123", query)
    filtered = frame.lazy_frame.collect()

    assert catalog_repo.calls == ["job-123"]
    assert annotation_repo.calls == ["job-123"]
    assert filtered.height == 1
    assert filtered["paperId"][0] == "W1"
    assert filtered["__mark"][0] == "good"
    assert frame.mark_lookup["W1"] == "good"


def test_column_options_builder_includes_selected_values_and_search():
    df = pl.DataFrame(
        {
            "title": ["Alpha", "Beta", "Alpha"],
            "venue": ["ConfA", "ConfB", "ConfA"],
            "year": [2020, 2021, 2020],
            "authors_display": [["Alice", "Bob"], ["Cara"], ["Alice"]],
            "doi": ["10.1", "10.2", "10.1"],
        }
    )
    frame = CatalogFrame(
        lazy_frame=df.lazy(),
        schema=df.lazy().schema,
        mark_lookup={},
    )
    builder = ColumnOptionsBuilder(
        columns=["title", "authors", "venue", "year", "identifier"],
        max_filter_options=10,
    )

    selected = {"title": ["Gamma"]}
    options = builder.build_all(frame, selected)

    gamma_option = next(
        (opt for opt in options["title"] if opt.label == "Gamma"),
        None,
    )
    assert gamma_option is not None
    assert gamma_option.count == 0

    page = builder.list_column_options(
        frame,
        "authors",
        page=1,
        page_size=5,
        option_query="ali",
        selected_filters={"authors": []},
    )
    assert page.total == 1
    assert page.options[0].label == "Alice"


def test_paper_catalog_service_uses_builders_for_listing():
    df = pl.DataFrame(
        {
            "paperId": ["W1", "W2"],
            "title": ["Item One", "Item Two"],
            "authors_display": [["Ann"], ["Ben", "Cara"]],
            "year": [2020, 2022],
            "centrality_in": [0.5, 0.1],
            "centrality_out": [0.7, 0.2],
        }
    )
    frame = CatalogFrame(
        lazy_frame=df.lazy(),
        schema=df.lazy().schema,
        mark_lookup={"W1": "good"},
    )

    class StubQueryBuilder:
        def __init__(self, frame):
            self.frame = frame
            self.requests: List[CatalogQuery] = []

        def build(self, job_id: str, query: CatalogQuery):
            self.requests.append(query)
            return self.frame

        def selected_filter_map(self, query: CatalogQuery):
            return {"title": ["Item One"]}

    class StubColumnOptionsBuilder:
        def __init__(self):
            self.calls: List[Dict[str, List[str]]] = []

        def build_all(self, frame: CatalogFrame, selected_filters):
            self.calls.append(selected_filters)
            return {"title": []}

        def list_column_options(self, *args, **kwargs):
            raise AssertionError("list_column_options should not be called in this test")

    class StubExporter:
        def export(self, job_id: str) -> bytes:
            return b"{}"

    service = PaperCatalogService(
        catalog_repository=StubCatalogRepository(df),
        annotation_repository=StubAnnotationRepository(),
        logger=logging.getLogger("test"),
        query_builder=StubQueryBuilder(frame),
        column_options_builder=StubColumnOptionsBuilder(),
        catalog_exporter=StubExporter(),
    )

    result = service.list_papers(
        "job-1",
        page=1,
        page_size=5,
        query="item",
        sort_by="year",
        descending=False,
    )

    assert result.total == 2
    assert result.papers[0].paper_id == "W1"
    assert result.papers[0].mark == "good"
    assert result.column_options == {"title": []}
