import random
import re
import uuid
from datetime import datetime
from .nlp import preprocess, tokenize, extract_name, detect_emotion_intensity
from .intents import classify_intent
from .responses import get_response
from .context import SessionManager
from .memory import MemorySystem
from .context_engine import ContextEngine
from .personality import PersonalityEngine
from .emotion_detector import EmotionDetector
from .plugins import PluginManager
from .knowledge import KnowledgeSystem
from .search import SearchEngine
from .analytics import Analytics
from .facts import get_random_fact
from .quotes import get_random_quote
from .games import get_would_you_rather, get_two_truths_lie, get_tongue_twister
from .names import get_name_meaning
from .calculator import calculate, solve_math
from .translator import translate
from .mobile import detect_mobile_command
from .database import save_user, update_user, save_message, get_messages, get_user_stats


class ChatEngine:
    def __init__(self):
        self.sessions = SessionManager(max_sessions=1000, ttl_seconds=7200)
        self.memory = MemorySystem()
        self.context_engine = ContextEngine()
        self.personality = PersonalityEngine()
        self.emotion_detector = EmotionDetector()
        self.plugin_manager = PluginManager()
        self.knowledge = KnowledgeSystem()
        self.search = SearchEngine()
        self.analytics = Analytics()
        self._register_plugins()

    def _register_plugins(self):
        try:
            from .plugins.weather import WeatherPlugin
            from .plugins.news import NewsPlugin
            from .plugins.notes import NotesPlugin
            from .plugins.todo import TodoPlugin
            from .plugins.reminders import RemindersPlugin
            from .plugins.currency import CurrencyPlugin
            from .plugins.unit_converter import UnitConverterPlugin
            from .plugins.password_gen import PasswordGenPlugin
            from .plugins.qr_code import QRCodePlugin
            from .plugins.navigation import NavigationPlugin
            from .plugins.music import MusicPlugin
            from .plugins.email_plugin import EmailPlugin
            from .plugins.dictionary import DictionaryPlugin

            for plugin_class in [
                WeatherPlugin, NewsPlugin, NotesPlugin, TodoPlugin,
                RemindersPlugin, CurrencyPlugin, UnitConverterPlugin,
                PasswordGenPlugin, QRCodePlugin, NavigationPlugin,
                MusicPlugin, EmailPlugin, DictionaryPlugin,
            ]:
                self.plugin_manager.register(plugin_class())
        except Exception:
            pass

    def chat(self, user_id: str, message: str) -> dict:
        start_time = datetime.now()

        session = self.sessions.get_session(user_id)
        save_user(user_id, session.user_name)

        intent = classify_intent(message)

        user_name = session.user_name
        if intent == "user_name":
            extracted = extract_name(message)
            if extracted:
                session.user_name = extracted
                user_name = extracted
                update_user(user_id, name=extracted)
                self.memory.add_personal_fact(user_id, f"User's name is {extracted}", "identity")

        user_mood = self.emotion_detector.detect_from_text(message)
        time_context = self._get_time_context()

        self.context_engine.update_context(user_id, message, intent)
        ctx = self.context_engine.get_context(user_id)

        plugin_result = self.plugin_manager.execute_by_intent(intent, user_id, message, ctx)
        if plugin_result and "response" in plugin_result:
            response = plugin_result["response"]
            command = plugin_result.get("command")
        else:
            response, command = self._generate_response(
                intent, message, session, user_name, time_context, user_mood, ctx
            )

        personality_ctx = self.personality.get_personality_context(
            user_mood["emotion"], time_context
        )
        response = self.personality.adapt_response(response, user_mood["emotion"], ctx)

        session.add_used_response(response)
        assistant_emotion = self._detect_emotion(intent, user_mood)

        session.add_message("user", message, intent=intent, emotion=user_mood["emotion"])
        session.add_message("assistant", response, intent=intent, emotion=assistant_emotion)

        save_message(user_id, "user", message, intent=intent, emotion=user_mood["emotion"])
        save_message(user_id, "assistant", response, intent=intent, emotion=assistant_emotion)
        update_user(user_id, increment_messages=True)

        importance = self._calculate_importance(intent, user_mood)
        self.memory.add_memory(user_id, "short_term", f"User: {message}", importance=importance)

        if intent == "user_name" and user_name:
            self.memory.set_preference(user_id, "name", user_name)

        self.analytics.track_event("chat", user_id, {"intent": intent, "emotion": user_mood["emotion"]})

        duration = (datetime.now() - start_time).total_seconds()
        self.analytics.track_api_call("/chat", "POST", 200, duration * 1000, user_id)

        result = {
            "response": response,
            "intent": intent,
            "emotion": assistant_emotion,
            "user_mood": user_mood["emotion"],
            "mood_intensity": user_mood["intensity"],
            "context": {
                "topic": ctx.get("current_topic"),
                "state": ctx.get("state"),
                "turn_count": ctx.get("turn_count", 0),
            },
        }

        if command:
            result["command"] = command

        return result

    def chat_with_history(self, user_id: str, message: str) -> dict:
        history = get_messages(user_id, limit=10)
        context_str = "\n".join([
            f"{'User' if m['role'] == 'user' else 'Mahi'}: {m['content']}"
            for m in history
        ])
        return self.chat(user_id, message)

    def search_knowledge(self, user_id: str, query: str) -> dict:
        results = self.knowledge.search(user_id, query)
        if results:
            best = results[0]["content"]
            return {"found": True, "answer": best, "source": "knowledge"}
        web_results = self.search.search(query)
        if web_results["results"]:
            return {"found": True, "answer": web_results["results"][0].get("snippet", ""), "source": "web"}
        return {"found": False, "answer": "", "source": "none"}

    def clear_session(self, user_id: str) -> bool:
        self.context_engine.clear_context(user_id)
        return self.sessions.delete_session(user_id)

    def get_memory(self, user_id: str) -> dict:
        return {
            "memories": self.memory.get_memories(user_id, limit=20),
            "facts": self.memory.get_personal_facts(user_id),
            "preferences": self.memory.get_all_preferences(user_id),
            "summary": self.memory.summarize_memory(user_id),
        }

    def add_memory(self, user_id: str, content: str, memory_type: str = "short_term",
                   importance: float = 0.5) -> bool:
        self.memory.add_memory(user_id, memory_type, content, importance)
        return True

    def search_memory(self, user_id: str, query: str) -> list[dict]:
        return self.memory.search_memory(user_id, query)

    def get_context(self, user_id: str) -> dict:
        return self.context_engine.get_context(user_id)

    def get_analytics(self) -> dict:
        return self.analytics.get_dashboard()

    def list_plugins(self) -> list[dict]:
        return self.plugin_manager.list_plugins()

    def execute_plugin(self, name: str, user_id: str, message: str) -> dict | None:
        ctx = self.context_engine.get_context(user_id)
        return self.plugin_manager.execute(name, user_id, message, ctx)

    def _generate_response(self, intent, message, session, user_name, time_context, user_mood, ctx):
        if intent == "daily_fact":
            return self._handle_fact(message), None
        elif intent == "quote":
            return self._handle_quote(message), None
        elif intent == "tongue_twister":
            return self._handle_tongue_twister(message), None
        elif intent == "name_meaning":
            return self._handle_name_meaning(message), None
        elif intent == "would_you":
            return self._handle_would_you(), None
        elif intent == "truth_lie":
            return self._handle_truth_lie(), None
        elif intent == "time":
            return self._handle_time(), None
        elif intent == "date":
            return self._handle_date(), None
        elif intent == "calculator":
            return self._handle_calculator(message), None
        elif intent == "translator":
            return self._handle_translator(message), None
        elif intent == "mobile_command":
            cmd = detect_mobile_command(message)
            return self._handle_mobile_command(message), cmd
        elif intent == "search":
            return self._handle_search(message), None
        elif intent == "knowledge":
            return self._handle_knowledge(user_name, message), None

        return get_response(
            intent,
            user_name=user_name,
            time_context=time_context,
            user_mood=user_mood["emotion"],
            used_responses=session.used_responses,
        ), None

    def _handle_fact(self, message):
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

    def _handle_quote(self, message):
        categories = ["inspirational", "life", "friendship", "funny", "motivation"]
        msg_lower = message.lower()
        selected_cat = None
        for cat in categories:
            if cat in msg_lower or (cat == "motivation" and "motiv" in msg_lower):
                selected_cat = cat
                break
        quote = get_random_quote(selected_cat)
        return f'"{quote["text"]}" - {quote["author"]}'

    def _handle_tongue_twister(self, message):
        msg_lower = message.lower()
        lang = "english" if "english" in msg_lower else "hindi"
        twister = get_tongue_twister(lang)
        intro = random.choice(["Try this: ", "Tongue twister: ", "Ab bolo ye: ", "Challenge: "])
        return f"{intro}{twister}"

    def _handle_name_meaning(self, message):
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

    def _handle_would_you(self):
        q = get_would_you_rather()
        return f"Would you rather:\n\nA) {q['option_a']}\n\nB) {q['option_b']}\n\nKya choose karoge? A ya B?"

    def _handle_truth_lie(self):
        game = get_two_truths_lie()
        return (
            f"Two Truths and a Lie!\n\n"
            f"A) {game['statement_a']}\n"
            f"B) {game['statement_b']}\n"
            f"C) {game['statement_c']}\n\n"
            f"Ek lie hai! Kya hai? A, B, ya C?"
        )

    def _handle_time(self):
        now = datetime.now()
        time_str = now.strftime("%I:%M %p")
        responses = [
            f"Abhi {time_str} hai! Kuch kaam hai kya?",
            f"Current time: {time_str}. Bolo kya karna hai?",
            f"{time_str} ho rahe hain! Kya plan hai?",
        ]
        return random.choice(responses)

    def _handle_date(self):
        now = datetime.now()
        date_str = now.strftime("%d %B %Y")
        responses = [
            f"Aaj {date_str} hai! Koi special din hai kya?",
            f"Date: {date_str}. Bolo kya karein aaj?",
            f"{date_str} - aaj ka din! Kya plan hai?",
        ]
        return random.choice(responses)

    def _handle_calculator(self, message):
        msg = message.lower()
        msg = re.sub(r'(calculate|calc|solve|kitna hota hai|batao kitna|jod ke batao|karo|hai|ho|hain|batao)', '', msg).strip()
        math_result = solve_math(msg)
        if math_result:
            return math_result
        calc_result = calculate(msg)
        if calc_result:
            return f"Answer: {calc_result['expression']} = {calc_result['result']}"
        nums = re.findall(r'[\d.]+', msg)
        if len(nums) >= 2:
            a, b = float(nums[0]), float(nums[1])
            if '+' in msg or 'jod' in msg or 'plus' in msg:
                return f"{int(a)} + {int(b)} = {int(a + b)}"
            elif '-' in msg or 'minus' in msg:
                return f"{int(a)} - {int(b)} = {int(a - b)}"
            elif '*' in msg or 'x' in msg or 'guna' in msg or 'into' in msg:
                return f"{int(a)} x {int(b)} = {int(a * b)}"
            elif '/' in msg or 'bhaag' in msg or 'divided' in msg:
                if b == 0:
                    return "Zero se divide nahi ho sakta!"
                return f"{int(a)} / {int(b)} = {a / b:.2f}"
        return "Kya calculate karna hai? Jaise: '5 + 3' ya '100 * 5'"

    def _handle_translator(self, message):
        msg = message.lower()
        msg = re.sub(r'(translate|anuvaad|tarjuma|karo|mein|bolo)', '', msg).strip()
        if not msg:
            return "Kya translate karna hai? Bolo word ya sentence!"
        result = translate(msg)
        if result:
            return f"{result['direction']}: \"{result['original']}\" -> \"{result['translated']}\""
        return f"Mujhe \"{msg}\" translate karna nahi aata. Par koshish karunga next time!"

    def _handle_mobile_command(self, message):
        command = detect_mobile_command(message)
        if command:
            return command["response"]
        return "Kya karna hai? Batao command!"

    def _handle_search(self, message):
        query = re.sub(r'(search|dhundh|khoj|google)', '', message, flags=re.IGNORECASE).strip()
        if not query:
            return "Kya search karna hai? Batao!"
        results = self.search.search(query)
        if results["results"]:
            top = results["results"][0]
            return f"Mujhe ye mila: {top.get('snippet', '')[:200]}"
        return f"Mujhe \"{query}\" ke baare mein info nahi mili."

    def _handle_knowledge(self, user_name, message):
        name_str = f"{user_name}!" if user_name else "!"
        return f"Bilkul bataungi{name_str} Kya topic hai?"

    def _get_time_context(self):
        hour = datetime.now().hour
        if 5 <= hour < 12:
            return "morning"
        elif 12 <= hour < 17:
            return "afternoon"
        elif 17 <= hour < 21:
            return "evening"
        else:
            return "night"

    def _detect_emotion(self, intent, user_mood):
        if user_mood["intensity"] == "high":
            if user_mood["emotion"] in ("happy", "energetic", "excited"):
                return "happy"
            elif user_mood["emotion"] in ("sad", "frustrated"):
                return "sad"
        emotion_map = {
            "greeting": "happy", "identity": "neutral", "user_name": "happy",
            "how_are_you": "neutral", "emotion_happy": "happy", "emotion_sad": "sad",
            "emotion_angry": "angry", "emotion_bored": "bored", "compliment": "happy",
            "thanks": "happy", "joke": "happy", "motivation": "energetic",
            "health": "concerned", "time": "neutral", "date": "neutral",
            "weather": "neutral", "love": "happy", "purpose": "neutral",
            "capability": "neutral", "bye": "sad", "life": "thinking",
            "knowledge": "neutral", "tech": "neutral", "music": "happy",
            "food": "happy", "fear": "concerned", "insult": "sad",
            "celebration": "happy", "gossip": "neutral", "advice": "thinking",
            "frustration": "concerned", "confusion": "confused", "story": "neutral",
            "riddle": "happy", "miss_you": "happy", "sleepy": "neutral",
            "morning": "happy", "daily_fact": "neutral", "quote": "thinking",
            "tongue_twister": "happy", "name_meaning": "neutral", "would_you": "happy",
            "truth_lie": "happy", "affirmation": "happy", "calculator": "neutral",
            "translator": "neutral", "mobile_command": "neutral",
            "search": "neutral", "unknown": "confused",
        }
        return emotion_map.get(intent, "neutral")

    def _calculate_importance(self, intent, user_mood):
        high_importance = ["user_name", "advice", "health", "life"]
        medium_importance = ["knowledge", "calculator", "search", "mobile_command"]
        if intent in high_importance:
            return 0.8
        if intent in medium_importance:
            return 0.6
        if user_mood.get("intensity") == "high":
            return 0.7
        return 0.3
