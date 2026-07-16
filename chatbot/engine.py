from datetime import datetime
from .nlp import preprocess, tokenize, extract_name, detect_emotion_intensity
from .intents import classify_intent
from .responses import get_response
from .context import SessionManager


class ChatEngine:
    def __init__(self):
        self.sessions = SessionManager(max_sessions=1000, ttl_seconds=7200)

    def chat(self, user_id: str, message: str) -> dict:
        session = self.sessions.get_session(user_id)

        intent = classify_intent(message)

        user_name = session.user_name
        if intent == "user_name":
            extracted = extract_name(message)
            if extracted:
                session.user_name = extracted
                user_name = extracted

        user_mood = detect_emotion_intensity(message)
        time_context = self._get_time_context()

        response = get_response(
            intent,
            user_name=user_name,
            time_context=time_context,
            user_mood=user_mood["emotion"],
            used_responses=session.used_responses,
        )

        session.add_used_response(response)
        assistant_emotion = self._detect_emotion(intent, user_mood)

        session.add_message("user", message, intent=intent, emotion=user_mood["emotion"])
        session.add_message("assistant", response, intent=intent, emotion=assistant_emotion)

        return {
            "response": response,
            "intent": intent,
            "emotion": assistant_emotion,
            "user_mood": user_mood["emotion"],
            "mood_intensity": user_mood["intensity"],
        }

    def clear_session(self, user_id: str) -> bool:
        return self.sessions.delete_session(user_id)

    def _get_time_context(self) -> str:
        hour = datetime.now().hour
        if 5 <= hour < 12:
            return "morning"
        elif 12 <= hour < 17:
            return "afternoon"
        elif 17 <= hour < 21:
            return "evening"
        else:
            return "night"

    def _detect_emotion(self, intent: str, user_mood: dict) -> str:
        if user_mood["intensity"] == "high":
            if user_mood["emotion"] in ("happy", "energetic", "excited"):
                return "happy"
            elif user_mood["emotion"] in ("sad", "frustrated"):
                return "sad"

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
            "celebration": "happy",
            "gossip": "neutral",
            "advice": "thinking",
            "frustration": "concerned",
            "confusion": "confused",
            "story": "neutral",
            "riddle": "happy",
            "miss_you": "happy",
            "sleepy": "neutral",
            "morning": "happy",
            "unknown": "confused",
        }
        return emotion_map.get(intent, "neutral")
