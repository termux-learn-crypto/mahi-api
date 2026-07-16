from dataclasses import dataclass, field
from collections import deque
import time


@dataclass
class Message:
    role: str
    text: str
    intent: str = "unknown"
    emotion: str = "neutral"
    timestamp: float = field(default_factory=time.time)


@dataclass
class Session:
    user_id: str
    user_name: str | None = None
    history: deque = field(default_factory=lambda: deque(maxlen=30))
    current_topic: str | None = None
    mood_history: list[str] = field(default_factory=list)
    message_count: int = 0
    used_responses: set = field(default_factory=set)
    first_seen: float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)

    def add_message(self, role: str, text: str, intent: str = "unknown", emotion: str = "neutral"):
        msg = Message(role=role, text=text, intent=intent, emotion=emotion)
        self.history.append(msg)
        self.message_count += 1
        self.last_active = time.time()
        if role == "user":
            self.current_topic = intent
        if emotion and emotion != "neutral":
            self.mood_history.append(emotion)
            if len(self.mood_history) > 10:
                self.mood_history = self.mood_history[-10:]

    def get_recent(self, n: int = 5) -> list[dict]:
        recent = list(self.history)[-n:]
        return [{"role": m.role, "text": m.text, "intent": m.intent} for m in recent]

    def get_recent_intents(self, n: int = 3) -> list[str]:
        return [m.intent for m in list(self.history)[-n:] if m.role == "user"]

    def get_current_mood(self) -> str:
        if not self.mood_history:
            return "neutral"
        return self.mood_history[-1]

    def get_mood_trend(self) -> str:
        if len(self.mood_history) < 2:
            return "stable"
        recent = self.mood_history[-3:]
        positive = {"happy", "energetic", "excited"}
        negative = {"sad", "angry", "frustrated", "concerned"}
        pos_count = sum(1 for m in recent if m in positive)
        neg_count = sum(1 for m in recent if m in negative)
        if pos_count > neg_count:
            return "improving"
        elif neg_count > pos_count:
            return "declining"
        return "stable"

    def is_first_interaction(self) -> bool:
        return self.message_count <= 1

    def get_time_since_first(self) -> float:
        return time.time() - self.first_seen

    def add_used_response(self, response: str):
        self.used_responses.add(response)
        if len(self.used_responses) > 50:
            self.used_responses = set(list(self.used_responses)[-25:])

    def clear(self):
        self.history.clear()
        self.mood_history.clear()
        self.used_responses.clear()
        self.current_topic = None
        self.message_count = 0


class SessionManager:
    def __init__(self, max_sessions: int = 1000, ttl_seconds: int = 7200):
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
