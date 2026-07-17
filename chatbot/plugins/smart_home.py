import json
from . import Plugin


class SmartHomePlugin(Plugin):
    def __init__(self):
        super().__init__("smart_home", "Smart Home device control", "1.0.0")
        self.commands = ["lights on", "ac on", "fan speed", "lock door", "smart home"]
        self.keywords = ["light", "ac", "fan", "lock", "door", "thermostat", "smart home", "device"]

    def can_handle(self, intent: str, message: str) -> bool:
        smart_keywords = [
            "light", "bulb", "lamp", "ac", "air conditioner", "fan",
            "lock", "door", "thermostat", "temperature", "smart home",
            "ghar ka", "bedroom", "kitchen light",
        ]
        msg_lower = message.lower()
        return any(kw in msg_lower for kw in smart_keywords)

    def execute(self, user_id: str, message: str, context: dict) -> dict:
        msg_lower = message.lower()

        if any(word in msg_lower for word in ["light", "bulb", "lamp", "roshni"]):
            return self._control_lights(user_id, message)
        elif any(word in msg_lower for word in ["ac", "air conditioner", "thand", "garmi"]):
            return self._control_ac(user_id, message)
        elif any(word in msg_lower for word in ["fan", "pankha"]):
            return self._control_fan(user_id, message)
        elif any(word in msg_lower for word in ["lock", "darwaza", "door"]):
            return self._control_lock(user_id, message)
        elif any(word in msg_lower for word in ["status", "haal", "kya chal"]):
            return self._get_status(user_id)
        else:
            return self._get_home_summary(user_id)

    def _control_lights(self, user_id: str, message: str) -> dict:
        msg_lower = message.lower()
        if any(word in msg_lower for word in ["on", "kholo", "jalaao", "badhao"]):
            state = "ON"
            emoji = "💡"
        elif any(word in message.lower() for word in ["off", "band", "bujhao", "kam"]):
            state = "OFF"
            emoji = "🌑"
        else:
            state = "TOGGLED"
            emoji = "💡"

        room = "Living Room"
        if "bedroom" in msg_lower or "kamra" in msg_lower:
            room = "Bedroom"
        elif "kitchen" in msg_lower or "rasoi" in msg_lower:
            room = "Kitchen"

        return {
            "response": f"{emoji} {room} lights {state}!\n\n"
                       f"Smart Home API (TP-Link/Philips Hue) lagega real control ke liye!",
            "command": {"type": "smart_light", "room": room, "state": state},
            "intent": "smart_home",
        }

    def _control_ac(self, user_id: str, message: str) -> dict:
        import re
        temp_match = re.search(r'(\d+)\s*degree', message, re.IGNORECASE)
        temp = temp_match.group(1) if temp_match else "24"

        msg_lower = message.lower()
        if any(word in msg_lower for word in ["on", "kholo", "chalu"]):
            state = "ON"
        elif any(word in msg_lower for word in ["off", "band"]):
            state = "OFF"
        else:
            state = "SET"

        return {
            "response": f"❄️ AC {state}!\n"
                       f"Temperature: {temp}°C\n"
                       f"Mode: Auto\n\n"
                       f"Smart Home API lagega!",
            "command": {"type": "smart_ac", "state": state, "temperature": temp},
            "intent": "smart_home",
        }

    def _control_fan(self, user_id: str, message: str) -> dict:
        import re
        speed_match = re.search(r'speed\s*(\d+)|level\s*(\d+)', message, re.IGNORECASE)
        speed = speed_match.group(1) or speed_match.group(2) if speed_match else "3"

        return {
            "response": f"🌀 Fan Speed: {speed}/5\n\n"
                       f"Smart Home API lagega!",
            "command": {"type": "smart_fan", "speed": speed},
            "intent": "smart_home",
        }

    def _control_lock(self, user_id: str, message: str) -> dict:
        msg_lower = message.lower()
        if any(word in msg_lower for word in ["lock", "band", "lock karo"]):
            state = "LOCKED"
            emoji = "🔒"
        else:
            state = "UNLOCKED"
            emoji = "🔓"

        return {
            "response": f"{emoji} Door {state}!\n\n"
                       f"Smart Lock API lagega!",
            "command": {"type": "smart_lock", "state": state},
            "intent": "smart_home",
        }

    def _get_status(self, user_id: str) -> dict:
        return {
            "response": "🏠 Smart Home Status:\n\n"
                       "💡 Living Room Lights: ON (80%)\n"
                       "💡 Bedroom Lights: OFF\n"
                       "❄️ AC: ON (24°C)\n"
                       "🌀 Fan: Speed 3/5\n"
                       "🔒 Door: LOCKED\n"
                       "📷 Camera: ACTIVE\n\n"
                       "Sab kuch normal hai!",
            "command": {"type": "smart_status"},
            "intent": "smart_home",
        }

    def _get_home_summary(self, user_id: str) -> dict:
        return {
            "response": "🏠 Smart Home Control:\n\n"
                       "Available Devices:\n"
                       "• Lights (Living Room, Bedroom, Kitchen)\n"
                       "• AC (Bedroom)\n"
                       "• Fan (Living Room, Bedroom)\n"
                       "• Smart Lock\n"
                       "• Security Camera\n\n"
                       "Kya control karna hai?",
            "command": {"type": "smart_list"},
            "intent": "smart_home",
        }
