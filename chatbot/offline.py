import json
from datetime import datetime
from .database import get_db


class OfflineMode:
    def __init__(self):
        self._init_tables()
        self.offline_responses = {
            "greeting": "Hi! Main abhi offline hu. Internet aate hi reply dunga!",
            "farewell": "Bye! Jab online aaunga tab baat karte hain.",
            "how_are_you": "Main theek hu! Tumhara haal kaisa hai?",
            "thanks": "Welcome! Jab online honga tab aur help karunga.",
            "time": self._get_time,
            "date": self._get_date,
        }

    def _init_tables(self):
        conn = get_db()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS offline_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                message TEXT NOT NULL,
                intent TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed_at TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS offline_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                cache_key TEXT NOT NULL,
                cache_value TEXT,
                expires_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, cache_key)
            )
        """)
        conn.commit()
        conn.close()

    def handle_offline_message(self, user_id: str, message: str) -> dict:
        intent = self._detect_simple_intent(message)

        if intent in self.offline_responses:
            response = self.offline_responses[intent]
            if callable(response):
                response = response()

            return {
                "response": response,
                "intent": intent,
                "offline": True,
                "queued": False,
            }

        self._queue_message(user_id, message, intent)

        return {
            "response": "Main abhi offline mode mein hu. Tumhara message save ho gaya hai. Jab main online aaunga, tab reply dunga!",
            "intent": intent,
            "offline": True,
            "queued": True,
        }

    def _detect_simple_intent(self, message: str) -> str:
        msg_lower = message.lower()

        if any(w in msg_lower for w in ["hello", "hi", "hey", "namaste"]):
            return "greeting"
        elif any(w in msg_lower for w in ["bye", "alvida", "tata"]):
            return "farewell"
        elif any(w in msg_lower for w in ["kaise", "how are you", "haal"]):
            return "how_are_you"
        elif any(w in msg_lower for w in ["thanks", "shukriya", "dhanyavaad"]):
            return "thanks"
        elif any(w in msg_lower for w in ["time", "waqt", "baje"]):
            return "time"
        elif any(w in msg_lower for w in ["date", "tarikh", "aaj"]):
            return "date"
        return "unknown"

    def _get_time(self) -> str:
        from datetime import datetime
        return f"Abhi {datetime.now().strftime('%I:%M %p')} hai!"

    def _get_date(self) -> str:
        from datetime import datetime
        return f"Aaj {datetime.now().strftime('%d %B %Y')} hai!"

    def _queue_message(self, user_id: str, message: str, intent: str):
        conn = get_db()
        conn.execute("""
            INSERT INTO offline_queue (user_id, message, intent)
            VALUES (?, ?, ?)
        """, (user_id, message, intent))
        conn.commit()
        conn.close()

    def get_pending_messages(self, user_id: str = None) -> list[dict]:
        conn = get_db()
        if user_id:
            rows = conn.execute("""
                SELECT * FROM offline_queue WHERE user_id=? AND status='pending'
                ORDER BY created_at
            """, (user_id,)).fetchall()
        else:
            rows = conn.execute("""
                SELECT * FROM offline_queue WHERE status='pending'
                ORDER BY created_at LIMIT 100
            """).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def process_queue(self, user_id: str, process_func) -> dict:
        pending = self.get_pending_messages(user_id)
        processed = 0

        for msg in pending:
            try:
                result = process_func(user_id, msg["message"])
                conn = get_db()
                conn.execute("""
                    UPDATE offline_queue SET status='processed', processed_at=CURRENT_TIMESTAMP
                    WHERE id=?
                """, (msg["id"],))
                conn.commit()
                conn.close()
                processed += 1
            except Exception:
                pass

        return {"processed": processed, "remaining": len(pending) - processed}

    def cache_response(self, user_id: str, key: str, value: str, ttl_hours: int = 24):
        from datetime import timedelta
        expires = (datetime.now() + timedelta(hours=ttl_hours)).isoformat()
        conn = get_db()
        conn.execute("""
            INSERT OR REPLACE INTO offline_cache (user_id, cache_key, cache_value, expires_at)
            VALUES (?, ?, ?, ?)
        """, (user_id, key, value, expires))
        conn.commit()
        conn.close()

    def get_cached_response(self, user_id: str, key: str) -> str | None:
        conn = get_db()
        row = conn.execute("""
            SELECT cache_value, expires_at FROM offline_cache
            WHERE user_id=? AND cache_key=?
        """, (user_id, key)).fetchone()
        conn.close()

        if row:
            from datetime import datetime
            try:
                expires = datetime.fromisoformat(row["expires_at"])
                if datetime.now() < expires:
                    return row["cache_value"]
            except (ValueError, TypeError):
                pass
        return None

    def get_offline_stats(self) -> dict:
        conn = get_db()
        pending = conn.execute(
            "SELECT COUNT(*) as c FROM offline_queue WHERE status='pending'"
        ).fetchone()["c"]
        processed = conn.execute(
            "SELECT COUNT(*) as c FROM offline_queue WHERE status='processed'"
        ).fetchone()["c"]
        conn.close()
        return {"pending": pending, "processed": processed}


offline = OfflineMode()
