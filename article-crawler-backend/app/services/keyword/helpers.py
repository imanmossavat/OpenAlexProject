from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from app.core.exceptions import InvalidInputException
from app.schemas.keywords import KeywordFilter


class KeywordRepository:
    """Simple in-memory persistence for keyword expressions per session."""

    def __init__(self):
        self._storage: Dict[str, Dict[str, Any]] = {}

    def load(self, session_id: str) -> Dict[str, Any]:
        return dict(self._storage.get(session_id, {}))

    def save(self, session_id: str, payload: Dict[str, Any]) -> None:
        self._storage[session_id] = dict(payload)

    def delete(self, session_id: str) -> None:
        self._storage.pop(session_id, None)


class KeywordFilterBuilder:
    """Validate and normalize keyword expressions."""

    def build(self, expression: str) -> str:
        try:
            model = KeywordFilter(expression=expression)
        except ValueError as exc:
            raise InvalidInputException(f"Invalid keyword expression: {exc}")
        return model.expression


def default_keyword_record() -> Dict[str, Any]:
    now = datetime.now()
    return {"keywords": [], "created_at": now, "updated_at": now}
