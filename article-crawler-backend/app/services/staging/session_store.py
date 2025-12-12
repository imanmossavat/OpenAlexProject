from __future__ import annotations

from typing import Dict


class StagingSessionStore:
    """In-memory persistence for staging sessions."""

    def __init__(self):
        self._sessions: Dict[str, Dict] = {}

    def get(self, session_id: str) -> Dict:
        if session_id not in self._sessions:
            self._sessions[session_id] = {
                "rows": [],
                "next_id": 1,
                "match_rows": [],
            }
        return self._sessions[session_id]

    def save(self, session_id: str, session: Dict) -> Dict:
        self._sessions[session_id] = session
        return self._sessions[session_id]

    def remove(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)
