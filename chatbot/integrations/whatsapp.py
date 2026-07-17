import json
import requests


class WhatsAppIntegration:
    def __init__(self, api_key: str = None, phone_number_id: str = None):
        self.api_key = api_key
        self.phone_number_id = phone_number_id
        self.base_url = "https://graph.facebook.com/v17.0"

    def is_configured(self) -> bool:
        return self.api_key is not None and self.phone_number_id is not None

    def send_message(self, to: str, text: str) -> dict:
        if not self.is_configured():
            return {"error": "WhatsApp API not configured"}

        url = f"{self.base_url}/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": text},
        }

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=10)
            return resp.json()
        except Exception as e:
            return {"error": str(e)}

    def handle_webhook(self, data: dict) -> dict:
        if "entry" not in data:
            return {"status": "ignored"}

        for entry in data["entry"]:
            for change in entry.get("changes", []):
                value = change.get("value", {})
                messages = value.get("messages", [])

                for msg in messages:
                    from_number = msg.get("from", "")
                    text = msg.get("text", {}).get("body", "")

                    if text and from_number:
                        from ..engine import ChatEngine
                        engine = ChatEngine()
                        result = engine.chat(f"whatsapp_{from_number}", text)

                        self.send_message(from_number, result["response"])

                        return {
                            "status": "processed",
                            "from": from_number,
                            "intent": result["intent"],
                        }

        return {"status": "ignored"}

    def send_template(self, to: str, template_name: str, language: str = "en") -> dict:
        if not self.is_configured():
            return {"error": "WhatsApp API not configured"}

        url = f"{self.base_url}/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language},
            },
        }

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=10)
            return resp.json()
        except Exception as e:
            return {"error": str(e)}

    def send_image(self, to: str, image_url: str, caption: str = None) -> dict:
        if not self.is_configured():
            return {"error": "WhatsApp API not configured"}

        url = f"{self.base_url}/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "image",
            "image": {"link": image_url, "caption": caption},
        }

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=10)
            return resp.json()
        except Exception as e:
            return {"error": str(e)}
