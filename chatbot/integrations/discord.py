import json
import requests


class DiscordIntegration:
    def __init__(self, bot_token: str = None):
        self.bot_token = bot_token
        self.base_url = "https://discord.com/api/v10"

    def is_configured(self) -> bool:
        return self.bot_token is not None

    def send_message(self, channel_id: str, content: str) -> dict:
        if not self.is_configured():
            return {"error": "Discord bot token not configured"}

        url = f"{self.base_url}/channels/{channel_id}/messages"
        headers = {
            "Authorization": f"Bot {self.bot_token}",
            "Content-Type": "application/json",
        }
        payload = {"content": content}

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=10)
            return resp.json()
        except Exception as e:
            return {"error": str(e)}

    def handle_message(self, data: dict) -> dict:
        if data.get("author", {}).get("bot", False):
            return {"status": "ignored"}

        channel_id = data.get("channel_id", "")
        user_id = data.get("author", {}).get("id", "unknown")
        content = data.get("content", "")

        if content.startswith("!mahi") or content.startswith("<@!mahi>"):
            query = content.replace("!mahi", "").replace("<@!mahi>", "").strip()

            from ..engine import ChatEngine
            engine = ChatEngine()
            result = engine.chat(f"discord_{user_id}", query)

            self.send_message(channel_id, result["response"])

            return {
                "status": "processed",
                "user_id": user_id,
                "intent": result["intent"],
            }

        return {"status": "ignored"}

    def send_embed(self, channel_id: str, title: str, description: str,
                   color: int = 0x00FF00) -> dict:
        if not self.is_configured():
            return {"error": "Discord bot token not configured"}

        url = f"{self.base_url}/channels/{channel_id}/messages"
        headers = {
            "Authorization": f"Bot {self.bot_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "embeds": [{
                "title": title,
                "description": description,
                "color": color,
            }]
        }

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=10)
            return resp.json()
        except Exception as e:
            return {"error": str(e)}

    def get_guilds(self) -> list[dict]:
        if not self.is_configured():
            return []

        url = f"{self.base_url}/users/@me/guilds"
        headers = {"Authorization": f"Bot {self.bot_token}"}

        try:
            resp = requests.get(url, headers=headers, timeout=10)
            return resp.json()
        except Exception:
            return []
