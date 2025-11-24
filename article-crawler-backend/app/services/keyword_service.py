
import logging
from typing import List, Dict
from datetime import datetime

from app.schemas.keywords import KeywordFilter
from app.core.exceptions import InvalidInputException


class KeywordService:

    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        
        self._keywords_storage: Dict[str, Dict] = {}
    
    def initialize_storage(self, session_id: str):
        """Initialize keyword storage for a session if not exists."""
        if session_id not in self._keywords_storage:
            self._keywords_storage[session_id] = {
                'keywords': [],
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
    
    def add_keyword(self, session_id: str, expression: str) -> int:

        self.initialize_storage(session_id)
        
        try:
            validated = KeywordFilter(expression=expression)
        except ValueError as e:
            raise InvalidInputException(f"Invalid keyword expression: {str(e)}")
        
        keywords = self._keywords_storage[session_id]['keywords']
        keywords.append(validated.expression)
        self._keywords_storage[session_id]['updated_at'] = datetime.now()
        
        self.logger.info(f"Added keyword '{validated.expression}' to session {session_id}")
        
        return len(keywords)
    
    def get_keywords(self, session_id: str) -> List[str]:

        self.initialize_storage(session_id)
        return self._keywords_storage[session_id]['keywords'].copy()
    
    def remove_keyword(self, session_id: str, expression: str):

        self.initialize_storage(session_id)
        
        keywords = self._keywords_storage[session_id]['keywords']
        
        try:
            keywords.remove(expression)
            self._keywords_storage[session_id]['updated_at'] = datetime.now()
            self.logger.info(f"Removed keyword '{expression}' from session {session_id}")
        except ValueError:
            raise InvalidInputException(
                f"Keyword '{expression}' not found in session"
            )
    
    def clear_keywords(self, session_id: str):

        self.initialize_storage(session_id)
        
        count = len(self._keywords_storage[session_id]['keywords'])
        self._keywords_storage[session_id]['keywords'] = []
        self._keywords_storage[session_id]['updated_at'] = datetime.now()
        
        self.logger.info(f"Cleared {count} keywords from session {session_id}")
    
    def finalize_keywords(self, session_id: str) -> List[str]:

        keywords = self.get_keywords(session_id)
        
        self.logger.info(
            f"Finalized {len(keywords)} keywords for session {session_id}"
        )
        
        return keywords
    
    def cleanup_session(self, session_id: str):

        if session_id in self._keywords_storage:
            del self._keywords_storage[session_id]
            self.logger.info(f"Cleaned up keyword data for session {session_id}")