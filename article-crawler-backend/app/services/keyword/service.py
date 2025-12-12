import logging
from datetime import datetime
from typing import Dict, List, Optional

from app.core.exceptions import InvalidInputException
from app.services.keyword.helpers import (
    KeywordRepository,
    KeywordFilterBuilder,
    default_keyword_record,
)


class KeywordService:
    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        repository: Optional[KeywordRepository] = None,
        filter_builder: Optional[KeywordFilterBuilder] = None,
    ):
        self.logger = logger or logging.getLogger(__name__)
        self._repository = repository or KeywordRepository()
        self._filter_builder = filter_builder or KeywordFilterBuilder()

    def _load_record(self, session_id: str) -> Dict:
        record = self._repository.load(session_id)
        if not record:
            record = default_keyword_record()
            self._repository.save(session_id, record)
        return record

    def add_keyword(self, session_id: str, expression: str) -> int:
        record = self._load_record(session_id)
        normalized = self._filter_builder.build(expression)
        record["keywords"].append(normalized)
        record["updated_at"] = datetime.now()
        self._repository.save(session_id, record)
        self.logger.info("Added keyword '%s' to session %s", normalized, session_id)
        return len(record["keywords"])

    def get_keywords(self, session_id: str) -> List[str]:
        record = self._load_record(session_id)
        return list(record["keywords"])

    def remove_keyword(self, session_id: str, expression: str):
        record = self._load_record(session_id)
        keywords = record["keywords"]
        try:
            keywords.remove(expression)
        except ValueError:
            raise InvalidInputException(f"Keyword '{expression}' not found in session")
        record["updated_at"] = datetime.now()
        self._repository.save(session_id, record)
        self.logger.info("Removed keyword '%s' from session %s", expression, session_id)

    def clear_keywords(self, session_id: str):
        record = self._load_record(session_id)
        count = len(record["keywords"])
        record["keywords"] = []
        record["updated_at"] = datetime.now()
        self._repository.save(session_id, record)
        self.logger.info("Cleared %s keywords from session %s", count, session_id)

    def finalize_keywords(self, session_id: str) -> List[str]:
        keywords = self.get_keywords(session_id)
        self.logger.info(
            "Finalized %s keywords for session %s",
            len(keywords),
            session_id,
        )
        return keywords

    def cleanup_session(self, session_id: str):
        self._repository.delete(session_id)
        self.logger.info("Cleaned up keyword data for session %s", session_id)
