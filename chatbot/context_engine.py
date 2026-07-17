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
    BRANCHING = "branching"


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
            "topic_history": deque(maxlen=50),
            "pending_questions": [],
            "user_focus": None,
            "conversation_started": None,
            "turn_count": 0,
            "entities_mentioned": defaultdict(list),
            "branches": [],
            "current_branch": None,
            "context_window": deque(maxlen=50),
            "predicted_next": None,
            "active_threads": {},
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

        ctx["context_window"].append({
            "role": "user",
            "message": message,
            "intent": intent,
            "timestamp": datetime.now().isoformat(),
        })

        if response:
            ctx["context_window"].append({
                "role": "assistant",
                "message": response[:200],
                "intent": intent,
                "timestamp": datetime.now().isoformat(),
            })

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

        self._track_entities(ctx, message, intent)

        if self._is_follow_up(message, ctx["last_intent"], intent):
            ctx["follow_up_count"] += 1
            ctx["state"] = ConversationState.FOLLOW_UP
        else:
            ctx["follow_up_count"] = 0

        if self._is_branching(message, ctx):
            ctx["state"] = ConversationState.BRANCHING
            self._create_branch(ctx, message, intent)
        elif intent and intent.startswith("mobile_"):
            ctx["state"] = ConversationState.COMMAND
        elif "?" in message:
            ctx["state"] = ConversationState.QUESTION
        elif intent in ("advice", "knowledge", "tech", "life"):
            ctx["state"] = ConversationState.TASK_ACTIVE
        else:
            ctx["state"] = ConversationState.CHATTING

        self._update_active_tasks(ctx, intent, message)

        ctx["predicted_next"] = self._predict_next_topic(ctx)

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
            "shopping": ["buy", "kharid", "shop", "price", "sale", "discount"],
            "gaming": ["game", "gaming", "play", "player", "level", "score"],
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

    def _is_branching(self, message: str, ctx: dict) -> bool:
        branching_indicators = [
            "waise", "by the way", "btw", "aur ek baat",
            "actually", "real mein", "anyway", "chalo",
        ]
        msg_lower = message.lower()
        has_branching = any(ind in msg_lower for ind in branching_indicators)

        if has_branching and ctx["current_topic"]:
            return True
        return False

    def _create_branch(self, ctx: dict, message: str, intent: str):
        branch = {
            "id": len(ctx["branches"]) + 1,
            "parent_topic": ctx["current_topic"],
            "message": message[:100],
            "intent": intent,
            "created_at": datetime.now().isoformat(),
            "turn": ctx["turn_count"],
        }
        ctx["branches"].append(branch)
        ctx["current_branch"] = branch["id"]

        ctx["active_threads"][branch["id"]] = {
            "topic": ctx["current_topic"],
            "parent_branch": None,
            "status": "active",
        }

    def _track_entities(self, ctx: dict, message: str, intent: str):
        from .entities import entity_extractor
        entities = entity_extractor.extract(message)

        for entity_type in ["names", "places", "food"]:
            for entity in entities.get(entity_type, []):
                if entity not in ctx["entities_mentioned"][entity_type]:
                    ctx["entities_mentioned"][entity_type].append(entity)

        if len(ctx["entities_mentioned"]["names"]) > 20:
            ctx["entities_mentioned"]["names"] = ctx["entities_mentioned"]["names"][-20:]
        if len(ctx["entities_mentioned"]["places"]) > 20:
            ctx["entities_mentioned"]["places"] = ctx["entities_mentioned"]["places"][-20:]

    def _update_active_tasks(self, ctx: dict, intent: str, message: str):
        task_intents = {
            "calculator": {"type": "calculation", "description": "Math calculation"},
            "translator": {"type": "translation", "description": "Translation task"},
            "search": {"type": "search", "description": "Web search"},
            "mobile_command": {"type": "command", "description": "Mobile command"},
            "weather": {"type": "query", "description": "Weather query"},
            "news": {"type": "query", "description": "News query"},
        }

        if intent in task_intents:
            task_id = f"task_{ctx['turn_count']}"
            ctx["active_tasks"][task_id] = {
                **task_intents[intent],
                "intent": intent,
                "started_at": datetime.now().isoformat(),
                "status": "active",
            }

        completed_intents = ["thanks", "bye", "greeting"]
        if intent in completed_intents:
            for task_id, task in list(ctx["active_tasks"].items()):
                if task["status"] == "active":
                    task["status"] = "completed"
                    task["completed_at"] = datetime.now().isoformat()

    def _predict_next_topic(self, ctx: dict) -> str | None:
        if ctx["turn_count"] < 3:
            return None

        recent_topics = [t["topic"] for t in list(ctx["topic_history"])[-5:] if t["topic"]]
        if not recent_topics:
            return None

        topic_frequency = defaultdict(int)
        for topic in recent_topics:
            topic_frequency[topic] += 1

        if topic_frequency:
            return max(topic_frequency, key=topic_frequency.get)
        return None

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
            "entities_mentioned": dict(ctx["entities_mentioned"]),
            "branches": ctx["branches"],
            "current_branch": ctx["current_branch"],
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
            data["topic_history"] = deque(data.get("topic_history", []), maxlen=50)
            data["active_tasks"] = {}
            data["pending_questions"] = []
            data["user_focus"] = None
            data["entities_mentioned"] = defaultdict(list, data.get("entities_mentioned", {}))
            data["branches"] = data.get("branches", [])
            data["current_branch"] = data.get("current_branch")
            data["context_window"] = deque(maxlen=50)
            data["predicted_next"] = None
            data["active_threads"] = {}
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

    def get_context_window(self, user_id: str, limit: int = 10) -> list[dict]:
        ctx = self.get_context(user_id)
        window = list(ctx["context_window"])
        return window[-limit:]

    def get_entities_context(self, user_id: str) -> dict:
        ctx = self.get_context(user_id)
        return dict(ctx["entities_mentioned"])

    def get_branches(self, user_id: str) -> list[dict]:
        ctx = self.get_context(user_id)
        return ctx["branches"]

    def get_active_threads(self, user_id: str) -> dict:
        ctx = self.get_context(user_id)
        return ctx["active_threads"]

    def switch_branch(self, user_id: str, branch_id: int) -> bool:
        ctx = self.get_context(user_id)
        for branch in ctx["branches"]:
            if branch["id"] == branch_id:
                ctx["current_branch"] = branch_id
                ctx["current_topic"] = branch.get("parent_topic")
                return True
        return False

    def get_conversation_stats(self, user_id: str) -> dict:
        ctx = self.get_context(user_id)
        return {
            "turn_count": ctx["turn_count"],
            "current_topic": ctx["current_topic"],
            "state": ctx["state"],
            "branches": len(ctx["branches"]),
            "active_tasks": len(ctx["active_tasks"]),
            "entities_tracked": sum(len(v) for v in ctx["entities_mentioned"].values()),
            "predicted_next": ctx["predicted_next"],
            "duration": self._get_duration(ctx),
        }

    def _get_duration(self, ctx: dict) -> str:
        if ctx["conversation_started"]:
            try:
                started = datetime.fromisoformat(ctx["conversation_started"])
                duration = datetime.now() - started
                minutes = int(duration.total_seconds() / 60)
                return f"{minutes} minutes"
            except (ValueError, TypeError):
                pass
        return "0 minutes"
