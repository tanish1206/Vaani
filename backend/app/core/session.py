"""
In-memory session state management for VAANI.
Tracks conversational context (last customer, last turn, undo stack, language).
"""

from typing import Dict, Any, Optional, List
import time

class UserSession:
    def __init__(self, session_id: str):
        self.session_id: str = session_id
        self.last_customer_id: Optional[int] = None
        self.last_customer_name: Optional[str] = None
        self.last_entry_ids: List[int] = []
        self.last_actions: List[Dict[str, Any]] = []
        self.language: str = "auto"
        self.updated_at: float = time.time()

    def set_last_customer(self, customer_id: int, name: str):
        self.last_customer_id = customer_id
        self.last_customer_name = name
        self.updated_at = time.time()

    def record_turn_entries(self, entry_ids: List[int], actions: List[Dict[str, Any]]):
        self.last_entry_ids.extend(entry_ids)
        self.last_actions.extend(actions)
        self.updated_at = time.time()

    def clear_last_entries(self):
        self.last_entry_ids = []
        self.last_actions = []
        self.updated_at = time.time()

class SessionManager:
    def __init__(self):
        self._sessions: Dict[str, UserSession] = {}

    def get_or_create(self, session_id: str = "default") -> UserSession:
        if session_id not in self._sessions:
            self._sessions[session_id] = UserSession(session_id)
        return self._sessions[session_id]

session_manager = SessionManager()

