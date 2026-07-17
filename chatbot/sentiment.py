import time
from datetime import datetime, timedelta
from collections import defaultdict
from .database import get_db


class SentimentAnalyzer:
    def __init__(self):
        self._init_tables()
        self.positive_words = set([
            "achha", "badhiya", "zabardast", "awesome", "great", "good", "nice",
            "happy", "khush", "mast", "excellent", "amazing", "wonderful",
            "fantastic", "brilliant", "superb", "perfect", "best", "love",
            "pyaar", "pasand", "thank", "shukriya", "dhanyavaad", "sukoon",
            "sahi", "theek", "ok", "okay", "haan", "yes", "bilkul", "sure",
            "pyaar", "mohabbat", "ishq", "dil", "sweet", "sundar", "sunder",
            "khushi", "josh", "utsah", "excited", "thrilled", "proud",
            "grateful", "blessed", "lucky", "confident", "strong",
        ])

        self.negative_words = set([
            "bura", "kharab", "ganda", "bad", "worst", "terrible", "awful",
            "sad", "dukh", "dard", "hate", "nafrat", "gussa", "angry",
            "frustrated", "pareshan", "tension", "stress", "anxious", "dar",
            "fear", "scared", "worried", "chinta", "depressed", "lonely",
            "akela", "bored", "thak", "tired", "exhausted", "confused",
            "lost", "broken", "hurt", "pain", "miss", "yaad", "rona",
            "cry", "weep", "problem", "issue", "trouble", "mushkil",
            "difficult", "impossible", "no", "nahi", "mat", "na",
        ])

        self.intensifiers = set([
            "bahut", "zyada", "bohot", "ekdum", "bilkul", "totally",
            "very", "really", "extremely", "absolutely", "completely",
            "seriously", "seriously", "issa", "itna", "so", "too",
        ])

        self.negators = set([
            "nahi", "na", "mat", "not", "never", "no", "bina", "without",
            "nahin", "naa",
        ])

    def _init_tables(self):
        conn = get_db()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sentiment_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                text TEXT,
                sentiment_score REAL,
                sentiment_label TEXT,
                positive_count INTEGER,
                negative_count INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_sentiment_user
            ON sentiment_history(user_id, created_at)
        """)
        conn.commit()
        conn.close()

    def analyze(self, text: str) -> dict:
        text_lower = text.lower()
        words = text_lower.split()

        pos_count = 0
        neg_count = 0
        has_negator = False

        for i, word in enumerate(words):
            if word in self.negators:
                has_negator = True
                continue

            if word in self.positive_words:
                if has_negator:
                    neg_count += 1
                else:
                    pos_count += 1
                has_negator = False

            elif word in self.negative_words:
                if has_negator:
                    pos_count += 1
                else:
                    neg_count += 1
                has_negator = False

            elif word in self.intensifiers:
                continue

        total = pos_count + neg_count
        if total == 0:
            score = 0.0
            label = "neutral"
        else:
            score = (pos_count - neg_count) / total
            if score > 0.2:
                label = "positive"
            elif score < -0.2:
                label = "negative"
            else:
                label = "neutral"

        return {
            "score": round(score, 3),
            "label": label,
            "positive_count": pos_count,
            "negative_count": neg_count,
            "confidence": min(1.0, total * 0.2),
        }

    def analyze_with_history(self, user_id: str, text: str) -> dict:
        result = self.analyze(text)

        self._save_sentiment(user_id, text, result)

        trend = self.get_trend(user_id, hours=24)
        result["trend"] = trend

        result["overall_mood"] = self._calculate_overall_mood(user_id)

        return result

    def _save_sentiment(self, user_id: str, text: str, sentiment: dict):
        conn = get_db()
        conn.execute("""
            INSERT INTO sentiment_history (user_id, text, sentiment_score, sentiment_label,
                                          positive_count, negative_count)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, text[:500], sentiment["score"], sentiment["label"],
              sentiment["positive_count"], sentiment["negative_count"]))
        conn.commit()
        conn.close()

    def get_trend(self, user_id: str, hours: int = 24) -> dict:
        conn = get_db()
        cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()

        rows = conn.execute("""
            SELECT sentiment_score, sentiment_label, created_at
            FROM sentiment_history
            WHERE user_id = ? AND created_at > ?
            ORDER BY created_at
        """, (user_id, cutoff)).fetchall()
        conn.close()

        if not rows:
            return {
                "direction": "stable",
                "avg_score": 0,
                "data_points": 0,
                "history": [],
            }

        scores = [r["sentiment_score"] for r in rows]
        avg_score = sum(scores) / len(scores)

        if len(scores) >= 2:
            first_half = scores[:len(scores)//2]
            second_half = scores[len(scores)//2:]
            first_avg = sum(first_half) / len(first_half)
            second_avg = sum(second_half) / len(second_half)

            diff = second_avg - first_avg
            if diff > 0.15:
                direction = "improving"
            elif diff < -0.15:
                direction = "declining"
            else:
                direction = "stable"
        else:
            direction = "stable"

        return {
            "direction": direction,
            "avg_score": round(avg_score, 3),
            "min_score": round(min(scores), 3),
            "max_score": round(max(scores), 3),
            "data_points": len(scores),
            "history": [
                {"score": r["sentiment_score"], "label": r["sentiment_label"], "time": r["created_at"]}
                for r in rows[-10:]
            ],
        }

    def _calculate_overall_mood(self, user_id: str) -> str:
        trend = self.get_trend(user_id, hours=48)
        avg = trend["avg_score"]

        if avg > 0.3:
            return "happy"
        elif avg > 0.1:
            return "content"
        elif avg > -0.1:
            return "neutral"
        elif avg > -0.3:
            return "down"
        else:
            return "unhappy"

    def get_mood_pattern(self, user_id: str) -> dict:
        conn = get_db()
        rows = conn.execute("""
            SELECT strftime('%H', created_at) as hour,
                   AVG(sentiment_score) as avg_score,
                   COUNT(*) as count
            FROM sentiment_history
            WHERE user_id = ?
            GROUP BY hour
            ORDER BY hour
        """, (user_id,)).fetchall()
        conn.close()

        hourly = {}
        for r in rows:
            hourly[r["hour"]] = {
                "avg_score": round(r["avg_score"], 3),
                "sample_count": r["count"],
            }

        best_hour = max(hourly.items(), key=lambda x: x[1]["avg_score"])[0] if hourly else None
        worst_hour = min(hourly.items(), key=lambda x: x[1]["avg_score"])[0] if hourly else None

        return {
            "hourly_pattern": hourly,
            "best_hour": best_hour,
            "worst_hour": worst_hour,
            "total_samples": sum(r["count"] for r in rows),
        }


sentiment_analyzer = SentimentAnalyzer()
