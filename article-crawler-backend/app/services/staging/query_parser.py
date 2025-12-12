from typing import Dict, List, Optional

from pydantic import ValidationError

from app.schemas.staging import (
    ColumnCustomFilter,
    NUMBER_FILTER_COLUMNS,
    NUMBER_FILTER_OPERATOR_VALUES,
    TEXT_FILTER_COLUMNS,
    TEXT_FILTER_OPERATOR_VALUES,
)


class StagingQueryParser:
    """Convert raw query parameters into validated filter objects."""

    IDENTIFIER_FIELDS = {"doi", "url"}
    VALID_RETRACTION_STATUSES = {"retracted", "not_retracted"}

    def parse_identifier_filters(self, raw_values: Optional[List[str]]) -> List[Dict[str, str]]:
        filters: List[Dict[str, str]] = []
        for raw in raw_values or []:
            if not raw or "::" not in raw:
                continue
            field, value = raw.split("::", 1)
            clean_field = (field or "").strip().lower()
            clean_value = (value or "").strip()
            if not clean_field or not clean_value:
                continue
            if clean_field not in self.IDENTIFIER_FIELDS:
                continue
            filters.append({"field": clean_field, "value": clean_value})
        return filters

    def parse_column_filters(self, raw_filters: Optional[List[str]]) -> List[ColumnCustomFilter]:
        parsed: List[ColumnCustomFilter] = []
        if not raw_filters:
            return parsed

        for raw in raw_filters:
            if not raw:
                continue
            parts = [part.strip() for part in raw.split("::")]
            if len(parts) < 3:
                continue

            column, operator, value = parts[0], parts[1], parts[2]
            value_to = parts[3] if len(parts) > 3 else None
            value_to = value_to or None

            try:
                candidate = ColumnCustomFilter(
                    column=column,
                    operator=operator,
                    value=value,
                    value_to=value_to,
                )
            except ValidationError:
                continue

            if candidate.column in NUMBER_FILTER_COLUMNS:
                if candidate.operator not in NUMBER_FILTER_OPERATOR_VALUES:
                    continue
                if candidate.operator in {"between", "not_between"} and not candidate.value_to:
                    continue
            elif candidate.column in TEXT_FILTER_COLUMNS:
                if candidate.operator not in TEXT_FILTER_OPERATOR_VALUES:
                    continue
            else:
                continue

            parsed.append(candidate)
        return parsed

    def validate_retraction_status(self, retraction_status: Optional[str]) -> Optional[str]:
        if (
            retraction_status
            and retraction_status not in self.VALID_RETRACTION_STATUSES
        ):
            raise ValueError("Invalid retraction_status value")
        return retraction_status
