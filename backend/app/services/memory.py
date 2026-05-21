"""
Session Memory Service
----------------------
In-memory, session-scoped conversation history with automatic expiry.
Each session stores a list of (role, content) message pairs.
"""

import time
from collections import defaultdict
from dataclasses import dataclass, field
from threading import Lock
from typing import List, Dict

from app.config import settings
from app.utils.logger import logger


@dataclass
class Message:
    role: str   # "user" | "assistant"
    content: str
    timestamp: float = field(default_factory=time.time)


class MemoryService:
    """Thread-safe in-memory session store."""

    def __init__(self):
        self._sessions: Dict[str, List[Message]] = defaultdict(list)
        self._lock = Lock()
        self._expiry_seconds = settings.SESSION_EXPIRY_MINUTES * 60
        self._max_turns = settings.MAX_HISTORY_TURNS

    # ── Public API ─────────────────────────────────────────────────────────────

    def add_message(self, session_id: str, role: str, content: str) -> None:
        with self._lock:
            self._sessions[session_id].append(Message(role=role, content=content))
            # Trim to max window (keep last N user+assistant pairs)
            self._sessions[session_id] = self._sessions[session_id][-(self._max_turns * 2):]

    def get_history(self, session_id: str) -> List[Message]:
        with self._lock:
            self._cleanup_expired()
            return list(self._sessions.get(session_id, []))

    def get_history_as_text(self, session_id: str) -> str:
        """Return conversation history formatted for prompt injection."""
        messages = self.get_history(session_id)
        if not messages:
            return ""
        lines = []
        for msg in messages:
            prefix = "Customer" if msg.role == "user" else "BankBot"
            lines.append(f"{prefix}: {msg.content}")
        return "\n".join(lines)

    def build_contextual_query(self, session_id: str, current_query: str) -> str:
        """
        Combine recent history with the current query so retrieval is
        context-aware (handles pronouns like 'it', 'that loan', etc.).
        """
        history = self.get_history(session_id)
        if not history:
            return current_query
        # Use last 2 exchanges for query reformulation
        recent = history[-4:]
        context_parts = [msg.content for msg in recent] + [current_query]
        return " ".join(context_parts)

    def clear_session(self, session_id: str) -> None:
        with self._lock:
            self._sessions.pop(session_id, None)
            logger.debug(f"Session cleared: {session_id}")

    def get_session_count(self) -> int:
        with self._lock:
            return len(self._sessions)

    # ── Cleanup ────────────────────────────────────────────────────────────────

    def _cleanup_expired(self) -> None:
        """Remove sessions that have been idle beyond the expiry window."""
        now = time.time()
        expired = []
        for sid, messages in self._sessions.items():
            if messages and (now - messages[-1].timestamp) > self._expiry_seconds:
                expired.append(sid)
        for sid in expired:
            del self._sessions[sid]
        if expired:
            logger.debug(f"Expired {len(expired)} idle session(s)")


# Singleton
_memory_service: MemoryService = None


def get_memory_service() -> MemoryService:
    global _memory_service
    if _memory_service is None:
        _memory_service = MemoryService()
    return _memory_service
