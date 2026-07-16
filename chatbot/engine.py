from .nlp import preprocess, tokenize, extract_name
from .intents import classify_intent
from .responses import get_response
from .context import SessionManager


class ChatEngine:
    def __init__(self):
        self.sessions = SessionManager(max_sessions=1000, ttl_seconds=7200)
        self.greeting_count: dict[str, int] = {}

    def chat(self, user_id: str, message: str) -> dict:
        session = self.sessions.get_session(user_id)
        intent = classify_intent(message)

        user_name = session.user_name
        if intent == "user_name":
            extracted = extract_name(message)
            if extracted:
                session.user_name = extracted
                user_name = extracted

        recent_context = session.get_recent(3)
        has_greeted = any(m["role"] == "assistant" for m in recent_context)

        response = get_response(intent, user_name=user_name)

        if intent == "greeting" and has_greeted:
            greeting_count = self.greeting_count.get(user_id, 0) + 1
            self.greeting_count[user_id] = greeting_count
            if greeting_count > 2:
                response = get_response("emotion_bored", user_name=user_name)

        session.add_message("user", message)
        session.add_message("assistant", response)

        return {
            "response": response,
            "intent": intent,
            "emotion": self._detect_emotion(intent),
        }

    def clear_session(self, user_id: str) -> bool:
        return self.sessions.delete_session(user_id)

    def _detect_emotion(self, intent: str) -> str:
        emotion_map = {
            "greeting": "happy",
            "identity": "neutral",
            "user_name": "happy",
            "how_are_you": "neutral",
            "emotion_happy": "happy",
            "emotion_sad": "sad",
            "emotion_angry": "angry",
            "emotion_bored": "bored",
            "compliment": "happy",
            "thanks": "happy",
            "joke": "happy",
            "motivation": "energetic",
            "health": "concerned",
            "time": "neutral",
            "date": "neutral",
            "weather": "neutral",
            "love": "happy",
            "purpose": "neutral",
            "capability": "neutral",
            "bye": "sad",
            "life": "thinking",
            "knowledge": "neutral",
            "tech": "neutral",
            "music": "happy",
            "food": "happy",
            "fear": "concerned",
            "insult": "sad",
            "unknown": "confused",
        }
        return emotion_map.get(intent, "neutral")
