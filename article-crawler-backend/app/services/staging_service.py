import logging
from math import ceil
from typing import Any, Dict, List, Optional, Tuple

from app.schemas.staging import (
    ColumnCustomFilter,
    ColumnFilterOption,
    NUMBER_FILTER_COLUMNS,
    NUMBER_FILTER_OPERATOR_VALUES,
    StagingListResponse,
    StagingMatchRow,
    StagingPaper,
    StagingPaperCreate,
    StagingPaperUpdate,
    TEXT_FILTER_COLUMNS,
    TEXT_FILTER_OPERATOR_VALUES,
    _normalize_venue_value,
)


class StagingService:
    """In-memory staging table manager scoped per session."""

    DEFAULT_PAGE_SIZE = 25
    MAX_PAGE_SIZE = 200
    IDENTIFIER_FIELDS = {"doi", "url"}

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self._sessions: Dict[str, Dict] = {}

    def _ensure_session(self, session_id: str) -> Dict:
        if session_id not in self._sessions:
            self._sessions[session_id] = {
                "rows": [],
                "next_id": 1,
                "match_rows": [],
            }
        return self._sessions[session_id]

    def _find_row(self, session_id: str, staging_id: int) -> Dict:
        session = self._ensure_session(session_id)
        for row in session["rows"]:
            if row["staging_id"] == staging_id:
                return row
        raise ValueError(f"Staging row {staging_id} not found for session {session_id}")

    def get_row(self, session_id: str, staging_id: int) -> StagingPaper:
        row = self._find_row(session_id, staging_id)
        return StagingPaper(**row)

    def add_rows(self, session_id: str, rows: List[StagingPaperCreate]) -> List[StagingPaper]:
        session = self._ensure_session(session_id)
        created: List[StagingPaper] = []
        existing_keys = self._collect_row_keys(session["rows"])
        for payload in rows:
            key = self._build_row_key_from_payload(payload)
            if key and key in existing_keys:
                self.logger.debug(f"Skipping duplicate staged row for session {session_id} (key: {key})")
                continue
            normalized_venue = _normalize_venue_value(payload.venue)
            staging_row = {
                "staging_id": session["next_id"],
                "source": payload.source,
                "source_type": payload.source_type,
                "title": payload.title,
                "authors": payload.authors,
                "year": payload.year,
                "venue": normalized_venue,
                "doi": payload.doi,
                "url": payload.url,
                "abstract": payload.abstract,
                "is_retracted": bool(payload.is_retracted),
                "retraction_reason": payload.retraction_reason,
                "retraction_checked_at": payload.retraction_checked_at,
                "retraction_date": payload.retraction_date,
                "source_id": payload.source_id,
                "is_selected": bool(payload.is_selected),
                "source_file_id": payload.source_file_id,
                "source_file_name": payload.source_file_name,
            }
            session["rows"].append(staging_row)
            created.append(StagingPaper(**staging_row))
            session["next_id"] += 1
            if key:
                existing_keys.add(key)
        self.logger.info(f"Added {len(created)} staged papers to session {session_id}")
        return created

    def update_row(self, session_id: str, staging_id: int, updates: StagingPaperUpdate) -> StagingPaper:
        row = self._find_row(session_id, staging_id)
        payload = updates.dict(exclude_unset=True)
        for field, value in payload.items():
            if field == "venue":
                row[field] = _normalize_venue_value(value)
            else:
                row[field] = value
        if "doi" in payload:
            row["is_retracted"] = False
            row["retraction_reason"] = None
            row["retraction_checked_at"] = None
            row["retraction_date"] = None
        self.logger.debug(f"Updated staging row {staging_id} for session {session_id}")
        return StagingPaper(**row)

    def set_selection(self, session_id: str, staging_ids: List[int], is_selected: bool) -> int:
        session = self._ensure_session(session_id)
        updated = 0
        target_ids = set(staging_ids)
        for row in session["rows"]:
            if row["staging_id"] in target_ids:
                row["is_selected"] = is_selected
                updated += 1
        self.logger.debug(
            f"Toggled selection for {updated} rows in session {session_id} (selected={is_selected})"
        )
        return updated

    def remove_rows(self, session_id: str, staging_ids: List[int]) -> int:
        session = self._ensure_session(session_id)
        target_ids = set(staging_ids)
        before = len(session["rows"])
        session["rows"] = [row for row in session["rows"] if row["staging_id"] not in target_ids]
        removed = before - len(session["rows"])
        if removed:
            self.logger.info(f"Removed {removed} staged papers from session {session_id}")
        return removed

    def clear_session(self, session_id: str) -> None:
        if session_id in self._sessions:
            del self._sessions[session_id]
            self.logger.info(f"Cleared staging rows for session {session_id}")
        else:
            self.logger.info(f"Clear staging requested for empty session {session_id}")

    def list_rows(
        self,
        session_id: str,
        *,
        page: int = 1,
        page_size: int = DEFAULT_PAGE_SIZE,
        source_values: Optional[List[str]] = None,
        year_min: Optional[int] = None,
        year_max: Optional[int] = None,
        title_search: Optional[str] = None,
        venue_search: Optional[str] = None,
        author_search: Optional[str] = None,
        keyword_search: Optional[str] = None,
        doi_presence: Optional[str] = None,
        selected_only: bool = False,
        retraction_status: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_dir: str = "asc",
        title_values: Optional[List[str]] = None,
        author_values: Optional[List[str]] = None,
        venue_values: Optional[List[str]] = None,
        year_values: Optional[List[int]] = None,
        identifier_filters: Optional[List[Dict[str, str]]] = None,
        custom_filters: Optional[List[ColumnCustomFilter]] = None,
    ) -> StagingListResponse:
        session = self._ensure_session(session_id)
        rows = session["rows"]
        selected_count = sum(1 for row in rows if row.get("is_selected"))

        normalized_identifier_filters = self._normalize_identifier_filters(identifier_filters)
        text_custom_filters, number_custom_filters = self._normalize_custom_filters(custom_filters)

        filtered = self._apply_filters(
            rows,
            source_values=source_values,
            year_min=year_min,
            year_max=year_max,
            title_search=title_search,
            venue_search=venue_search,
            author_search=author_search,
            keyword_search=keyword_search,
            doi_presence=doi_presence,
            selected_only=selected_only,
            retraction_status=retraction_status,
            title_values=title_values,
            author_values=author_values,
            venue_values=venue_values,
            year_values=year_values,
            identifier_filters=normalized_identifier_filters,
            text_custom_filters=text_custom_filters,
            number_custom_filters=number_custom_filters,
        )

        sorted_rows = self._apply_sort(filtered, sort_by=sort_by, sort_dir=sort_dir)

        size = max(1, min(page_size or self.DEFAULT_PAGE_SIZE, self.MAX_PAGE_SIZE))
        current_page = max(1, page or 1)
        start = (current_page - 1) * size
        end = start + size

        paged_rows = sorted_rows[start:end]
        total_filtered = len(filtered)
        total_pages = ceil(total_filtered / size) if total_filtered else 1
        selected_column_values = {
            "title": title_values or [],
            "authors": author_values or [],
            "venue": venue_values or [],
            "year": [str(value) for value in year_values or []],
            "identifier": self._selected_identifier_values(identifier_filters),
        }
        column_options = self._build_column_options(filtered, selected_column_values)

        return StagingListResponse(
            session_id=session_id,
            rows=[StagingPaper(**row) for row in paged_rows],
            total_rows=len(rows),
            filtered_rows=total_filtered,
            selected_count=selected_count,
            retracted_count=sum(1 for row in rows if row.get("is_retracted")),
            page=current_page,
            page_size=size,
            total_pages=total_pages,
            column_options=column_options,
        )

    def apply_retraction_results(
        self,
        session_id: str,
        *,
        retracted_dois: set,
        checked_at,
        reason: str,
        metadata: Optional[Dict[str, Dict[str, Optional[str]]]] = None,
    ) -> Dict[str, int]:
        session = self._ensure_session(session_id)
        normalized = {self._normalize_doi(value) for value in retracted_dois if value}
        self.logger.debug("Applying retraction results for session %s with %d matched DOIs", session_id, len(normalized))
        eligible_rows = 0
        retracted_rows = 0
        metadata = metadata or {}
        for row in session["rows"]:
            doi_value = self._normalize_doi(row.get("doi"))
            self.logger.debug(
                "Row %s DOI normalized to %s (raw=%s)",
                row.get("staging_id"),
                doi_value,
                row.get("doi"),
            )
            if not doi_value:
                row["is_retracted"] = False
                row["retraction_reason"] = None
                row["retraction_checked_at"] = None
                row["retraction_date"] = None
                continue
            eligible_rows += 1
            is_retracted = doi_value in normalized
            if is_retracted:
                self.logger.debug(
                    "Row %s marked retracted (doi=%s)",
                    row.get("staging_id"),
                    doi_value,
                )
            row["is_retracted"] = is_retracted
            info = metadata.get(doi_value)
            row["retraction_reason"] = (info and info.get("reason")) if is_retracted else None
            if row["retraction_reason"] is None and is_retracted:
                row["retraction_reason"] = reason
            row["retraction_date"] = (info and info.get("date")) if is_retracted else None
            row["retraction_checked_at"] = checked_at
            if is_retracted:
                self.logger.debug(
                    "Row %s metadata reason=%r date=%r",
                    row.get("staging_id"),
                    row["retraction_reason"],
                    row["retraction_date"],
                )
                retracted_rows += 1
        return {
            "eligible_rows": eligible_rows,
            "retracted_rows": retracted_rows,
            "checked_rows": eligible_rows,
        }

    def get_selected_rows(self, session_id: str) -> List[StagingPaper]:
        session = self._ensure_session(session_id)
        return [StagingPaper(**row) for row in session["rows"] if row.get("is_selected")]

    def get_all_rows(self, session_id: str) -> List[StagingPaper]:
        session = self._ensure_session(session_id)
        return [StagingPaper(**row) for row in session["rows"]]

    def store_match_rows(self, session_id: str, rows: List[StagingMatchRow]) -> None:
        session = self._ensure_session(session_id)
        serialized = [
            row.dict()
            if isinstance(row, StagingMatchRow)
            else row
            for row in rows
        ]
        session["match_rows"] = serialized

    def get_match_rows(self, session_id: str) -> List[StagingMatchRow]:
        session = self._ensure_session(session_id)
        stored = session.get("match_rows") or []
        return [
            row
            if isinstance(row, StagingMatchRow)
            else StagingMatchRow(**row)
            for row in stored
        ]

    def _collect_row_keys(self, rows: List[Dict]) -> set:
        keys = set()
        for row in rows:
            key = self._build_row_key_from_dict(row)
            if key:
                keys.add(key)
        return keys

    def _build_row_key_from_payload(self, payload: StagingPaperCreate):
        doi = (payload.doi or "").strip().lower()
        if doi:
            return ("doi", doi)
        source_id = (payload.source_id or "").strip().lower()
        if source_id:
            source_type = (payload.source_type or "").strip().lower()
            return ("source_id", source_type, source_id)
        title = (payload.title or "").strip().lower()
        year = payload.year or None
        if title:
            return ("title_year", title, year)
        return None

    def _build_row_key_from_dict(self, row: Dict):
        doi = (row.get("doi") or "").strip().lower()
        if doi:
            return ("doi", doi)
        source_id = (row.get("source_id") or "").strip().lower()
        if source_id:
            source_type = (row.get("source_type") or "").strip().lower()
            return ("source_id", source_type, source_id)
        title = (row.get("title") or "").strip().lower()
        year = row.get("year") or None
        if title:
            return ("title_year", title, year)
        return None


    def _apply_filters(
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
            if title_q:
                title = (row.get("title") or "").lower()
                if title_q not in title:
                    continue
            if venue_q:
                venue = (row.get("venue") or "").lower()
                if venue_q not in venue:
                    continue
            if author_q:
                authors = (row.get("authors") or "").lower()
                if author_q not in authors:
                    continue
            if keyword_q:
                title = (row.get("title") or "").lower()
                abstract = (row.get("abstract") or "").lower()
                if keyword_q not in title and keyword_q not in abstract:
                    continue
            if doi_filter == "with":
                if not row.get("doi"):
                    continue
            elif doi_filter == "without":
                if row.get("doi"):
                    continue
            if selected_only and not row.get("is_selected"):
                continue
            if retraction_status == "retracted" and not row.get("is_retracted"):
                continue
            if retraction_status == "not_retracted" and row.get("is_retracted"):
                continue
            if title_exact:
                normalized_title = self._normalize_string(row.get("title"))
                if normalized_title not in title_exact:
                    continue
            if author_exact:
                normalized_authors = self._normalize_string(row.get("authors"))
                if normalized_authors not in author_exact:
                    continue
            if venue_exact:
                normalized_venue = self._normalize_string(row.get("venue"))
                if normalized_venue not in venue_exact:
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
            if (text_custom_filters or number_custom_filters) and not self._matches_custom_filters(
                row,
                text_custom_filters,
                number_custom_filters,
            ):
                continue
            filtered.append(row)
        return filtered

    @staticmethod
    def _normalize_string(value: Optional[str]) -> str:
        return (value or "").strip().lower()

    @staticmethod
    def _normalize_doi(value: Optional[str]) -> Optional[str]:
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

    def _normalize_identifier_filters(
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

    def _selected_identifier_values(
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

    def _build_column_options(
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
                if not raw_value:
                    continue
                if raw_value in bucket:
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

    def _normalize_custom_filters(
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

    def _matches_custom_filters(
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

    def _apply_sort(self, rows: List[Dict], *, sort_by: Optional[str], sort_dir: str) -> List[Dict]:
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
