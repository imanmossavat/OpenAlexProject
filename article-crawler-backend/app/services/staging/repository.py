from __future__ import annotations

from typing import Dict, Optional

from app.services.staging.session_store import StagingSessionStore


class StagingRepository:
    """Encapsulate CRUD operations for staging sessions."""

    def __init__(self, session_store: Optional[StagingSessionStore] = None):
        self._session_store = session_store or StagingSessionStore()

    def get_session(self, session_id: str) -> Dict:
        return self._session_store.get(session_id)

    def save_session(self, session_id: str, session: Dict) -> Dict:
        self._session_store.save(session_id, session)
        return session

    def delete_session(self, session_id: str) -> None:
        self._session_store.remove(session_id)
