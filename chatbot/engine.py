import random
import re
from datetime import datetime
from .nlp import preprocess, tokenize, extract_name, detect_emotion_intensity
from .intents import classify_intent
from .responses import get_response
from .context import SessionManager
from .facts import get_random_fact
from .quotes import get_random_quote
from .games import get_would_you_rather, get_two_truths_lie, get_tongue_twister
from .names import get_name_meaning


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

        response = self._generate_response(
            intent, message, session, user_name, time_context, user_mood
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

    def _generate_response(
        self, intent: str, message: str, session, user_name, time_context, user_mood
    ) -> str:

        if intent == "daily_fact":
            return self._handle_fact(message)
        elif intent == "quote":
            return self._handle_quote(message)
        elif intent == "tongue_twister":
            return self._handle_tongue_twister(message)
        elif intent == "name_meaning":
            return self._handle_name_meaning(message)
        elif intent == "would_you":
            return self._handle_would_you()
        elif intent == "truth_lie":
            return self._handle_truth_lie()
        elif intent == "time":
            return self._handle_time()
        elif intent == "date":
            return self._handle_date()

        return get_response(
            intent,
            user_name=user_name,
            time_context=time_context,
            user_mood=user_mood["emotion"],
            used_responses=session.used_responses,
        )

    def _handle_fact(self, message: str) -> str:
        categories = ["science", "india", "history", "tech", "animals"]
        msg_lower = message.lower()
        selected_cat = None
        for cat in categories:
            if cat in msg_lower:
                selected_cat = cat
                break

        fact = get_random_fact(selected_cat)
        intro = random.choice(["Fact: ", "Did you know? ", "Interesting fact: ", "Pata hai? ", "Sunno ye: "])
        return f"{intro}{fact}"

    def _handle_quote(self, message: str) -> str:
        categories = ["inspirational", "life", "friendship", "funny", "motivation"]
        msg_lower = message.lower()
        selected_cat = None
        for cat in categories:
            if cat in msg_lower or (cat == "motivation" and "motiv" in msg_lower):
                selected_cat = cat
                break

        quote = get_random_quote(selected_cat)
        return f'"{quote["text"]}" - {quote["author"]}'

    def _handle_tongue_twister(self, message: str) -> str:
        msg_lower = message.lower()
        lang = "english" if "english" in msg_lower else "hindi"
        twister = get_tongue_twister(lang)
        intro = random.choice(["Try this: ", "Tongue twister: ", "Ab bolo ye: ", "Challenge: "])
        return f"{intro}{twister}"

    def _handle_name_meaning(self, message: str) -> str:
        msg_lower = message.lower()
        name_patterns = [
            r"(.+?)\s*naam\s+ka\s+(?:matlab|arth)",
            r"(.+?)\s*ka\s+matlab\s+kya\s+hai",
            r"(.+?)\s*ka\s+meaning\s+batao",
            r"(.+?)\s*ka\s+meaning",
            r"(.+?)\s*ka\s+arth",
            r"meaning\s+of\s+(.+?)(?:\?|$)",
            r"(.+?)\s*matlab\s+kya\s+hai",
        ]

        name = None
        for pattern in name_patterns:
            match = re.search(pattern, msg_lower)
            if match:
                name = match.group(1).strip()
                name = re.sub(r'\b(my|mera|meri|mujhe|batao|sunao|janna|jaanna|kya|hai|ho|bata|bolo|do|kare)\b', '', name).strip()
                name = name.strip('?!,. ')
                if name and len(name) > 1:
                    break
                name = None

        if name and len(name) > 1:
            meaning = get_name_meaning(name)
            if meaning:
                return f'"{name.capitalize()}" ka matlab hai "{meaning["meaning"]}" ({meaning["origin"]})'
            else:
                return f'Mujhe "{name}" ka meaning nahi pata. Par naam bahut achha hai!'

        return "Kis naam ka matlab jaanna hai? Batao naam!"

    def _handle_would_you(self) -> str:
        q = get_would_you_rather()
        return f"Would you rather:\n\nA) {q['option_a']}\n\nB) {q['option_b']}\n\nKya choose karoge? A ya B?"

    def _handle_truth_lie(self) -> str:
        game = get_two_truths_lie()
        lie_letter = game["lie"].upper()
        return (
            f"Two Truths and a Lie!\n\n"
            f"A) {game['statement_a']}\n"
            f"B) {game['statement_b']}\n"
            f"C) {game['statement_c']}\n\n"
            f"Ek lie hai! Kya hai? A, B, ya C?"
        )

    def _handle_time(self) -> str:
        now = datetime.now()
        time_str = now.strftime("%I:%M %p")
        responses = [
            f"Abhi {time_str} hai! Kuch kaam hai kya?",
            f"Current time: {time_str}. Bolo kya karna hai?",
            f"{time_str} ho rahe hain! Kya plan hai?",
            f"Ghadi dekho, {time_str} hai! Ab batao?",
        ]
        return random.choice(responses)

    def _handle_date(self) -> str:
        now = datetime.now()
        date_str = now.strftime("%d %B %Y")
        responses = [
            f"Aaj {date_str} hai! Koi special din hai kya?",
            f"Date: {date_str}. Bolo kya karein aaj?",
            f"{date_str} - aaj ka din! Kya plan hai?",
            f"Aaj {date_str} hai! Kuch special plan hai?",
        ]
        return random.choice(responses)

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
            "daily_fact": "neutral",
            "quote": "thinking",
            "tongue_twister": "happy",
            "name_meaning": "neutral",
            "would_you": "happy",
            "truth_lie": "happy",
            "affirmation": "happy",
            "unknown": "confused",
        }
        return emotion_map.get(intent, "neutral")
