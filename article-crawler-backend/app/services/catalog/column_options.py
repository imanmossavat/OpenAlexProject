from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import polars as pl

from app.schemas.papers import ColumnFilterOption, ColumnOptionsPage

from .query_builder import CatalogFrame


class ColumnOptionsBuilder:
    """Builds filter option lists for catalog columns."""

    def __init__(
        self,
        *,
        columns: List[str],
        max_filter_options: int,
    ) -> None:
        self._columns = set(columns)
        self._max_options = max_filter_options

    def build_all(
        self,
        frame: CatalogFrame,
        selected_filters: Dict[str, List[str]],
    ) -> Dict[str, List[ColumnFilterOption]]:
        buckets = {
            "title": self._collect_value_counts(frame, "title")[0],
            "venue": self._collect_value_counts(frame, "venue")[0],
            "year": self._collect_value_counts(
                frame, "year", cast_to_str=True
            )[0],
            "authors": self._collect_author_counts(frame)[0],
            "identifier": self._collect_identifier_counts(frame)[0],
        }

        for column, values in (selected_filters or {}).items():
            bucket = buckets.get(column)
            if bucket is None:
                continue
            for value in values or []:
                if not value or value in bucket:
                    continue
                bucket[value] = {
                    "value": value,
                    "label": value,
                    "count": 0,
                }

        formatted: Dict[str, List[ColumnFilterOption]] = {}
        for column, bucket in buckets.items():
            formatted[column] = self._format_column_options(column, bucket)
        return formatted

    def list_column_options(
        self,
        frame: CatalogFrame,
        column: str,
        *,
        page: int,
        page_size: int,
        option_query: Optional[str],
        selected_filters: Dict[str, List[str]],
    ) -> ColumnOptionsPage:
        normalized_column = (column or "").strip().lower()
        if normalized_column not in self._columns:
            raise ValueError(f"Unsupported column '{column}' for options")

        offset = (page - 1) * page_size
        search_value = (option_query or "").strip()
        bucket, total = self._collect_column_bucket(
            frame,
            normalized_column,
            search=search_value or None,
            limit=page_size,
            offset=offset,
        )

        for value in selected_filters.get(normalized_column, []):
            if not value or value in bucket:
                continue
            bucket[value] = {
                "value": value,
                "label": value,
                "count": 0,
            }

        options = self._format_column_options(
            normalized_column,
            bucket,
            limit=page_size,
        )

        return ColumnOptionsPage(
            column=normalized_column,
            page=page,
            page_size=page_size,
            total=total,
            options=options,
        )

    def _collect_column_bucket(
        self,
        frame: CatalogFrame,
        column: str,
        *,
        search: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> Tuple[Dict[str, Dict[str, Any]], int]:
        if column == "title":
            return self._collect_value_counts(
                frame, "title", search=search, limit=limit, offset=offset
            )
        if column == "venue":
            return self._collect_value_counts(
                frame, "venue", search=search, limit=limit, offset=offset
            )
        if column == "year":
            return self._collect_value_counts(
                frame,
                "year",
                cast_to_str=True,
                search=search,
                limit=limit,
                offset=offset,
            )
        if column == "authors":
            return self._collect_author_counts(
                frame, search=search, limit=limit, offset=offset
            )
        if column == "identifier":
            return self._collect_identifier_counts(
                frame, search=search, limit=limit, offset=offset
            )
        return {}, 0

    def _collect_value_counts(
        self,
        frame: CatalogFrame,
        column: str,
        *,
        cast_to_str: bool = False,
        search: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> Tuple[Dict[str, Dict[str, Any]], int]:
        lf, schema = frame.lazy_frame, frame.schema
        if column not in schema:
            return {}, 0
        expr = pl.col(column)
        if cast_to_str:
            expr = expr.cast(pl.Utf8, strict=False)
        value_frame = (
            lf.select(
                expr.cast(pl.Utf8, strict=False).str.strip_chars().alias("value")
            )
            .filter(pl.col("value").is_not_null() & (pl.col("value") != ""))
        )
        trimmed_search = (search or "").strip()
        if trimmed_search:
            lowered = trimmed_search.lower()
            value_frame = value_frame.filter(
                pl.col("value")
                .str.to_lowercase()
                .str.contains(lowered, literal=False)
            )
        result = (
            value_frame.group_by("value")
            .agg(pl.len().alias("count"))
            .sort("value")
            .collect()
        )
        total = result.height
        start = max(offset, 0)
        length = limit if limit is not None else None
        if start or length is not None:
            result = result.slice(start, length)
        bucket: Dict[str, Dict[str, Any]] = {}
        for row in result.to_dicts():
            value = row.get("value")
            if not value:
                continue
            bucket[value] = {
                "value": value,
                "label": value,
                "count": int(row.get("count", 0)),
            }
        return bucket, total

    def _collect_author_counts(
        self,
        frame: CatalogFrame,
        search: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> Tuple[Dict[str, Dict[str, Any]], int]:
        lf, schema = frame.lazy_frame, frame.schema
        if "authors_display" not in schema:
            return {}, 0
        author_frame = (
            lf.select(pl.col("authors_display"))
            .explode("authors_display")
            .with_columns(
                pl.col("authors_display")
                .cast(pl.Utf8, strict=False)
                .str.strip_chars()
                .alias("value")
            )
            .filter(pl.col("value").is_not_null() & (pl.col("value") != ""))
        )
        trimmed_search = (search or "").strip()
        if trimmed_search:
            lowered = trimmed_search.lower()
            author_frame = author_frame.filter(
                pl.col("value")
                .str.to_lowercase()
                .str.contains(lowered, literal=False)
            )
        result = (
            author_frame.group_by("value")
            .agg(pl.len().alias("count"))
            .sort("value")
            .collect()
        )
        total = result.height
        start = max(offset, 0)
        length = limit if limit is not None else None
        if start or length is not None:
            result = result.slice(start, length)
        bucket: Dict[str, Dict[str, Any]] = {}
        for row in result.to_dicts():
            value = row.get("value")
            if not value:
                continue
            bucket[value] = {
                "value": value,
                "label": value,
                "count": int(row.get("count", 0)),
            }
        return bucket, total

    def _collect_identifier_counts(
        self,
        frame: CatalogFrame,
        search: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> Tuple[Dict[str, Dict[str, Any]], int]:
        lf, schema = frame.lazy_frame, frame.schema
        if "doi" not in schema:
            return {}, 0
        identifier_frame = (
            lf.select(
                pl.col("doi").cast(pl.Utf8, strict=False).str.strip_chars().alias("value")
            )
            .filter(pl.col("value").is_not_null() & (pl.col("value") != ""))
        )
        trimmed_search = (search or "").strip()
        if trimmed_search:
            lowered = trimmed_search.lower()
            identifier_frame = identifier_frame.filter(
                pl.col("value")
                .str.to_lowercase()
                .str.contains(lowered, literal=False)
            )
        result = (
            identifier_frame.group_by("value")
            .agg(pl.len().alias("count"))
            .sort("value")
            .collect()
        )
        total = result.height
        start = max(offset, 0)
        length = limit if limit is not None else None
        if start or length is not None:
            result = result.slice(start, length)
        bucket: Dict[str, Dict[str, Any]] = {}
        for row in result.to_dicts():
            value = row.get("value")
            if not value:
                continue
            key = f"doi::{value}"
            bucket[key] = {
                "value": key,
                "label": f"DOI · {value}",
                "count": int(row.get("count", 0)),
                "meta": {"type": "doi"},
            }
        return bucket, total

    def _format_column_options(
        self,
        column: str,
        bucket: Dict[str, Dict[str, Any]],
        limit: Optional[int] = None,
    ) -> List[ColumnFilterOption]:
        if not bucket:
            return []
        options = list(bucket.values())
        if column == "year":
            def year_key(option: Dict[str, Any]):
                try:
                    return (0, int(option["value"]))
                except (ValueError, TypeError):
                    return (1, option["value"])

            options.sort(key=year_key)
        else:
            options.sort(key=lambda option: str(option["label"]).lower())

        slice_limit = limit if limit is not None else self._max_options
        formatted: List[ColumnFilterOption] = []
        for option in options[:slice_limit]:
            payload = {
                "value": option["value"],
                "label": option["label"],
                "count": int(option.get("count", 0)),
            }
            if option.get("meta"):
                payload["meta"] = option["meta"]
            formatted.append(ColumnFilterOption(**payload))
        return formatted
