import re
from .nlp import detect_emotion_intensity


class EmotionDetector:
    EMOTIONS = {
        "happy": {
            "text_keywords": ["khush", "happy", "achha", "maza", "mast", "badhiya", "awesome", "great",
                              "nice", "amazing", "excellent", "wonderful", "yay", "wow", "love"],
            "voice_indicators": {"pitch": "high", "tempo": "fast", "volume": "medium-high"},
            "weight": 1.0,
        },
        "sad": {
            "text_keywords": ["sad", "dukhi", "dukh", "bura", "udas", "roya", "rona", "hurt",
                              "broken", "toota", "dil toota", "cry", "miss"],
            "voice_indicators": {"pitch": "low", "tempo": "slow", "volume": "low"},
            "weight": 1.0,
        },
        "angry": {
            "text_keywords": ["gussa", "angry", "irritate", "naraz", "krodh", "furious",
                              "hate", "stupid", "idiot"],
            "voice_indicators": {"pitch": "high", "tempo": "fast", "volume": "high"},
            "weight": 1.0,
        },
        "excited": {
            "text_keywords": ["excited", "josh", "waiting", "cant wait", "intezar", "party",
                              "celebration", "wow", "amazing"],
            "voice_indicators": {"pitch": "high", "tempo": "fast", "volume": "high"},
            "weight": 0.9,
        },
        "calm": {
            "text_keywords": ["calm", "shant", "relax", "chill", "theek hai", "koi baat nahi"],
            "voice_indicators": {"pitch": "medium", "tempo": "medium", "volume": "medium"},
            "weight": 0.8,
        },
        "stressed": {
            "text_keywords": ["stress", "tension", "pareshan", "pressure", "overwhelmed",
                              "thak gaya", "exhausted", "burnout"],
            "voice_indicators": {"pitch": "low", "tempo": "slow", "volume": "low-medium"},
            "weight": 0.9,
        },
        "frustrated": {
            "text_keywords": ["frustrated", "pareshan", "nahi ho raha", "tang", "mood off",
                              "irritated", "annoyned"],
            "voice_indicators": {"pitch": "medium-high", "tempo": "medium", "volume": "medium-high"},
            "weight": 0.9,
        },
        "confused": {
            "text_keywords": ["confuse", "samajh nahi", "pata nahi", "unclear", "doubt",
                              "kya", "kyun", "kaise"],
            "voice_indicators": {"pitch": "medium", "tempo": "medium", "volume": "medium"},
            "weight": 0.7,
        },
        "fearful": {
            "text_keywords": ["dar", "fear", "scared", "afraid", "terrified", "phobia"],
            "voice_indicators": {"pitch": "high", "tempo": "fast", "volume": "low"},
            "weight": 0.8,
        },
        "bored": {
            "text_keywords": ["bore", "boring", "alas", "khali", "free", "lonely", "akela"],
            "voice_indicators": {"pitch": "low", "tempo": "slow", "volume": "low"},
            "weight": 0.8,
        },
        "neutral": {
            "text_keywords": [],
            "voice_indicators": {"pitch": "medium", "tempo": "medium", "volume": "medium"},
            "weight": 0.5,
        },
    }

    def detect_from_text(self, text: str) -> dict:
        base_result = detect_emotion_intensity(text)

        text_lower = text.lower()
        scores = {}

        for emotion, config in self.EMOTIONS.items():
            score = 0
            for keyword in config["text_keywords"]:
                if keyword in text_lower:
                    score += 1
            scores[emotion] = score * config["weight"]

        if base_result["emotion"] != "neutral":
            scores[base_result["emotion"]] = scores.get(base_result["emotion"], 0) + 2

        caps_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)
        if caps_ratio > 0.5:
            scores["angry"] = scores.get("angry", 0) + 1
            scores["excited"] = scores.get("excited", 0) + 1

        exclamation_count = text.count("!")
        if exclamation_count >= 3:
            scores["excited"] = scores.get("excited", 0) + 2

        if "?" in text:
            scores["confused"] = scores.get("confused", 0) + 1

        if not scores or max(scores.values()) == 0:
            primary_emotion = "neutral"
        else:
            primary_emotion = max(scores, key=scores.get)

        intensity = base_result["intensity"]
        confidence = min(scores.get(primary_emotion, 0) / 5.0, 1.0)

        return {
            "emotion": primary_emotion,
            "intensity": intensity,
            "confidence": round(confidence, 2),
            "all_scores": {k: round(v, 2) for k, v in scores.items() if v > 0},
            "voice_indicators": self.EMOTIONS[primary_emotion]["voice_indicators"],
        }

    def detect_from_voice(self, pitch: float, tempo: float, volume: float) -> str:
        best_match = "neutral"
        best_score = 0

        for emotion, config in self.EMOTIONS.items():
            if emotion == "neutral":
                continue
            vi = config["voice_indicators"]
            score = 0

            pitch_map = {"low": 0.3, "medium": 0.5, "high": 0.8}
            tempo_map = {"slow": 0.3, "medium": 0.5, "fast": 0.8}
            volume_map = {"low": 0.3, "low-medium": 0.4, "medium": 0.5, "medium-high": 0.7, "high": 0.8}

            if abs(pitch - pitch_map.get(vi["pitch"], 0.5)) < 0.2:
                score += 1
            if abs(tempo - tempo_map.get(vi["tempo"], 0.5)) < 0.2:
                score += 1
            if abs(volume - volume_map.get(vi["volume"], 0.5)) < 0.2:
                score += 1

            if score > best_score:
                best_score = score
                best_match = emotion

        return best_match

    def get_emotion_response_hint(self, emotion: str) -> str:
        hints = {
            "happy": "User is happy. Match their energy, be enthusiastic.",
            "sad": "User is sad. Be empathetic, comforting, supportive.",
            "angry": "User is angry. Stay calm, acknowledge their frustration, help them.",
            "excited": "User is excited. Be equally enthusiastic, share their joy.",
            "calm": "User is calm. Keep conversation relaxed, natural.",
            "stressed": "User is stressed. Be supportive, offer help, suggest breaks.",
            "frustrated": "User is frustrated. Acknowledge their feelings, help solve the issue.",
            "confused": "User is confused. Explain clearly, be patient, use examples.",
            "fearful": "User is scared. Reassure them, be supportive, provide comfort.",
            "bored": "User is bored. Suggest something interesting, be engaging.",
            "neutral": "User is neutral. Be friendly, conversational.",
        }
        return hints.get(emotion, hints["neutral"])
