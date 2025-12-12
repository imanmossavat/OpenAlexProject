from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

import polars as pl

from app.repositories import PaperAnnotationRepository, PaperCatalogRepository
from app.schemas.staging import ColumnCustomFilter

from .query import CatalogQuery


@dataclass(frozen=True)
class CatalogFrame:
    lazy_frame: pl.LazyFrame
    schema: Dict[str, pl.datatypes.DataType]
    mark_lookup: Dict[str, str]


class CatalogLazyFrameBuilder:
    """Build filtered catalog frames based on a ``CatalogQuery``."""

    def __init__(
        self,
        catalog_repository: PaperCatalogRepository,
        annotation_repository: PaperAnnotationRepository,
        *,
        mark_column: str,
        allowed_marks: Sequence[str],
        identifier_fields: Sequence[str],
    ) -> None:
        self._catalog_repo = catalog_repository
        self._annotation_repo = annotation_repository
        self._mark_column = mark_column
        self._allowed_marks = {mark.lower() for mark in allowed_marks}
        self._identifier_fields = {field.lower() for field in identifier_fields}

    def build(self, job_id: str, query: CatalogQuery) -> CatalogFrame:
        lf = self._catalog_repo.scan_catalog(job_id)
        schema = lf.schema

        mark_lookup = self._annotation_repo.load_marks(job_id) or {}
        if mark_lookup:
            lf = lf.with_columns(
                pl.col("paperId")
                .cast(pl.Utf8, strict=False)
                .replace(mark_lookup, default="standard")
                .fill_null("standard")
                .alias(self._mark_column)
            )
        else:
            lf = lf.with_columns(pl.lit("standard").alias(self._mark_column))

        lf = self._apply_search_filters(lf, schema, query)
        lf = self._apply_topic_filters(lf, schema, query)
        lf = self._apply_mark_filters(lf, schema, query)
        lf = self._apply_column_value_filters(lf, schema, query)
        lf = self._apply_custom_filters(lf, schema, query.custom_filters)

        return CatalogFrame(lazy_frame=lf, schema=schema, mark_lookup=mark_lookup)

    def selected_filter_map(self, query: CatalogQuery) -> Dict[str, List[str]]:
        return {
            "title": self._normalize_value_list(query.title_values),
            "authors": self._normalize_value_list(query.author_values),
            "venue": self._normalize_value_list(query.venue_values),
            "year": [str(year) for year in self._normalize_int_list(query.year_values)],
            "identifier": self._selected_identifier_values(query.identifier_filters),
        }

    def _apply_search_filters(
        self, lf: pl.LazyFrame, schema: Dict[str, pl.datatypes.DataType], query: CatalogQuery
    ) -> pl.LazyFrame:
        trimmed_query = query.normalized_search()
        if trimmed_query:
            filters = []
            lowered_query = trimmed_query.lower()
            if "title" in schema:
                filters.append(
                    pl.col("title")
                    .cast(pl.Utf8, strict=False)
                    .fill_null("")
                    .str.to_lowercase()
                    .str.contains(lowered_query, literal=True)
                )
            if "paperId" in schema:
                filters.append(
                    pl.col("paperId")
                    .cast(pl.Utf8, strict=False)
                    .fill_null("")
                    .str.to_lowercase()
                    .str.contains(lowered_query, literal=True)
                )
            if filters:
                combined = filters[0]
                for expr in filters[1:]:
                    combined = combined | expr
                lf = lf.filter(combined)

        trimmed_venue = (query.venue or "").strip()
        if trimmed_venue and "venue" in schema:
            venue_lookup = trimmed_venue.lower()
            lf = lf.filter(
                pl.col("venue")
                .cast(pl.Utf8, strict=False)
                .fill_null("")
                .str.to_lowercase()
                .str.contains(venue_lookup, literal=False)
            )

        trimmed_doi = (query.doi or "").strip()
        if trimmed_doi and "doi" in schema:
            doi_lookup = trimmed_doi.lower()
            lf = lf.filter(
                pl.col("doi")
                .cast(pl.Utf8, strict=False)
                .fill_null("")
                .str.to_lowercase()
                .str.contains(doi_lookup, literal=False)
            )

        normalized_doi_filter = self._normalize_presence_filter(query.doi_filter)
        if normalized_doi_filter:
            lf = self._apply_string_presence_filter(
                lf, schema, "doi", normalized_doi_filter
            )

        if query.year_from is not None and "year" in schema:
            lf = lf.filter(
                pl.col("year").cast(pl.Int64, strict=False) >= int(query.year_from)
            )
        if query.year_to is not None and "year" in schema:
            lf = lf.filter(
                pl.col("year").cast(pl.Int64, strict=False) <= int(query.year_to)
            )

        normalized_seed_filter = self._normalize_presence_filter(query.seed_filter)
        if not normalized_seed_filter and query.seed_only:
            normalized_seed_filter = "with"
        if normalized_seed_filter:
            lf = self._apply_boolean_presence_filter(
                lf, schema, ["isSeed", "seed", "is_seed"], normalized_seed_filter
            )

        normalized_retraction_filter = self._normalize_presence_filter(
            query.retraction_filter
        )
        if not normalized_retraction_filter and query.retracted_only:
            normalized_retraction_filter = "with"
        if normalized_retraction_filter:
            lf = self._apply_boolean_presence_filter(
                lf,
                schema,
                ["isRetracted", "retracted", "is_retracted"],
                normalized_retraction_filter,
            )

        return lf

    def _apply_topic_filters(
        self, lf: pl.LazyFrame, schema: Dict[str, pl.datatypes.DataType], query: CatalogQuery
    ) -> pl.LazyFrame:
        normalized_topics: List[int] = []
        if query.topic is not None:
            normalized_topics.append(int(query.topic))
        if query.topic_ids:
            for value in query.topic_ids:
                try:
                    normalized_topics.append(int(value))
                except (TypeError, ValueError):
                    continue
        if not normalized_topics:
            return lf

        topic_exprs = []
        for topic_value in normalized_topics:
            expr = self._topic_filter_expression(schema, topic_value, query.topic_model)
            if expr is not None:
                topic_exprs.append(expr)
        if not topic_exprs:
            return lf

        combined = topic_exprs[0]
        for expr in topic_exprs[1:]:
            combined = combined | expr
        return lf.filter(combined)

    def _apply_mark_filters(
        self, lf: pl.LazyFrame, schema: Dict[str, pl.datatypes.DataType], query: CatalogQuery
    ) -> pl.LazyFrame:
        normalized_marks = self._normalize_mark_filters(query.mark_filters)
        if normalized_marks:
            return lf.filter(pl.col(self._mark_column).is_in(normalized_marks))
        return lf

    def _apply_column_value_filters(
        self, lf: pl.LazyFrame, schema: Dict[str, pl.datatypes.DataType], query: CatalogQuery
    ) -> pl.LazyFrame:
        normalized_titles = self._normalize_value_list(query.title_values)
        if normalized_titles and "title" in schema:
            lf = lf.filter(
                pl.col("title")
                .cast(pl.Utf8, strict=False)
                .str.strip_chars()
                .is_in(normalized_titles)
            )

        normalized_venues = self._normalize_value_list(query.venue_values)
        if normalized_venues and "venue" in schema:
            lf = lf.filter(
                pl.col("venue")
                .cast(pl.Utf8, strict=False)
                .str.strip_chars()
                .is_in(normalized_venues)
            )

        numeric_years = self._normalize_int_list(query.year_values)
        if numeric_years and "year" in schema:
            lf = lf.filter(
                pl.col("year").cast(pl.Int64, strict=False).is_in(numeric_years)
            )

        normalized_authors = self._normalize_value_list(query.author_values)
        if normalized_authors:
            if "authors_display" in schema:
                expr = None
                for value in normalized_authors:
                    clause = pl.col("authors_display").list.contains(value)
                    expr = clause if expr is None else (expr | clause)
                if expr is not None:
                    lf = lf.filter(expr)
            elif "authors" in schema:
                expr = None
                for value in normalized_authors:
                    lowered = value.lower()
                    clause = (
                        pl.col("authors")
                        .cast(pl.Utf8, strict=False)
                        .str.to_lowercase()
                        .str.contains(lowered, literal=True)
                    )
                    expr = clause if expr is None else (expr | clause)
                if expr is not None:
                    lf = lf.filter(expr)

        normalized_identifiers = self._normalize_identifier_filters(
            query.identifier_filters
        )
        if normalized_identifiers:
            expr = None
            for field, value in normalized_identifiers:
                column = "doi" if field == "doi" else field
                if column not in schema:
                    continue
                clause = (
                    pl.col(column)
                    .cast(pl.Utf8, strict=False)
                    .str.strip_chars()
                    .str.to_lowercase()
                    == value.lower()
                )
                expr = clause if expr is None else (expr | clause)
            if expr is not None:
                lf = lf.filter(expr)

        return lf

    def _apply_custom_filters(
        self,
        lf: pl.LazyFrame,
        schema: Dict[str, pl.datatypes.DataType],
        custom_filters: Optional[List[ColumnCustomFilter]],
    ) -> pl.LazyFrame:
        if not custom_filters:
            return lf

        expressions: List[pl.Expr] = []

        for custom in custom_filters:
            column = custom.column
            operator = custom.operator
            value = (custom.value or "").strip()
            value_to = (custom.value_to or "").strip() if custom.value_to else None
            if not value:
                continue

            if column == "identifier":
                target_column = None
                for candidate in ("doi", "url"):
                    if candidate in schema:
                        target_column = candidate
                        break
                if not target_column:
                    continue
                base = pl.col(target_column).cast(pl.Utf8, strict=False)
                expr = self._build_text_filter_expr(base, operator, value, value_to)
            elif column == "authors":
                if "authors_display" in schema:
                    base = pl.col("authors_display").list.join(" || ")
                elif "authors" in schema:
                    base = pl.col("authors")
                else:
                    continue
                base = base.cast(pl.Utf8, strict=False)
                expr = self._build_text_filter_expr(base, operator, value, value_to)
            elif column == "year":
                if "year" not in schema:
                    continue
                expr = self._build_number_filter_expr(
                    pl.col("year").cast(pl.Float64, strict=False),
                    operator,
                    value,
                    value_to,
                )
            else:
                if column not in schema:
                    continue
                base = pl.col(column).cast(pl.Utf8, strict=False)
                expr = self._build_text_filter_expr(base, operator, value, value_to)

            if expr is not None:
                expressions.append(expr)

        if not expressions:
            return lf

        combined = expressions[0]
        for expr in expressions[1:]:
            combined = combined & expr
        return lf.filter(combined)

    def _normalize_presence_filter(self, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = str(value).strip().lower()
        if normalized in {"with", "without"}:
            return normalized
        if normalized in {"all", ""}:
            return None
        return None

    def _apply_string_presence_filter(
        self,
        lf: pl.LazyFrame,
        schema: Dict[str, pl.datatypes.DataType],
        column: str,
        mode: str,
    ) -> pl.LazyFrame:
        if column not in schema or mode not in {"with", "without"}:
            return lf
        trimmed = (
            pl.col(column)
            .cast(pl.Utf8, strict=False)
            .str.strip_chars()
        )
        present_expr = trimmed.is_not_null() & (trimmed != "")
        if mode == "with":
            return lf.filter(present_expr)
        return lf.filter(~present_expr)

    def _apply_boolean_presence_filter(
        self,
        lf: pl.LazyFrame,
        schema: Dict[str, pl.datatypes.DataType],
        candidates: List[str],
        mode: str,
    ) -> pl.LazyFrame:
        if mode not in {"with", "without"}:
            return lf
        expr = self._any_bool_columns(schema, candidates)
        if expr is None:
            return lf
        if mode == "with":
            return lf.filter(expr)
        return lf.filter(~expr)

    def _any_bool_columns(
        self, schema: Dict[str, pl.datatypes.DataType], candidates: List[str]
    ) -> Optional[pl.Expr]:
        available = [name for name in candidates if name in schema]
        if not available:
            return None
        expr = pl.col(available[0]).cast(pl.Boolean, strict=False).fill_null(False)
        for name in available[1:]:
            expr = expr | pl.col(name).cast(pl.Boolean, strict=False).fill_null(False)
        return expr

    def _topic_filter_expression(
        self,
        schema: Dict[str, pl.datatypes.DataType],
        topic: int,
        topic_model: Optional[str],
    ) -> Optional[pl.Expr]:
        topic_value = int(topic)
        if topic_model:
            normalized = topic_model.lower()
            column = f"{normalized}_topic"
            if column in schema:
                return pl.col(column).cast(pl.Int64, strict=False) == topic_value
            return None

        columns = [col for col in ("nmf_topic", "lda_topic") if col in schema]
        if not columns:
            return None
        expr = pl.col(columns[0]).cast(pl.Int64, strict=False) == topic_value
        for column in columns[1:]:
            expr = expr | (pl.col(column).cast(pl.Int64, strict=False) == topic_value)
        return expr

    def _normalize_mark_filters(
        self,
        marks: Optional[List[str]],
    ) -> List[str]:
        if not marks:
            return []
        normalized: List[str] = []
        seen = set()
        for value in marks:
            if not value:
                continue
            candidate = str(value).strip().lower()
            if candidate in {"", "all"}:
                continue
            if candidate in self._allowed_marks and candidate not in seen:
                seen.add(candidate)
                normalized.append(candidate)
        if not normalized or len(seen) == len(self._allowed_marks):
            return []
        return normalized

    def _normalize_value_list(self, values: Optional[List[str]]) -> List[str]:
        normalized: List[str] = []
        for value in values or []:
            text = (value or "").strip()
            if text:
                normalized.append(text)
        return normalized

    def _normalize_int_list(self, values: Optional[List[int]]) -> List[int]:
        normalized: List[int] = []
        for value in values or []:
            try:
                normalized.append(int(value))
            except (TypeError, ValueError):
                continue
        return normalized

    def _normalize_identifier_filters(
        self,
        filters: Optional[List[Dict[str, str]]],
    ) -> List[tuple[str, str]]:
        normalized: List[tuple[str, str]] = []
        for item in filters or []:
            field = (item.get("field") or "").strip().lower()
            value = (item.get("value") or "").strip()
            if not field or not value or field not in self._identifier_fields:
                continue
            normalized.append((field, value))
        return normalized

    def _selected_identifier_values(
        self,
        filters: Optional[List[Dict[str, str]]],
    ) -> List[str]:
        selected: List[str] = []
        for item in filters or []:
            field = (item.get("field") or "").strip().lower()
            value = (item.get("value") or "").strip()
            if not field or not value:
                continue
            selected.append(f"{field}::{value}")
        return selected

    def _build_text_filter_expr(
        self,
        expr: pl.Expr,
        operator: str,
        value: str,
        value_to: Optional[str],
    ) -> Optional[pl.Expr]:
        normalized = expr.cast(pl.Utf8, strict=False).str.strip_chars().fill_null("")
        lowered = normalized.str.to_lowercase()
        target = value.lower()

        if operator == "equals":
            return lowered == target
        if operator == "not_equals":
            return lowered != target
        if operator == "begins_with":
            return lowered.str.starts_with(target)
        if operator == "not_begins_with":
            return ~lowered.str.starts_with(target)
        if operator == "ends_with":
            return lowered.str.ends_with(target)
        if operator == "not_ends_with":
            return ~lowered.str.ends_with(target)
        if operator == "contains":
            return lowered.str.contains(target, literal=True)
        if operator == "not_contains":
            return ~lowered.str.contains(target, literal=True)
        return None

    def _build_number_filter_expr(
        self,
        expr: pl.Expr,
        operator: str,
        value: str,
        value_to: Optional[str],
    ) -> Optional[pl.Expr]:
        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            return None

        if operator == "equals":
            return expr == numeric_value
        if operator == "not_equals":
            return expr != numeric_value
        if operator == "greater_than":
            return expr > numeric_value
        if operator == "greater_than_or_equal":
            return expr >= numeric_value
        if operator == "less_than":
            return expr < numeric_value
        if operator == "less_than_or_equal":
            return expr <= numeric_value
        if operator in {"between", "not_between"}:
            if value_to is None:
                return None
            try:
                numeric_to = float(value_to)
            except (TypeError, ValueError):
                return None
            between_expr = (expr >= min(numeric_value, numeric_to)) & (
                expr <= max(numeric_value, numeric_to)
            )
            return between_expr if operator == "between" else ~between_expr
        return None
