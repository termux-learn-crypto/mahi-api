import json
import time
from datetime import datetime
from collections import defaultdict, deque
from .database import get_db


class ConversationState:
    IDLE = "idle"
    CHATTING = "chatting"
    COMMAND = "command"
    QUESTION = "question"
    FOLLOW_UP = "follow_up"
    TASK_ACTIVE = "task_active"


class ContextEngine:
    def __init__(self):
        self._init_tables()
        self.contexts = defaultdict(lambda: {
            "current_topic": None,
            "previous_topics": deque(maxlen=10),
            "active_tasks": {},
            "state": ConversationState.IDLE,
            "last_intent": None,
            "follow_up_count": 0,
            "topic_history": deque(maxlen=20),
            "pending_questions": [],
            "user_focus": None,
            "conversation_started": None,
            "turn_count": 0,
        })

    def _init_tables(self):
        conn = get_db()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversation_context (
                user_id TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()

    def get_context(self, user_id: str) -> dict:
        if user_id in self.contexts:
            return dict(self.contexts[user_id])
        ctx = self._load_from_db(user_id)
        if ctx:
            self.contexts[user_id] = ctx
            return dict(ctx)
        return self.contexts[user_id]

    def update_context(self, user_id: str, message: str, intent: str, response: str = None):
        ctx = self.contexts[user_id]

        if ctx["conversation_started"] is None:
            ctx["conversation_started"] = datetime.now().isoformat()
        ctx["turn_count"] += 1

        topic = self._detect_topic(message, intent)
        if topic and topic != ctx["current_topic"]:
            if ctx["current_topic"]:
                ctx["previous_topics"].append(ctx["current_topic"])
            ctx["current_topic"] = topic
            ctx["topic_history"].append({
                "topic": topic,
                "timestamp": datetime.now().isoformat(),
                "turn": ctx["turn_count"],
            })

        if self._is_follow_up(message, ctx["last_intent"], intent):
            ctx["follow_up_count"] += 1
            ctx["state"] = ConversationState.FOLLOW_UP
        else:
            ctx["follow_up_count"] = 0

        if intent and intent.startswith("mobile_"):
            ctx["state"] = ConversationState.COMMAND
        elif "?" in message:
            ctx["state"] = ConversationState.QUESTION
        elif intent in ("advice", "knowledge", "tech", "life"):
            ctx["state"] = ConversationState.TASK_ACTIVE
        else:
            ctx["state"] = ConversationState.CHATTING

        if ctx["pending_questions"]:
            ctx["pending_questions"] = [
                q for q in ctx["pending_questions"]
                if time.time() - q["timestamp"] < 300
            ]

        ctx["last_intent"] = intent
        self._save_to_db(user_id, ctx)

    def _detect_topic(self, message: str, intent: str) -> str | None:
        topic_keywords = {
            "work": ["kaam", "office", "project", "deadline", "meeting", "boss"],
            "health": ["health", "exercise", "gym", "workout", "diet", "doctor"],
            "food": ["food", "khana", "recipe", "restaurant", "cooking"],
            "entertainment": ["movie", "song", "music", "game", "netflix", "youtube"],
            "relationships": ["friend", "dost", "family", "pyar", "love"],
            "education": ["padhai", "study", "exam", "school", "college", "book"],
            "technology": ["tech", "computer", "phone", "app", "software"],
            "weather": ["weather", "mausam", "barish", "dhoop", "thand"],
            "travel": ["travel", "trip", "ghumna", "vacation", "flight"],
            "finance": ["paisa", "money", "saving", "budget", "salary"],
        }

        msg_lower = message.lower()
        for topic, keywords in topic_keywords.items():
            if any(kw in msg_lower for kw in keywords):
                return topic

        intent_topic_map = {
            "health": "health",
            "food": "food",
            "music": "entertainment",
            "tech": "technology",
            "weather": "weather",
            "knowledge": "education",
            "life": "philosophy",
        }
        return intent_topic_map.get(intent)

    def _is_follow_up(self, message: str, last_intent: str, current_intent: str) -> bool:
        follow_up_indicators = [
            "aur", "phir", "uske baad", "woh", "ye", "wo",
            "kya", "kyun", "kaise", "kab", "kahan",
            "same", "wahi", "aisa hi", "aur batao",
            "explain", "elaborate", "details",
        ]
        msg_lower = message.lower()
        return any(ind in msg_lower for ind in follow_up_indicators)

    def clear_context(self, user_id: str):
        if user_id in self.contexts:
            del self.contexts[user_id]
        conn = get_db()
        conn.execute("DELETE FROM conversation_context WHERE user_id=?", (user_id,))
        conn.commit()
        conn.close()

    def _save_to_db(self, user_id: str, ctx: dict):
        conn = get_db()
        data = {
            "current_topic": ctx["current_topic"],
            "previous_topics": list(ctx["previous_topics"]),
            "state": ctx["state"],
            "last_intent": ctx["last_intent"],
            "follow_up_count": ctx["follow_up_count"],
            "turn_count": ctx["turn_count"],
            "topic_history": list(ctx["topic_history"]),
            "conversation_started": ctx["conversation_started"],
        }
        conn.execute("""
            INSERT OR REPLACE INTO conversation_context (user_id, data, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        """, (user_id, json.dumps(data)))
        conn.commit()
        conn.close()

    def _load_from_db(self, user_id: str) -> dict | None:
        conn = get_db()
        row = conn.execute(
            "SELECT data FROM conversation_context WHERE user_id=?",
            (user_id,)
        ).fetchone()
        conn.close()
        if row:
            data = json.loads(row["data"])
            data["previous_topics"] = deque(data.get("previous_topics", []), maxlen=10)
            data["topic_history"] = deque(data.get("topic_history", []), maxlen=20)
            data["active_tasks"] = {}
            data["pending_questions"] = []
            data["user_focus"] = None
            return data
        return None

    def get_topic_summary(self, user_id: str) -> str:
        ctx = self.get_context(user_id)
        topics = list(ctx["topic_history"])[-5:]
        if not topics:
            return "Abhi koi specific topic discuss nahi ho raha."
        topic_list = ", ".join([t["topic"] for t in topics])
        return f"Recent topics: {topic_list}"

    def should_redirect(self, user_id: str) -> bool:
        ctx = self.get_context(user_id)
        return ctx["follow_up_count"] > 3
