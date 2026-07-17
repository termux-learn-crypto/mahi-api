import json
import requests


class SlackIntegration:
    def __init__(self, bot_token: str = None, signing_secret: str = None):
        self.bot_token = bot_token
        self.signing_secret = signing_secret
        self.base_url = "https://slack.com/api"

    def is_configured(self) -> bool:
        return self.bot_token is not None

    def send_message(self, channel: str, text: str) -> dict:
        if not self.is_configured():
            return {"error": "Slack bot token not configured"}

        url = f"{self.base_url}/chat.postMessage"
        headers = {
            "Authorization": f"Bearer {self.bot_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "channel": channel,
            "text": text,
        }

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=10)
            return resp.json()
        except Exception as e:
            return {"error": str(e)}

    def handle_event(self, event: dict) -> dict:
        if event.get("type") == "message" and "text" in event:
            user_id = event.get("user", "unknown")
            channel = event.get("channel", "")
            text = event.get("text", "")

            if text.startswith("!mahi") or text.startswith("@mahi"):
                query = text.replace("!mahi", "").replace("@mahi", "").strip()

                from ..engine import ChatEngine
                engine = ChatEngine()
                result = engine.chat(f"slack_{user_id}", query)

                self.send_message(channel, result["response"])

                return {
                    "status": "processed",
                    "user_id": user_id,
                    "intent": result["intent"],
                }

        return {"status": "ignored"}

    def handle_interaction(self, payload: dict) -> dict:
        action = payload.get("actions", [{}])[0]
        action_type = action.get("type", "")
        action_value = action.get("value", "")

        if action_type == "button":
            from ..engine import ChatEngine
            engine = ChatEngine()
            result = engine.chat("slack_interactive", action_value)

            return {
                "status": "processed",
                "response": result["response"],
                "replace_original": True,
            }

        return {"status": "ignored"}

    def get_channels(self) -> list[dict]:
        if not self.is_configured():
            return []

        url = f"{self.base_url}/channels.list"
        headers = {"Authorization": f"Bearer {self.bot_token}"}

        try:
            resp = requests.get(url, headers=headers, timeout=10)
            data = resp.json()
            return data.get("channels", [])
        except Exception:
            return []
