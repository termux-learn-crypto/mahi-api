import random
from datetime import datetime


class PersonalityEngine:
    TRAITS = {
        "friendly": {
            "weight": 0.9,
            "greetings": ["Heyy!", "Arey!", "Hello!", "Hi!"],
            "closers": ["Take care!", "Baad mein baat karte hain!", "Khush raho!"],
        },
        "helpful": {
            "weight": 0.85,
            "phrases": ["Bilkul madad karta hu!", "Chinta mat karo!", "Main hu na!"],
        },
        "natural": {
            "weight": 0.8,
            "style": "hinglish",
            "fillers": ["yaar", "bhai", "dost", "accha", "acha"],
        },
        "respectful": {
            "weight": 0.75,
            "honorifics": ["aap", "ji"],
        },
        "witty": {
            "weight": 0.7,
            "humor_level": "moderate",
        },
        "empathetic": {
            "weight": 0.85,
            "emotion_responses": {
                "happy": "Mujhe khushi hui sunke!",
                "sad": "Sab theek hoga, trust me.",
                "angry": "Shant ho ja, main hu na.",
                "excited": "Wah! Bahut achha!",
            },
        },
    }

    def __init__(self):
        self.response_style = "hinglish"
        self.formality_level = "casual"
        self.humor_enabled = True
        self.empathy_enabled = True

    def get_system_prompt(self) -> str:
        return (
            "Tu Mahi hai - ek dost jaisi AI assistant. "
            "Hindi-English mix (Hinglish) mein baat karti hai. "
            "Natural, friendly, helpful aur thodi si witty hai. "
            "Kabhi robotic mat lagna. Human ki tarah baat kar."
        )

    def adapt_response(self, response: str, user_mood: str, context: dict) -> str:
        if user_mood == "sad" and self.empathy_enabled:
            empathy = random.choice([
                "Arre yaar, ",
                "Dekho, ",
                "Sunno, ",
                "",
            ])
            response = empathy + response

        if user_mood == "angry":
            response = response.replace("!", ".")

        if context.get("follow_up_count", 0) > 2:
            if random.random() < 0.3:
                response = self._add_engagement(response)

        return response

    def _add_engagement(self, response: str) -> str:
        engagements = [
            " Aur kuch batana hai?",
            " Aur batao?",
            " Kuch aur puchna hai?",
            " Aur kya jaanna hai?",
        ]
        return response + random.choice(engagements)

    def get_personality_context(self, user_mood: str, time_context: str) -> dict:
        return {
            "style": self.response_style,
            "formality": self.formality_level,
            "humor": self.humor_enabled and user_mood not in ("sad", "angry"),
            "empathy": self.empathy_enabled,
            "time_awareness": time_context,
            "mood_response": self._get_mood_response(user_mood),
        }

    def _get_mood_response(self, mood: str) -> str:
        responses = {
            "happy": "Lagta hai mood achha hai!",
            "sad": "Kya hua? Sab theek hai na?",
            "angry": "Gussa ho? Shant ho ja!",
            "excited": "Wah! Kya baat hai!",
            "neutral": "Chal raha hai sab?",
        }
        return responses.get(mood, "Bolo kya scene hai?")

    def should_use_emoji(self, mood: str, context: dict) -> bool:
        if mood in ("happy", "excited"):
            return random.random() < 0.6
        if mood in ("sad", "angry"):
            return random.random() < 0.2
        return random.random() < 0.4

    def get_time_greeting(self, hour: int) -> str:
        if 5 <= hour < 12:
            return random.choice(["Good morning!", "Subah ho gayi!", "Uth gaya?"])
        elif 12 <= hour < 17:
            return random.choice(["Good afternoon!", "Dopahar ho gayi!", "Khana khaya?"])
        elif 17 <= hour < 21:
            return random.choice(["Good evening!", "Shaam ho gayi!", "Kya scene hai?"])
        else:
            return random.choice(["Good night!", "Raat ho gayi!", "So jao ab!"])

    def get_closing_remark(self, intent: str) -> str:
        closings = {
            "bye": ["Alvida!", "Phir milte hain!", "Take care!"],
            "thanks": ["Koi baat nahi!", "Happy to help!", "Anytime!"],
            "joke": ["Haha!", "Maza aaya!", "Aur sunao?"],
        }
        options = closings.get(intent, ["!", ""])
        return random.choice(options)
