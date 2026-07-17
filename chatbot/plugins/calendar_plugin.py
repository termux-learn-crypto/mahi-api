import json
from datetime import datetime, timedelta
from . import Plugin


class CalendarPlugin(Plugin):
    def __init__(self):
        super().__init__("calendar", "Google Calendar integration", "1.0.0")
        self.commands = ["add event", "upcoming events", "calendar", "meeting", "schedule"]
        self.keywords = ["calendar", "event", "meeting", "schedule", "remind", "appointment", "plan"]

    def can_handle(self, intent: str, message: str) -> bool:
        calendar_keywords = [
            "calendar", "event", "meeting", "schedule", "appointment",
            "upcoming", "plan karo", "add event", "calendar mein",
        ]
        msg_lower = message.lower()
        return any(kw in msg_lower for kw in calendar_keywords)

    def execute(self, user_id: str, message: str, context: dict) -> dict:
        msg_lower = message.lower()

        if any(word in msg_lower for word in ["add", "create", "banao", "jodo"]):
            return self._add_event(user_id, message)
        elif any(word in msg_lower for word in ["upcoming", "aane wale", "next", "agla"]):
            return self._get_upcoming(user_id)
        elif any(word in msg_lower for word in ["today", "aaj", "is hafte"]):
            return self._get_today(user_id)
        else:
            return self._get_upcoming(user_id)

    def _add_event(self, user_id: str, message: str) -> dict:
        import re
        event = {
            "title": self._extract_event_title(message),
            "date": self._extract_event_date(message),
            "time": self._extract_event_time(message),
            "reminder": True,
        }

        return {
            "response": f"Calendar mein add kar rahi hu:\n"
                       f"Event: {event['title']}\n"
                       f"Date: {event['date']}\n"
                       f"Time: {event['time']}\n\n"
                       f"Google Calendar API key lagegi iske liye!",
            "command": {"type": "calendar_add", "event": event},
            "intent": "calendar",
        }

    def _get_upcoming(self, user_id: str) -> dict:
        return {
            "response": "Aane wale events:\n\n"
                       "1. Team Meeting - Kal 10:00 AM\n"
                       "2. Doctor Appointment - Parson 2:00 PM\n"
                       "3. Birthday Party - 20 July\n\n"
                       "Google Calendar API key lagegi real events dekhne ke liye!",
            "command": {"type": "calendar_list"},
            "intent": "calendar",
        }

    def _get_today(self, user_id: str) -> dict:
        today = datetime.now().strftime("%d %B %Y")
        return {
            "response": f"Aaj {today} hai.\n\nAaj ke events:\n"
                       "1. Morning Standup - 9:00 AM\n"
                       "2. Lunch with Client - 1:00 PM\n\n"
                       "Google Calendar API key lagegi real events dekhne ke liye!",
            "command": {"type": "calendar_today"},
            "intent": "calendar",
        }

    def _extract_event_title(self, message: str) -> str:
        import re
        patterns = [
            r"add\s+(?:event|meeting)?\s*(.+)",
            r"create\s+(.+)",
            r"schedule\s+(.+)",
            r"banao\s+(.+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return "New Event"

    def _extract_event_date(self, message: str) -> str:
        msg_lower = message.lower()
        if "kal" in msg_lower or "tomorrow" in msg_lower:
            return (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        elif "parson" in msg_lower:
            return (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
        elif "aaj" in msg_lower or "today" in msg_lower:
            return datetime.now().strftime("%Y-%m-%d")
        return datetime.now().strftime("%Y-%m-%d")

    def _extract_event_time(self, message: str) -> str:
        import re
        time_match = re.search(r'(\d{1,2}):(\d{2})\s*(am|pm)?', message, re.IGNORECASE)
        if time_match:
            return time_match.group()
        return "10:00 AM"
