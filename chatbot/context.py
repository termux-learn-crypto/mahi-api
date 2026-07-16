from dataclasses import dataclass, field
from collections import deque
import time


@dataclass
class Message:
    role: str
    text: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class Session:
    user_id: str
    user_name: str | None = None
    history: deque = field(default_factory=lambda: deque(maxlen=20))
    created_at: float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)

    def add_message(self, role: str, text: str):
        self.history.append(Message(role=role, text=text))
        self.last_active = time.time()

    def get_recent(self, n: int = 5) -> list[dict]:
        recent = list(self.history)[-n:]
        return [{"role": msg.role, "text": msg.text} for msg in recent]

    def clear(self):
        self.history.clear()


class SessionManager:
    def __init__(self, max_sessions: int = 1000, ttl_seconds: int = 3600):
        self.sessions: dict[str, Session] = {}
        self.max_sessions = max_sessions
        self.ttl_seconds = ttl_seconds

    def get_session(self, user_id: str) -> Session:
        if user_id in self.sessions:
            session = self.sessions[user_id]
            session.last_active = time.time()
            return session
        session = Session(user_id=user_id)
        self.sessions[user_id] = session
        self._cleanup()
        return session

    def delete_session(self, user_id: str) -> bool:
        if user_id in self.sessions:
            del self.sessions[user_id]
            return True
        return False

    def _cleanup(self):
        now = time.time()
        expired = [
            uid for uid, s in self.sessions.items()
            if now - s.last_active > self.ttl_seconds
        ]
        for uid in expired:
            del self.sessions[uid]

        if len(self.sessions) > self.max_sessions:
            sorted_sessions = sorted(
                self.sessions.items(),
                key=lambda x: x[1].last_active
            )
            to_remove = len(self.sessions) - self.max_sessions
            for uid, _ in sorted_sessions[:to_remove]:
                del self.sessions[uid]
