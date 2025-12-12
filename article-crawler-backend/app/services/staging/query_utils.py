from __future__ import annotations

from math import ceil
from typing import Any, Dict, List, Optional, Tuple

from app.schemas.staging import (
    ColumnCustomFilter,
    ColumnFilterOption,
    NUMBER_FILTER_COLUMNS,
    NUMBER_FILTER_OPERATOR_VALUES,
    TEXT_FILTER_COLUMNS,
    TEXT_FILTER_OPERATOR_VALUES,
)


class StagingQueryHelper:
    """Utility class encapsulating staging filter/sort/column logic."""

    IDENTIFIER_FIELDS = {"doi", "url"}

    def filter_rows(
        self,
        rows: List[Dict],
        *,
        source_values: Optional[List[str]],
        year_min: Optional[int],
        year_max: Optional[int],
        title_search: Optional[str],
        venue_search: Optional[str],
        author_search: Optional[str],
        keyword_search: Optional[str],
        doi_presence: Optional[str],
        selected_only: bool,
        retraction_status: Optional[str],
        title_values: Optional[List[str]],
        author_values: Optional[List[str]],
        venue_values: Optional[List[str]],
        year_values: Optional[List[int]],
        identifier_filters: Optional[List[Tuple[str, str]]],
        text_custom_filters: Optional[List[Dict]] = None,
        number_custom_filters: Optional[List[Dict]] = None,
    ) -> List[Dict]:
        values = {value.lower() for value in source_values or []}
        title_q = (title_search or "").strip().lower()
        venue_q = (venue_search or "").strip().lower()
        author_q = (author_search or "").strip().lower()
        keyword_q = (keyword_search or "").strip().lower()
        doi_filter = (doi_presence or "").strip().lower()
        title_exact = {self._normalize_string(value) for value in title_values or [] if self._normalize_string(value)}
        author_exact = {self._normalize_string(value) for value in author_values or [] if self._normalize_string(value)}
        venue_exact = {self._normalize_string(value) for value in venue_values or [] if self._normalize_string(value)}
        year_exact = {int(value) for value in year_values or [] if isinstance(value, int)}
        identifier_rules = identifier_filters or []

        filtered = []
        for row in rows:
            if values:
                source = (row.get("source") or "").lower()
                source_type = (row.get("source_type") or "").lower()
                if source not in values and source_type not in values:
                    continue
            year = row.get("year")
            if year_min is not None and year is not None and year < year_min:
                continue
            if year_max is not None and year is not None and year > year_max:
                continue
            if title_q and title_q not in (row.get("title") or "").lower():
                continue
            if venue_q and venue_q not in (row.get("venue") or "").lower():
                continue
            if author_q and author_q not in (row.get("authors") or "").lower():
                continue
            if keyword_q:
                title = (row.get("title") or "").lower()
                abstract = (row.get("abstract") or "").lower()
                if keyword_q not in title and keyword_q not in abstract:
                    continue
            if doi_filter == "with" and not row.get("doi"):
                continue
            if doi_filter == "without" and row.get("doi"):
                continue
            if selected_only and not row.get("is_selected"):
                continue
            if retraction_status == "retracted" and not row.get("is_retracted"):
                continue
            if retraction_status == "not_retracted" and row.get("is_retracted"):
                continue
            if title_exact and self._normalize_string(row.get("title")) not in title_exact:
                continue
            if author_exact and self._normalize_string(row.get("authors")) not in author_exact:
                continue
            if venue_exact and self._normalize_string(row.get("venue")) not in venue_exact:
                continue
            if year_exact:
                year_val = row.get("year")
                if year_val is None or year_val not in year_exact:
                    continue
            if identifier_rules:
                matched_identifier = False
                for field, expected in identifier_rules:
                    candidate = self._normalize_string(row.get(field))
                    if candidate and candidate == expected:
                        matched_identifier = True
                        break
                if not matched_identifier:
                    continue
            if (text_custom_filters or number_custom_filters) and not self.matches_custom_filters(
                row,
                text_custom_filters,
                number_custom_filters,
            ):
                continue
            filtered.append(row)
        return filtered

    def apply_sort(self, rows: List[Dict], *, sort_by: Optional[str], sort_dir: str) -> List[Dict]:
        if not sort_by:
            return list(rows)

        valid_fields = {
            "title",
            "year",
            "venue",
            "source",
            "source_type",
            "authors",
            "selected",
        }
        if sort_by not in valid_fields:
            return list(rows)

        reverse = (sort_dir or "asc").lower() == "desc"
        sort_field = "is_selected" if sort_by == "selected" else sort_by

        def is_empty(row: Dict) -> bool:
            value = row.get(sort_field)
            if sort_field == "year":
                return value is None
            if sort_field == "is_selected":
                return value is None
            if isinstance(value, str):
                return not value.strip()
            return value is None

        def value_key(row: Dict):
            value = row.get(sort_field)
            if sort_field == "year":
                try:
                    return int(value)
                except (TypeError, ValueError):
                    return 0
            if sort_field == "is_selected":
                return bool(value)
            if isinstance(value, str):
                return value.strip().lower()
            return value

        non_empty_rows = [row for row in rows if not is_empty(row)]
        empty_rows = [row for row in rows if is_empty(row)]
        sorted_non_empty = sorted(non_empty_rows, key=value_key, reverse=reverse)
        return sorted_non_empty + empty_rows

    def build_column_options(
        self,
        rows: List[Dict],
        selected_filters: Dict[str, List[str]],
    ) -> Dict[str, List[ColumnFilterOption]]:
        buckets: Dict[str, Dict[str, Dict]] = {
            "title": {},
            "authors": {},
            "venue": {},
            "year": {},
            "identifier": {},
        }

        for row in rows:
            self._accumulate_option(buckets["title"], row.get("title"))
            self._accumulate_option(buckets["authors"], row.get("authors"))
            self._accumulate_option(buckets["venue"], row.get("venue"))
            year_value = row.get("year")
            if year_value is not None:
                self._accumulate_option(buckets["year"], str(year_value))
            for field in self.IDENTIFIER_FIELDS:
                value = row.get(field)
                if not value:
                    continue
                trimmed = str(value).strip()
                if not trimmed:
                    continue
                key = f"{field}::{trimmed}"
                label = f"{field.upper()} · {trimmed}"
                entry = buckets["identifier"].setdefault(
                    key,
                    {"value": key, "label": label, "count": 0, "meta": {"type": field}},
                )
                entry["count"] += 1

        for column, values in (selected_filters or {}).items():
            bucket = buckets.get(column)
            if bucket is None:
                continue
            for raw_value in values or []:
                if not raw_value or raw_value in bucket:
                    continue
                label = raw_value
                meta = None
                if column == "identifier" and "::" in raw_value:
                    field, text = raw_value.split("::", 1)
                    field = field.strip()
                    text = text.strip()
                    label = f"{field.upper()} · {text}"
                    meta = {"type": field.lower()}
                entry = {"value": raw_value, "label": label, "count": 0}
                if meta:
                    entry["meta"] = meta
                bucket[raw_value] = entry

        formatted: Dict[str, List[ColumnFilterOption]] = {}
        for column, bucket in buckets.items():
            formatted[column] = self._format_column_options(column, bucket)
        return formatted

    def normalize_identifier_filters(
        self,
        identifier_filters: Optional[List[Dict[str, str]]],
    ) -> List[Tuple[str, str]]:
        normalized: List[Tuple[str, str]] = []
        for item in identifier_filters or []:
            field = (item.get("field") or "").strip().lower()
            if field not in self.IDENTIFIER_FIELDS:
                continue
            normalized_value = self._normalize_string(item.get("value"))
            if not normalized_value:
                continue
            normalized.append((field, normalized_value))
        return normalized

    def selected_identifier_values(
        self,
        identifier_filters: Optional[List[Dict[str, str]]],
    ) -> List[str]:
        selected: List[str] = []
        for item in identifier_filters or []:
            field = (item.get("field") or "").strip().lower()
            raw_value = (item.get("value") or "").strip()
            if field not in self.IDENTIFIER_FIELDS or not raw_value:
                continue
            selected.append(f"{field}::{raw_value}")
        return selected

    def normalize_custom_filters(
        self,
        filters: Optional[List[ColumnCustomFilter]],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        text_filters: List[Dict[str, Any]] = []
        number_filters: List[Dict[str, Any]] = []
        for candidate in filters or []:
            column = candidate.column
            operator = candidate.operator
            if column in NUMBER_FILTER_COLUMNS:
                primary = self._parse_int(candidate.value)
                secondary = self._parse_int(candidate.value_to) if candidate.value_to is not None else None
                if primary is None:
                    continue
                if operator in {"between", "not_between"}:
                    if secondary is None:
                        continue
                    start, end = sorted([primary, secondary])
                    number_filters.append(
                        {"column": column, "operator": operator, "value": start, "value_to": end}
                    )
                else:
                    number_filters.append(
                        {"column": column, "operator": operator, "value": primary, "value_to": None}
                    )
            else:
                raw_value = (candidate.value or "").strip()
                if not raw_value:
                    continue
                text_filters.append(
                    {"column": column, "operator": operator, "value": raw_value.lower()}
                )
        return text_filters, number_filters

    def normalize_doi(self, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        text = str(value).strip().lower()
        prefixes = (
            "https://doi.org/",
            "http://doi.org/",
            "https://dx.doi.org/",
            "http://dx.doi.org/",
            "doi:",
        )
        for prefix in prefixes:
            if text.startswith(prefix):
                text = text[len(prefix):]
                break
        text = text.strip()
        return text or None

    def accumulate_selected_filters(
        self,
        title_values: Optional[List[str]],
        author_values: Optional[List[str]],
        venue_values: Optional[List[str]],
        year_values: Optional[List[int]],
        identifier_filters: Optional[List[Dict[str, str]]],
    ) -> Dict[str, List[str]]:
        return {
            "title": title_values or [],
            "authors": author_values or [],
            "venue": venue_values or [],
            "year": [str(value) for value in year_values or []],
            "identifier": self.selected_identifier_values(identifier_filters),
        }

    @staticmethod
    def paginate(total: int, page: int, page_size: int) -> Tuple[int, int, int]:
        size = max(1, page_size)
        current_page = max(1, page)
        total_pages = ceil(total / size) if total else 1
        return current_page, size, total_pages

    def _accumulate_option(self, bucket: Dict[str, Dict], raw_value: Optional[str]) -> None:
        if raw_value is None:
            return
        value_str = str(raw_value).strip()
        if not value_str:
            return
        entry = bucket.setdefault(
            value_str,
            {"value": value_str, "label": value_str, "count": 0},
        )
        entry["count"] += 1

    def _format_column_options(
        self,
        column: str,
        bucket: Dict[str, Dict],
    ) -> List[ColumnFilterOption]:
        options = list(bucket.values())
        if not options:
            return []

        if column == "year":
            def year_key(option: Dict):
                try:
                    return (0, int(option["value"]))
                except (ValueError, TypeError):
                    return (1, option["value"])

            options.sort(key=year_key)
        else:
            options.sort(key=lambda option: option["label"].lower())

        formatted: List[ColumnFilterOption] = []
        for option in options:
            payload = {
                "value": option["value"],
                "label": option["label"],
                "count": int(option.get("count", 0)),
            }
            if "meta" in option and option["meta"]:
                payload["meta"] = option["meta"]
            formatted.append(ColumnFilterOption(**payload))
        return formatted

    @staticmethod
    def _normalize_string(value: Optional[str]) -> str:
        return (value or "").strip().lower()

    def matches_custom_filters(
        self,
        row: Dict,
        text_filters: Optional[List[Dict[str, Any]]],
        number_filters: Optional[List[Dict[str, Any]]],
    ) -> bool:
        for rule in text_filters or []:
            candidate = self._extract_text_value(row, rule["column"])
            if not self._evaluate_text_rule(candidate, rule):
                return False
        for rule in number_filters or []:
            candidate = row.get(rule["column"])
            if not self._evaluate_number_rule(candidate, rule):
                return False
        return True

    def _extract_text_value(self, row: Dict, column: str) -> str:
        if column == "identifier":
            parts = []
            doi = (row.get("doi") or "").strip()
            if doi:
                parts.append(doi)
            url = (row.get("url") or "").strip()
            if url:
                parts.append(url)
            return " ".join(parts)
        return (row.get(column) or "").strip()

    def _evaluate_text_rule(self, value: str, rule: Dict[str, Any]) -> bool:
        text_value = (value or "").lower()
        target = rule.get("value") or ""
        operator = rule.get("operator")
        if operator == "equals":
            return text_value == target
        if operator == "not_equals":
            return text_value != target
        if operator == "begins_with":
            return text_value.startswith(target)
        if operator == "not_begins_with":
            return not text_value.startswith(target)
        if operator == "ends_with":
            return text_value.endswith(target)
        if operator == "not_ends_with":
            return not text_value.endswith(target)
        if operator == "contains":
            return target in text_value
        if operator == "not_contains":
            return target not in text_value
        return True

    def _evaluate_number_rule(self, value: Optional[int], rule: Dict[str, Any]) -> bool:
        if value is None:
            return False
        operator = rule.get("operator")
        rule_value = rule.get("value")
        rule_value_to = rule.get("value_to")
        if operator == "equals":
            return value == rule_value
        if operator == "not_equals":
            return value != rule_value
        if operator == "greater_than":
            return value > rule_value
        if operator == "greater_than_or_equal":
            return value >= rule_value
        if operator == "less_than":
            return value < rule_value
        if operator == "less_than_or_equal":
            return value <= rule_value
        if operator == "between":
            if rule_value_to is None:
                return False
            return rule_value <= value <= rule_value_to
        if operator == "not_between":
            if rule_value_to is None:
                return False
            return value < rule_value or value > rule_value_to
        return True

    @staticmethod
    def _parse_int(value: Optional[str]) -> Optional[int]:
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None
