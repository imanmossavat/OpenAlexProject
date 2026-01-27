from __future__ import annotations

import ast
import logging
import math
from typing import Any, Dict, List, Optional, Tuple

import polars as pl

from ArticleCrawler.utils.url_builder import PaperURLBuilder

from app.repositories import PaperCatalogRepository, PaperAnnotationRepository
from app.schemas.papers import (
    ColumnOptionsPage,
    PaginatedPaperSummaries,
    PaperSummary,
    PaperMarkResponse,
)
from app.schemas.staging import ColumnCustomFilter
from app.services.catalog import (
    CatalogLazyFrameBuilder,
    CatalogQuery,
    ColumnOptionsBuilder,
    PaperCatalogExporter,
)


class PaperCatalogService:
    """Application service that exposes catalog browsing and annotations."""

    DEFAULT_SORT_CANDIDATES = [
        "centrality (out)",
        "centrality_out",
        "centrality (in)",
        "centrality_in",
        "year",
    ]
    ALLOWED_MARKS = {"standard", "good", "neutral", "bad"}
    MAX_FILTER_OPTIONS = 150
    IDENTIFIER_FIELDS = {"doi", "url"}
    COLUMN_OPTION_COLUMNS = {"title", "authors", "venue", "year", "identifier"}
    MARK_COLUMN = "__annotation_mark"

    def __init__(
        self,
        catalog_repository: PaperCatalogRepository,
        annotation_repository: PaperAnnotationRepository,
        logger: Optional[logging.Logger] = None,
        query_builder: Optional[CatalogLazyFrameBuilder] = None,
        column_options_builder: Optional[ColumnOptionsBuilder] = None,
        catalog_exporter: Optional[PaperCatalogExporter] = None,
    ):
        self._catalog_repo = catalog_repository
        self._annotation_repo = annotation_repository
        self._logger = logger or logging.getLogger(__name__)
        self._url_builder = PaperURLBuilder()
        self._query_builder = query_builder or CatalogLazyFrameBuilder(
            catalog_repository,
            annotation_repository,
            mark_column=self.MARK_COLUMN,
            allowed_marks=list(self.ALLOWED_MARKS),
            identifier_fields=list(self.IDENTIFIER_FIELDS),
        )
        self._column_options_builder = column_options_builder or ColumnOptionsBuilder(
            columns=list(self.COLUMN_OPTION_COLUMNS),
            max_filter_options=self.MAX_FILTER_OPTIONS,
        )
        self._catalog_exporter = catalog_exporter or PaperCatalogExporter(
            catalog_repository,
            annotation_repository,
            mark_column=self.MARK_COLUMN,
        )

    def list_papers(
        self,
        job_id: str,
        page: int = 1,
        page_size: int = 50,
        query: Optional[str] = None,
        sort_by: Optional[str] = None,
        descending: bool = True,
        venue: Optional[str] = None,
        doi: Optional[str] = None,
        doi_filter: Optional[str] = None,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        topic: Optional[int] = None,
        topic_ids: Optional[List[int]] = None,
        topic_model: Optional[str] = None,
        seed_filter: Optional[str] = None,
        retraction_filter: Optional[str] = None,
        seed_only: bool = False,
        retracted_only: bool = False,
        mark_filters: Optional[List[str]] = None,
        title_values: Optional[List[str]] = None,
        author_values: Optional[List[str]] = None,
        venue_values: Optional[List[str]] = None,
        year_values: Optional[List[int]] = None,
        identifier_filters: Optional[List[Dict[str, str]]] = None,
        custom_filters: Optional[List[ColumnCustomFilter]] = None,
    ) -> PaginatedPaperSummaries:
        if page_size > 200:
            raise ValueError("page_size cannot exceed 200")
        if page < 1:
            raise ValueError("page must be at least 1")
        catalog_query = CatalogQuery(
            search=query or "",
            venue=venue,
            doi=doi,
            doi_filter=doi_filter,
            year_from=year_from,
            year_to=year_to,
            topic=topic,
            topic_ids=topic_ids,
            topic_model=topic_model,
            seed_filter=seed_filter,
            retraction_filter=retraction_filter,
            seed_only=seed_only,
            retracted_only=retracted_only,
            mark_filters=mark_filters,
            title_values=title_values,
            author_values=author_values,
            venue_values=venue_values,
            year_values=year_values,
            identifier_filters=identifier_filters,
            custom_filters=custom_filters,
            sort_by=sort_by,
            descending=descending,
        )
        frame = self._query_builder.build(job_id, catalog_query)
        selected_for_options = self._query_builder.selected_filter_map(catalog_query)
        column_options = self._column_options_builder.build_all(
            frame, selected_for_options
        )

        lf, schema, mark_lookup = (
            frame.lazy_frame,
            frame.schema,
            frame.mark_lookup,
        )

        sort_column = self._pick_sort_column(schema, sort_by)
        if sort_column:
            lf = lf.sort(sort_column, descending=descending)

        total = lf.select(pl.len()).collect().item()
        offset = (page - 1) * page_size
        lf_page = lf.slice(offset, page_size)
        records = lf_page.collect().to_dicts()

        summaries = [
            self._convert_row_to_summary(row, mark_lookup.get(row.get("paperId")))
            for row in records
        ]

        return PaginatedPaperSummaries(
            page=page,
            page_size=page_size,
            total=total,
            papers=summaries,
            column_options=column_options,
        )

    def get_paper_summaries(self, job_id: str, paper_ids: List[str]) -> List[PaperSummary]:
        """Return catalog summaries for a subset of paper IDs, preserving input order."""
        if not paper_ids:
            return []
        normalized_ids = []
        seen = set()
        for pid in paper_ids:
            if not pid:
                continue
            trimmed = str(pid).strip()
            if not trimmed or trimmed in seen:
                continue
            seen.add(trimmed)
            normalized_ids.append(trimmed)
        if not normalized_ids:
            return []

        lf = self._catalog_repo.scan_catalog(job_id)
        if "paperId" not in lf.schema:
            raise ValueError("Catalog does not contain paper identifiers")
        frame = (
            lf.filter(pl.col("paperId").is_in(normalized_ids))
            .collect()
            .to_dicts()
        )
        marks = self._annotation_repo.load_marks(job_id) or {}
        lookup = {
            str(row.get("paperId") or row.get("paper_id") or ""): self._convert_row_to_summary(
                row,
                marks.get(str(row.get("paperId") or row.get("paper_id") or "")),
            )
            for row in frame
        }
        ordered: List[PaperSummary] = []
        for pid in normalized_ids:
            summary = lookup.get(pid)
            if summary:
                ordered.append(summary)
        return ordered

    def list_column_options(
        self,
        job_id: str,
        column: str,
        *,
        page: int = 1,
        page_size: int = 100,
        option_query: Optional[str] = None,
        query: Optional[str] = None,
        venue: Optional[str] = None,
        doi: Optional[str] = None,
        doi_filter: Optional[str] = None,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        topic: Optional[int] = None,
        topic_ids: Optional[List[int]] = None,
        topic_model: Optional[str] = None,
        seed_filter: Optional[str] = None,
        retraction_filter: Optional[str] = None,
        seed_only: bool = False,
        retracted_only: bool = False,
        mark_filters: Optional[List[str]] = None,
        title_values: Optional[List[str]] = None,
        author_values: Optional[List[str]] = None,
        venue_values: Optional[List[str]] = None,
        year_values: Optional[List[int]] = None,
        identifier_filters: Optional[List[Dict[str, str]]] = None,
        custom_filters: Optional[List[ColumnCustomFilter]] = None,
    ) -> ColumnOptionsPage:
        normalized_column = (column or "").strip().lower()
        if normalized_column not in self.COLUMN_OPTION_COLUMNS:
            raise ValueError(f"Unsupported column '{column}' for options")
        if page_size > 500:
            raise ValueError("page_size cannot exceed 500 for column options")
        if page < 1:
            raise ValueError("page must be at least 1")

        catalog_query = CatalogQuery(
            search=query or "",
            venue=venue,
            doi=doi,
            doi_filter=doi_filter,
            year_from=year_from,
            year_to=year_to,
            topic=topic,
            topic_ids=topic_ids,
            topic_model=topic_model,
            seed_filter=seed_filter,
            retraction_filter=retraction_filter,
            seed_only=seed_only,
            retracted_only=retracted_only,
            mark_filters=mark_filters,
            title_values=title_values,
            author_values=author_values,
            venue_values=venue_values,
            year_values=year_values,
            identifier_filters=identifier_filters,
            custom_filters=custom_filters,
        )
        frame = self._query_builder.build(job_id, catalog_query)
        selected_filters = self._query_builder.selected_filter_map(catalog_query)

        return self._column_options_builder.list_column_options(
            frame,
            normalized_column,
            page=page,
            page_size=page_size,
            option_query=option_query,
            selected_filters=selected_filters,
        )

    def update_mark(self, job_id: str, paper_id: str, mark: str) -> PaperMarkResponse:
        mark = mark.lower().strip()
        if mark not in self.ALLOWED_MARKS:
            raise ValueError(f"Unsupported mark '{mark}'")

        # Ensure the paper exists before writing
        lf = self._catalog_repo.scan_catalog(job_id)
        if "paperId" not in lf.schema:
            raise ValueError("Catalog does not contain paper identifiers")
        exists = (
            lf.filter(pl.col("paperId") == paper_id)
            .select(pl.len())
            .collect()
            .item()
        )
        if exists == 0:
            raise ValueError(f"Paper {paper_id} not found in job {job_id}")

        self._annotation_repo.save_mark(job_id, paper_id, mark)
        return PaperMarkResponse(paper_id=paper_id, mark=mark)

    def _pick_sort_column(self, schema: Dict[str, pl.datatypes.DataType], explicit: Optional[str]) -> Optional[str]:
        if explicit and explicit in schema:
            return explicit
        for candidate in self.DEFAULT_SORT_CANDIDATES:
            if candidate in schema:
                return candidate
        return None

    def _convert_row_to_summary(self, row: Dict, mark: Optional[str]) -> PaperSummary:
        paper_id = str(row.get("paperId") or row.get("paper_id") or "")
        title = row.get("title") or paper_id
        authors_source = (
            row.get("authors")
            or row.get("authors_display")
            or row.get("author_names")
        )
        authors = self._normalize_authors(authors_source)
        venue = row.get("venue")
        year = self._safe_int(row.get("year"))
        doi = self._safe_str(row.get("doi"))
        api_provider = (
            self._safe_str(
                row.get("api_provider")
                or row.get("provider")
                or row.get("source_provider")
            )
            or "openalex"
        )
        url = self._safe_str(row.get("url")) or (
            self._url_builder.build_url(paper_id, api_provider) if paper_id else None
        )

        citation_count = self._extract_int(
            row,
            ["citation_count", "cited_by_count", "citedByCount", "numCitations"],
        )
        centrality_in = self._extract_float(
            row, ["centrality (in)", "centrality_in", "centrality_in_degree"]
        )
        centrality_out = self._extract_float(
            row, ["centrality (out)", "centrality_out", "centrality_out_degree"]
        )
        is_seed = self._coerce_bool(
            row.get("isSeed") or row.get("seed") or row.get("is_seed")
        )
        is_retracted = self._coerce_bool(
            row.get("isRetracted") or row.get("retracted") or row.get("is_retracted")
        )
        selected_flag = self._coerce_bool(
            row.get("selected") or row.get("is_selected")
        )
        topics = self._extract_topics(row)
        nmf_topic = self._extract_topic_value(row, "nmf_topic")
        lda_topic = self._extract_topic_value(row, "lda_topic")

        return PaperSummary(
            paper_id=paper_id,
            title=title,
            authors=authors,
            venue=venue,
            year=year,
            doi=doi,
            url=url,
            citation_count=citation_count,
            centrality_in=centrality_in,
            centrality_out=centrality_out,
            is_seed=is_seed,
            is_retracted=is_retracted,
            selected=selected_flag,
            mark=mark or "standard",
            topics=topics,
            nmf_topic=nmf_topic,
            lda_topic=lda_topic,
        )

    def _normalize_authors(self, value) -> List[str]:
        if value is None:
            return []
        if isinstance(value, list):
            if value and isinstance(value[0], dict):
                return [item.get("name") or item.get("display_name") for item in value if isinstance(item, dict)]
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return []
            if stripped.startswith("[") and stripped.endswith("]"):
                try:
                    parsed = ast.literal_eval(stripped)
                    return self._normalize_authors(parsed)
                except Exception:
                    pass
            if ";" in stripped:
                return [part.strip() for part in stripped.split(";") if part.strip()]
            return [stripped]
        return [str(value)]

    def _extract_topics(self, row: Dict) -> List[str]:
        topics: List[str] = []
        for key, value in row.items():
            key_lower = str(key).lower()
            if key_lower.endswith("_topic"):
                if isinstance(value, (int, float)) and value == value:
                    topics.append(f"{key}:{int(value)}")
                elif isinstance(value, str) and value.strip():
                    topics.append(f"{key}:{value.strip()}")
        return topics

    def _extract_topic_value(self, row: Dict, column: str) -> Optional[int]:
        if column in row:
            try:
                value = row.get(column)
                if value is None:
                    return None
                if isinstance(value, (int, float)):
                    if isinstance(value, float) and math.isnan(value):
                        return None
                    return int(value)
                text = str(value).strip()
                if not text:
                    return None
                return int(float(text))
            except (TypeError, ValueError):
                return None
        return None

    def _extract_int(self, row: Dict, keys: List[str]) -> Optional[int]:
        for key in keys:
            if key in row:
                return self._safe_int(row.get(key))
        return None

    def _extract_float(self, row: Dict, keys: List[str]) -> Optional[float]:
        for key in keys:
            if key in row:
                return self._safe_float(row.get(key))
        return None

    @staticmethod
    def _safe_int(value) -> Optional[int]:
        if value is None or (isinstance(value, float) and math.isnan(value)):
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _safe_float(value) -> Optional[float]:
        if value is None or (isinstance(value, float) and math.isnan(value)):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _safe_str(value) -> Optional[str]:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @staticmethod
    def _coerce_bool(value) -> bool:
        if isinstance(value, bool):
            return value
        if value is None:
            return False
        if isinstance(value, (int, float)):
            return value != 0 and not math.isnan(value)
        text = str(value).strip().lower()
        if text in {"1", "true", "yes", "y"}:
            return True
        if text in {"0", "false", "no", "n", "", "none"}:
            return False
        return True

    def export_catalog(self, job_id: str) -> bytes:
        return self._catalog_exporter.export(job_id)
