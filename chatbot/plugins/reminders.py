import re
from datetime import datetime, timedelta
from . import Plugin
from ..database import get_db


class RemindersPlugin(Plugin):
    TIME_PATTERNS = [
        (r'(\d+)\s*(?:min|minute)', 'minutes'),
        (r'(\d+)\s*(?:hr|hour|ghante|ghanta)', 'hours'),
        (r'(\d+)\s*(?:day|din)', 'days'),
        (r'(\d+)\s*(?:sec|second)', 'seconds'),
    ]

    def __init__(self):
        super().__init__(
            name="reminders",
            description="Set reminders with time, list and cancel reminders with Android alarm support",
            version="1.0.0",
        )
        self.commands = ["remind", "reminder", "yaad dilana", "set reminder", "alarm"]
        self.keywords = [
            "remind", "reminder", "yaad", "dilana", "alarm", "alert",
            "notification", "set reminder", "remind me",
        ]

    def can_handle(self, intent: str, message: str) -> bool:
        if intent in ("reminder", "set_reminder"):
            return True
        msg = message.lower()
        return any(kw in msg for kw in self.keywords)

    def execute(self, user_id: str, message: str, context: dict) -> dict:
        msg = message.strip()
        conn = get_db()

        try:
            if re.search(r'\b(list|dikhao|sab|meri|show|all)\b.*\b(reminder|yaad)\b', msg, re.I) or \
               re.search(r'\b(reminder|yaad)\b.*\b(list|dikhao|sab|meri|show|all)\b', msg, re.I):
                return self._list_reminders(conn, user_id)
            if re.search(r'\b(cancel|hatao|delete|remove|mita)\b.*\b(reminder|yaad)\b', msg, re.I) or \
               re.search(r'\b(reminder|yaad)\b.*\b(cancel|hatao|delete|remove|mita)\b', msg, re.I):
                return self._cancel_reminder(conn, user_id, msg)
            return self._set_reminder(conn, user_id, msg)
        finally:
            conn.close()

    def _init_table(self, conn):
        conn.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                message TEXT NOT NULL,
                remind_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                active INTEGER DEFAULT 1
            )
        """)
        conn.commit()

    def _set_reminder(self, conn, user_id: str, message: str) -> dict:
        self._init_table(conn)
        time_delta = None
        for pattern, unit in self.TIME_PATTERNS:
            match = re.search(pattern, message, re.I)
            if match:
                amount = int(match.group(1))
                time_delta = timedelta(**{unit: amount})
                break

        if not time_delta:
            abs_match = re.search(
                r'(\d{1,2}):(\d{2})\s*(am|pm)?',
                message, re.I,
            )
            if abs_match:
                hour = int(abs_match.group(1))
                minute = int(abs_match.group(2))
                ampm = abs_match.group(3)
                if ampm:
                    if ampm.lower() == 'pm' and hour < 12:
                        hour += 12
                    elif ampm.lower() == 'am' and hour == 12:
                        hour = 0
                now = datetime.now()
                remind_at = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                if remind_at <= now:
                    remind_at += timedelta(days=1)
                time_delta = remind_at - now

        if not time_delta:
            return {
                "response": (
                    "⏰ Reminder set kaise karu?\n\n"
                    "Examples:\n"
                    "• 'remind me 30 min mein call karna'\n"
                    "• 'yaad dilana 2 ghante baad meeting hai'\n"
                    "• 'remind me 3:30 PM ko lunch'"
                ),
            }

        remind_at = datetime.now() + time_delta

        reminder_msg = re.sub(
            r'\b(remind|me|yaad|dilana|karna|set|after|baad|in|min|minute|hr|hour|ghante|ghanta|day|din|sec|second|alarm|notification)\b',
            '', message, flags=re.I
        ).strip()
        if not reminder_msg:
            reminder_msg = "Kuch karna tha!"

        cursor = conn.execute(
            "INSERT INTO reminders (user_id, message, remind_at) VALUES (?, ?, ?)",
            (user_id, reminder_msg, remind_at.isoformat()),
        )
        conn.commit()
        reminder_id = cursor.lastrowid

        time_str = remind_at.strftime("%I:%M %p, %d %b")
        readable_delta = self._readable_delta(time_delta)

        return {
            "response": (
                f"⏰ Reminder set ho gaya! (#{reminder_id})\n\n"
                f"📝 Kaam: {reminder_msg}\n"
                f"⏰ Kab: {time_str}\n"
                f"⏳ {readable_delta} baad\n\n"
                f"Cancel karne ke liye: 'cancel reminder #{reminder_id}'"
            ),
            "data": {
                "reminder_id": reminder_id,
                "message": reminder_msg,
                "remind_at": remind_at.isoformat(),
                "seconds_until": int(time_delta.total_seconds()),
                "alarm_intent": {
                    "action": "set_alarm",
                    "time": remind_at.strftime("%H:%M"),
                    "label": reminder_msg,
                },
            },
        }

    def _list_reminders(self, conn, user_id: str) -> dict:
        self._init_table(conn)
        now = datetime.now().isoformat()
        rows = conn.execute(
            "SELECT id, message, remind_at FROM reminders WHERE user_id = ? AND active = 1 AND remind_at > ? ORDER BY remind_at ASC LIMIT 20",
            (user_id, now),
        ).fetchall()

        if not rows:
            return {"response": "Koi active reminders nahi hain! 'remind me [time] [task]' se set karo. ⏰"}

        lines = [f"⏰ Tumhare {len(rows)} active reminders:\n"]
        for row in rows:
            remind_at = datetime.fromisoformat(row["remind_at"])
            time_str = remind_at.strftime("%I:%M %p, %d %b")
            delta = remind_at - datetime.now()
            readable = self._readable_delta(delta) if delta.total_seconds() > 0 else "abhi"
            lines.append(f"#{row['id']} | {row['message']}")
            lines.append(f"   ⏰ {time_str} ({readable} baad)\n")
        lines.append("Cancel: 'cancel reminder #3'")
        return {"response": "\n".join(lines)}

    def _cancel_reminder(self, conn, user_id: str, message: str) -> dict:
        self._init_table(conn)
        id_match = re.search(r'#?(\d+)', message)
        if not id_match:
            return {"response": "Kaunsa reminder cancel karna hai? ID batao! Jaise: 'cancel reminder #3'"}

        rid = int(id_match.group(1))
        row = conn.execute(
            "SELECT id, message FROM reminders WHERE id = ? AND user_id = ? AND active = 1",
            (rid, user_id),
        ).fetchone()
        if not row:
            return {"response": f"Reminder #{rid} nahi mila ya pehle se cancelled hai! ❌"}

        conn.execute("UPDATE reminders SET active = 0 WHERE id = ? AND user_id = ?", (rid, user_id))
        conn.commit()
        return {"response": f"🔕 Reminder #{rid} '{row['message']}' cancel ho gaya!"}

    @staticmethod
    def _readable_delta(delta: timedelta) -> str:
        total = int(delta.total_seconds())
        if total < 0:
            return "abhi"
        days = total // 86400
        hours = (total % 86400) // 3600
        minutes = (total % 3600) // 60
        parts = []
        if days > 0:
            parts.append(f"{days} din")
        if hours > 0:
            parts.append(f"{hours} ghante")
        if minutes > 0:
            parts.append(f"{minutes} minute")
        return " ".join(parts) if parts else "kuch hi second"
