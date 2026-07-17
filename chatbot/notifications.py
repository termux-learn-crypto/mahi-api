import json
from datetime import datetime
from .database import get_db


class NotificationEngine:
    def __init__(self):
        self._init_tables()
        self.fcm_server_key = None

    def _init_tables(self):
        conn = get_db()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS notification_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                platform TEXT NOT NULL,
                token TEXT NOT NULL,
                active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, platform)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS notification_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                title TEXT NOT NULL,
                body TEXT NOT NULL,
                data TEXT,
                status TEXT DEFAULT 'sent',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()

    def register_token(self, user_id: str, platform: str, token: str) -> dict:
        conn = get_db()
        conn.execute("""
            INSERT OR REPLACE INTO notification_tokens (user_id, platform, token, active)
            VALUES (?, ?, ?, 1)
        """, (user_id, platform, token))
        conn.commit()
        conn.close()
        return {"registered": True, "user_id": user_id, "platform": platform}

    def unregister_token(self, user_id: str, platform: str = None) -> dict:
        conn = get_db()
        if platform:
            conn.execute(
                "UPDATE notification_tokens SET active=0 WHERE user_id=? AND platform=?",
                (user_id, platform)
            )
        else:
            conn.execute(
                "UPDATE notification_tokens SET active=0 WHERE user_id=?",
                (user_id,)
            )
        conn.commit()
        conn.close()
        return {"unregistered": True, "user_id": user_id}

    def send_notification(self, user_id: str, title: str, body: str,
                         data: dict = None) -> dict:
        conn = get_db()
        tokens = conn.execute(
            "SELECT platform, token FROM notification_tokens WHERE user_id=? AND active=1",
            (user_id,)
        ).fetchall()
        conn.close()

        if not tokens:
            return {"sent": False, "reason": "no_tokens"}

        sent_count = 0
        for t in tokens:
            success = self._send_fcm(t["token"], title, body, data)
            if success:
                sent_count += 1

        conn = get_db()
        conn.execute("""
            INSERT INTO notification_history (user_id, title, body, data, status)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, title, body, json.dumps(data) if data else None,
              "sent" if sent_count > 0 else "failed"))
        conn.commit()
        conn.close()

        return {"sent": sent_count > 0, "count": sent_count, "total_tokens": len(tokens)}

    def _send_fcm(self, token: str, title: str, body: str, data: dict = None) -> bool:
        if not self.fcm_server_key:
            return False

        try:
            import requests
            url = "https://fcm.googleapis.com/fcm/send"
            headers = {
                "Authorization": f"key={self.fcm_server_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "to": token,
                "notification": {"title": title, "body": body},
                "data": data or {},
            }
            resp = requests.post(url, headers=headers, json=payload, timeout=10)
            return resp.status_code == 200
        except Exception:
            return False

    def send_reminder(self, user_id: str, reminder_text: str, scheduled_time: str = None):
        return self.send_notification(
            user_id,
            "Reminder",
            reminder_text,
            {"type": "reminder", "scheduled": scheduled_time}
        )

    def send_daily_summary(self, user_id: str, summary: dict):
        body = f"Today: {summary.get('messages', 0)} messages, {summary.get('intents', 0)} tasks"
        return self.send_notification(user_id, "Daily Summary", body, summary)

    def get_notification_history(self, user_id: str, limit: int = 20) -> list[dict]:
        conn = get_db()
        rows = conn.execute("""
            SELECT title, body, status, created_at
            FROM notification_history WHERE user_id=?
            ORDER BY created_at DESC LIMIT ?
        """, (user_id, limit)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_user_tokens(self, user_id: str) -> list[dict]:
        conn = get_db()
        rows = conn.execute(
            "SELECT platform, active, created_at FROM notification_tokens WHERE user_id=?",
            (user_id,)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]


notifications = NotificationEngine()
