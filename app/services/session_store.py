"""
Session Store
In-memory cache for resume data and analysis results.
In production, replace with Redis for multi-instance support.
"""

import time
import uuid
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class SessionStore:
    """
    Simple in-memory store keyed by session_id.
    Each session holds: parsed_resume, job_description, analysis results.
    TTL-based eviction prevents memory leaks.
    """

    def __init__(self, ttl_seconds: int = 3600):
        self._store: Dict[str, dict] = {}
        self._ttl = ttl_seconds

    def create_session(self) -> str:
        session_id = str(uuid.uuid4())
        self._store[session_id] = {
            "created_at": time.time(),
            "parsed_resume": None,
            "job_description": None,
            "target_role": None,
            "ats_score": None,
            "skill_gap": None,
            "section_feedback": None,
            "ai_suggestions": None,
            "learning_roadmap": None,
            "interview_questions": None,
            "career_paths": None,
            "project_suggestions": None,
            "github_analysis": None,
            "chat_history": [],
        }
        self._evict_expired()
        return session_id

    def get(self, session_id: str) -> Optional[dict]:
        session = self._store.get(session_id)
        if session and (time.time() - session["created_at"]) < self._ttl:
            return session
        if session:
            del self._store[session_id]
        return None

    def update(self, session_id: str, key: str, value: Any) -> bool:
        session = self.get(session_id)
        if session is None:
            return False
        self._store[session_id][key] = value
        return True

    def append_chat(self, session_id: str, role: str, content: str):
        session = self.get(session_id)
        if session:
            self._store[session_id]["chat_history"].append(
                {"role": role, "content": content}
            )

    def _evict_expired(self):
        now = time.time()
        expired = [
            sid for sid, data in self._store.items()
            if (now - data["created_at"]) > self._ttl
        ]
        for sid in expired:
            del self._store[sid]
        if expired:
            logger.info(f"Evicted {len(expired)} expired sessions")

    def session_exists(self, session_id: str) -> bool:
        return self.get(session_id) is not None


# Singleton
session_store = SessionStore()
