import json
from datetime import datetime
from .database import get_db
from .encryption import encryption


class GDPREngine:
    def __init__(self):
        self._init_tables()

    def _init_tables(self):
        conn = get_db()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS gdpr_consents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                consent_type TEXT NOT NULL,
                granted INTEGER NOT NULL,
                ip_address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS data_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                request_type TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()

    def record_consent(self, user_id: str, consent_type: str, granted: bool,
                       ip_address: str = None) -> dict:
        conn = get_db()
        conn.execute("""
            INSERT INTO gdpr_consents (user_id, consent_type, granted, ip_address)
            VALUES (?, ?, ?, ?)
        """, (user_id, consent_type, 1 if granted else 0, ip_address))
        conn.commit()
        conn.close()
        return {"user_id": user_id, "consent": consent_type, "granted": granted}

    def get_consents(self, user_id: str) -> dict:
        conn = get_db()
        rows = conn.execute(
            "SELECT consent_type, granted, created_at FROM gdpr_consents WHERE user_id=? ORDER BY created_at DESC",
            (user_id,)
        ).fetchall()
        conn.close()

        consents = {}
        for r in rows:
            if r["consent_type"] not in consents:
                consents[r["consent_type"]] = {
                    "granted": bool(r["granted"]),
                    "last_updated": r["created_at"],
                }

        return consents

    def export_user_data(self, user_id: str) -> dict:
        conn = get_db()

        user = conn.execute(
            "SELECT * FROM users WHERE user_id=?", (user_id,)
        ).fetchone()

        messages = conn.execute(
            "SELECT * FROM messages WHERE user_id=?", (user_id,)
        ).fetchall()

        memories = conn.execute(
            "SELECT * FROM memories WHERE user_id=?", (user_id,)
        ).fetchall()

        facts = conn.execute(
            "SELECT * FROM personal_facts WHERE user_id=?", (user_id,)
        ).fetchall()

        preferences = conn.execute(
            "SELECT * FROM user_preferences WHERE user_id=?", (user_id,)
        ).fetchall()

        consents = conn.execute(
            "SELECT * FROM gdpr_consents WHERE user_id=?", (user_id,)
        ).fetchall()

        events = conn.execute(
            "SELECT * FROM analytics_events WHERE user_id=?", (user_id,)
        ).fetchall()

        conn.close()

        export_data = {
            "export_date": datetime.now().isoformat(),
            "user_id": user_id,
            "profile": dict(user) if user else None,
            "messages": [dict(m) for m in messages],
            "memories": [dict(m) for m in memories],
            "personal_facts": [dict(f) for f in facts],
            "preferences": [dict(p) for p in preferences],
            "consents": [dict(c) for c in consents],
            "analytics_events": [dict(e) for e in events],
            "total_records": {
                "messages": len(messages),
                "memories": len(memories),
                "facts": len(facts),
                "preferences": len(preferences),
            },
        }

        return export_data

    def delete_user_data(self, user_id: str, confirm: bool = False) -> dict:
        if not confirm:
            return {"error": "Confirmation required. Set confirm=True to delete all data."}

        conn = get_db()
        deleted = {
            "messages": conn.execute("DELETE FROM messages WHERE user_id=?", (user_id,)).rowcount,
            "memories": conn.execute("DELETE FROM memories WHERE user_id=?", (user_id,)).rowcount,
            "facts": conn.execute("DELETE FROM personal_facts WHERE user_id=?", (user_id,)).rowcount,
            "preferences": conn.execute("DELETE FROM user_preferences WHERE user_id=?", (user_id,)).rowcount,
            "analytics": conn.execute("DELETE FROM analytics_events WHERE user_id=?", (user_id,)).rowcount,
            "context": conn.execute("DELETE FROM conversation_context WHERE user_id=?", (user_id,)).rowcount,
        }
        conn.commit()
        conn.close()

        return {
            "user_id": user_id,
            "deleted": deleted,
            "total_deleted": sum(deleted.values()),
            "message": "All user data has been permanently deleted.",
        }

    def anonymize_user_data(self, user_id: str) -> dict:
        anon_id = encryption.hash_data(user_id)[:12]

        conn = get_db()
        conn.execute("UPDATE messages SET user_id=? WHERE user_id=?", (anon_id, user_id))
        conn.execute("UPDATE memories SET user_id=? WHERE user_id=?", (anon_id, user_id))
        conn.execute("UPDATE personal_facts SET user_id=? WHERE user_id=?", (anon_id, user_id))
        conn.execute("UPDATE user_preferences SET user_id=? WHERE user_id=?", (anon_id, user_id))
        conn.execute("UPDATE analytics_events SET user_id=? WHERE user_id=?", (anon_id, user_id))
        conn.commit()
        conn.close()

        return {
            "original_user_id": user_id,
            "anonymized_id": anon_id,
            "message": "User data has been anonymized.",
        }

    def get_privacy_policy(self) -> dict:
        return {
            "version": "1.0",
            "last_updated": "2024-01-01",
            "sections": [
                {
                    "title": "Data Collection",
                    "content": "We collect chat messages, user preferences, and usage analytics to improve our service.",
                },
                {
                    "title": "Data Usage",
                    "content": "Your data is used to provide personalized responses and improve AI accuracy.",
                },
                {
                    "title": "Data Sharing",
                    "content": "We do not share your personal data with third parties.",
                },
                {
                    "title": "Data Security",
                    "content": "All data is encrypted and stored securely.",
                },
                {
                    "title": "Your Rights",
                    "content": "You can export or delete your data at any time.",
                },
            ],
        }


gdpr = GDPREngine()
