import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from . import Plugin
from ..config import config


class EmailPlugin(Plugin):
    def __init__(self):
        super().__init__(
            name="email",
            description="Send emails via Gmail SMTP with subject, body, and to address",
            version="1.0.0",
        )
        self.commands = ["email", "mail", "bhejo", "send email"]
        self.keywords = [
            "email", "mail", "bhejo", "send", "compose", "likh",
            "gmail", "smtp", "forward",
        ]

    def can_handle(self, intent: str, message: str) -> bool:
        if intent in ("email", "send_email"):
            return True
        msg = message.lower()
        return any(kw in msg for kw in self.keywords)

    def execute(self, user_id: str, message: str, context: dict) -> dict:
        to, subject, body = self._parse_email(message)

        if not to:
            return {
                "response": (
                    "📧 Email bhejne ke liye ye batao:\n\n"
                    "Examples:\n"
                    "• 'email to user@gmail.com subject Meeting hai body Kal meeting hai 10 baje'\n"
                    "• 'mail bhejo raj@company.com Welcome to team'\n"
                    "• 'send email to +919876543210 subject Hello body Hi how are you'\n\n"
                    "Note: Gmail app password set hona chahiye!"
                ),
            }

        if not self._validate_email(to) and not self._validate_phone(to):
            return {"response": f"Email address ya phone number galat lag raha hai: '{to}'! Check karo. ❌"}

        if not config.EMAIL_USER or not config.EMAIL_PASS:
            return {
                "response": (
                    "📧 Email credentials set nahi hai!\n\n"
                    "Admin ko bolo .env file mein ye set kare:\n"
                    "EMAIL_USER=tumhara@gmail.com\n"
                    "EMAIL_PASS=gmail_app_password\n\n"
                    "Gmail App Password banane ke liye:\n"
                    "Google Account > Security > 2-Step Verification > App Passwords"
                ),
            }

        success = self._send_email(to, subject, body)

        if success:
            return {
                "response": (
                    f"✅ Email bhej diya!\n\n"
                    f"📧 To: {to}\n"
                    f"📝 Subject: {subject}\n"
                    f"💬 Body: {body[:200]}{'...' if len(body) > 200 else ''}"
                ),
                "data": {
                    "to": to, "subject": subject, "body": body,
                    "from": config.EMAIL_USER, "status": "sent",
                },
            }
        else:
            return {
                "response": (
                    "❌ Email nahi bhej paya! Possible reasons:\n"
                    "• Gmail App Password galat hai\n"
                    "• SMTP connection issue hai\n"
                    "• Internet band hai\n\n"
                    "Gmail App Password check karo!"
                ),
            }

    def _parse_email(self, message: str) -> tuple:
        to = None
        subject = "No Subject"
        body = ""

        to_match = re.search(
            r'(?:to|ko|bhejo|send)\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}|\+?\d{10,15})',
            message, re.I,
        )
        if to_match:
            to = to_match.group(1).strip()

        subject_match = re.search(
            r'(?:subject|vishay|title)\s*[:=]?\s*(.+?)(?:\s+body|\s+content|\s+message|$)',
            message, re.I,
        )
        if subject_match:
            subject = subject_match.group(1).strip()
            subject = subject.strip('".!')
        else:
            if to:
                after_to = message[message.index(to) + len(to):].strip()
                body_match = re.search(
                    r'^(?:subject|vishay|title)\s*[:=]?\s*(.+?)(?:\s+body|\s+content|\s+message|$)',
                    after_to, re.I,
                )
                if body_match:
                    subject = body_match.group(1).strip().strip('".!')
                    after_subject = after_to[after_to.index(body_match.group(1)) + len(body_match.group(1)):].strip()
                    body_match2 = re.search(
                        r'(?:body|content|message|sandesh)\s*[:=]?\s*(.+)',
                        after_subject, re.I,
                    )
                    if body_match2:
                        body = body_match2.group(1).strip()

        if not body:
            body_match = re.search(
                r'(?:body|content|message|sandesh)\s*[:=]?\s*(.+)',
                message, re.I,
            )
            if body_match:
                body = body_match.group(1).strip()
            elif to:
                remaining = message
                if to in remaining:
                    idx = remaining.index(to)
                    remaining = remaining[idx + len(to):]
                remaining = re.sub(
                    r'\b(to|ko|send|bhejo|subject|vishay|title|body|content|message|sandesh)\b',
                    '', remaining, flags=re.I
                ).strip()
                remaining = re.sub(r'\s*[:=]\s*', ' ', remaining).strip()
                if remaining and not body:
                    body = remaining

        if not body and to:
            body = subject
            if body == "No Subject":
                body = "Hi! ye email Mahi se aaya hai."

        return to, subject, body

    def _send_email(self, to: str, subject: str, body: str) -> bool:
        try:
            msg = MIMEMultipart()
            msg["From"] = config.EMAIL_USER
            msg["To"] = to
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain", "utf-8"))

            with smtplib.SMTP(config.EMAIL_HOST, config.EMAIL_PORT) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(config.EMAIL_USER, config.EMAIL_PASS)
                server.send_message(msg)
            return True
        except Exception:
            return False

    @staticmethod
    def _validate_email(email: str) -> bool:
        return bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email))

    @staticmethod
    def _validate_phone(phone: str) -> bool:
        cleaned = re.sub(r'[\s\-\(\)]', '', phone)
        return bool(re.match(r'^\+?\d{10,15}$', cleaned))
