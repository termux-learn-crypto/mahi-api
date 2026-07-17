import json
from datetime import datetime
from . import Plugin


class GmailPlugin(Plugin):
    def __init__(self):
        super().__init__("gmail", "Gmail integration", "1.0.0")
        self.commands = ["check email", "send email", "read emails", "inbox"]
        self.keywords = ["email", "mail", "inbox", "gmail", "compose", "bhejo"]

    def can_handle(self, intent: str, message: str) -> bool:
        gmail_keywords = [
            "email", "mail", "gmail", "inbox", "compose", "send mail",
            "check email", "read email", "bhejo mail", "mail bhejo",
        ]
        msg_lower = message.lower()
        return any(kw in msg_lower for kw in gmail_keywords)

    def execute(self, user_id: str, message: str, context: dict) -> dict:
        msg_lower = message.lower()

        if any(word in msg_lower for word in ["send", "bhejo", "compose", "likho"]):
            return self._send_email(user_id, message)
        elif any(word in msg_lower for word in ["check", "read", "inbox", "dekho"]):
            return self._check_emails(user_id)
        elif any(word in msg_lower for word in ["unread", "napadhe"]):
            return self._get_unread(user_id)
        else:
            return self._get_inbox_summary(user_id)

    def _send_email(self, user_id: str, message: str) -> dict:
        import re
        to_match = re.search(r'to\s+(\S+@\S+)', message, re.IGNORECASE)
        to_email = to_match.group(1) if to_match else "recipient@example.com"

        return {
            "response": f"Email bhej rahi hu...\n\n"
                       f"To: {to_email}\n\n"
                       f"Gmail API key aur OAuth setup lagega iske liye!\n"
                       f"Abhi sirf demo response de sakti hu.",
            "command": {"type": "email_send", "to": to_email},
            "intent": "gmail",
        }

    def _check_emails(self, user_id: str) -> dict:
        return {
            "response": "Tumhara Inbox:\n\n"
                       "1. From: boss@company.com\n"
                       "   Subject: Meeting Tomorrow\n"
                       "   Time: 2 hours ago\n\n"
                       "2. From: friend@gmail.com\n"
                       "   Subject: Party Invite\n"
                       "   Time: 5 hours ago\n\n"
                       "3. From: amazon@orders.com\n"
                       "   Subject: Order Shipped\n"
                       "   Time: 1 day ago\n\n"
                       "Gmail API key lagegi real emails dekhne ke liye!",
            "command": {"type": "email_list"},
            "intent": "gmail",
        }

    def _get_unread(self, user_id: str) -> dict:
        return {
            "response": "Unread Emails (3):\n\n"
                       "1. Meeting Tomorrow - boss@company.com\n"
                       "2. Party Invite - friend@gmail.com\n"
                       "3. Order Shipped - amazon@orders.com\n\n"
                       "Gmail API key lagegi!",
            "command": {"type": "email_unread"},
            "intent": "gmail",
        }

    def _get_inbox_summary(self, user_id: str) -> dict:
        return {
            "response": "Email Summary:\n\n"
                       "Total: 25 emails\n"
                       "Unread: 3\n"
                       "Important: 2\n\n"
                       "Last email: Meeting Tomorrow (2 hours ago)\n\n"
                       "Kya karna hai? Check, send, ya kuch aur?",
            "command": {"type": "email_summary"},
            "intent": "gmail",
        }
