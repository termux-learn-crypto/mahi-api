import json
import requests
from datetime import datetime


class TelegramIntegration:
    def __init__(self, bot_token: str = None):
        self.bot_token = bot_token
        self.base_url = f"https://api.telegram.org/bot{bot_token}" if bot_token else None

    def is_configured(self) -> bool:
        return self.bot_token is not None

    def send_message(self, chat_id: str, text: str, parse_mode: str = "HTML") -> dict:
        if not self.is_configured():
            return {"error": "Telegram bot token not configured"}

        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
        }

        try:
            resp = requests.post(url, json=payload, timeout=10)
            return resp.json()
        except Exception as e:
            return {"error": str(e)}

    def handle_webhook(self, update: dict) -> dict:
        if "message" not in update:
            return {"status": "ignored"}

        message = update["message"]
        chat_id = str(message["chat"]["id"])
        user_id = str(message["from"]["id"])
        text = message.get("text", "")

        if not text:
            return {"status": "no_text"}

        from ..engine import ChatEngine
        engine = ChatEngine()
        result = engine.chat(f"telegram_{user_id}", text)

        response = result["response"]
        self.send_message(chat_id, response)

        return {
            "status": "processed",
            "user_id": user_id,
            "intent": result["intent"],
        }

    def get_updates(self, offset: int = None) -> list[dict]:
        if not self.is_configured():
            return []

        url = f"{self.base_url}/getUpdates"
        params = {"limit": 100}
        if offset:
            params["offset"] = offset

        try:
            resp = requests.get(url, params=params, timeout=10)
            data = resp.json()
            return data.get("result", [])
        except Exception:
            return []

    def set_webhook(self, webhook_url: str) -> dict:
        if not self.is_configured():
            return {"error": "Telegram bot token not configured"}

        url = f"{self.base_url}/setWebhook"
        payload = {"url": webhook_url}

        try:
            resp = requests.post(url, json=payload, timeout=10)
            return resp.json()
        except Exception as e:
            return {"error": str(e)}

    def get_bot_info(self) -> dict:
        if not self.is_configured():
            return {"error": "Not configured"}

        url = f"{self.base_url}/getMe"
        try:
            resp = requests.get(url, timeout=10)
            return resp.json().get("result", {})
        except Exception:
            return {"error": "Failed to get bot info"}

    def send_typing(self, chat_id: str):
        if not self.is_configured():
            return

        url = f"{self.base_url}/sendChatAction"
        payload = {"chat_id": chat_id, "action": "typing"}
        try:
            requests.post(url, json=payload, timeout=5)
        except Exception:
            pass
