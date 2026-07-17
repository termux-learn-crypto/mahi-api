import re
from . import Plugin


class MusicPlugin(Plugin):
    ACTIONS = {
        "play": {
            "keywords": ["play", "chalaao", "chala", "bajao", "sunao", "start", "resume"],
            "command": "play",
            "emoji": "▶\uFE0F",
        },
        "pause": {
            "keywords": ["pause", "ruk", "ruko", "tham", "stop"],
            "command": "pause",
            "emoji": "⏸",
        },
        "resume": {
            "keywords": ["resume", "chalu", "phir se", "wapas"],
            "command": "play",
            "emoji": "▶\uFE0F",
        },
        "next": {
            "keywords": ["next", "agla", "agle", "skip", "agla gaana", "next song"],
            "command": "next",
            "emoji": "⏭",
        },
        "previous": {
            "keywords": ["previous", "pichla", "pichle", "back", "pichla gaana", "last song"],
            "command": "previous",
            "emoji": "⏮",
        },
        "shuffle": {
            "keywords": ["shuffle", "random", "bekarar", "mishra"],
            "command": "shuffle",
            "emoji": "🔀",
        },
        "repeat": {
            "keywords": ["repeat", "dubara", "baar baar", "loop"],
            "command": "repeat",
            "emoji": "🔁",
        },
        "stop": {
            "keywords": ["stop music", "band karo music", "music band", "gaana band"],
            "command": "stop",
            "emoji": "⏹",
        },
    }

    def __init__(self):
        super().__init__(
            name="music",
            description="Music control - play, pause, skip, previous, shuffle, repeat",
            version="1.0.0",
        )
        self.commands = ["play", "pause", "skip", "next", "music", "gaana"]
        self.keywords = [
            "play", "pause", "skip", "next", "previous", "music", "gaana",
            "song", "bajao", "chalaao", "shuffle", "repeat", "resume",
        ]

    def can_handle(self, intent: str, message: str) -> bool:
        if intent in ("music", "play_music", "music_control"):
            return True
        if intent not in ("music", "mobile_command", "unknown", "greeting"):
            return False
        msg = message.lower()
        has_music_kw = any(kw in msg for kw in ["music", "gaana", "song", "sangeet"])
        has_action = any(
            any(kw in msg for kw in action["keywords"])
            for action in self.ACTIONS.values()
        )
        return has_music_kw or has_action

    def execute(self, user_id: str, message: str, context: dict) -> dict:
        msg = message.lower().strip()
        action = self._detect_action(msg)
        song_name = self._extract_song_name(msg, action)

        if action == "unknown":
            return {
                "response": (
                    "🎵 Music commands:\n\n"
                    "• 'play gaana' / 'chalaao song'\n"
                    "• 'pause karo'\n"
                    "• 'skip' / 'agla gaana'\n"
                    "• 'previous' / 'pichla gaana'\n"
                    "• 'shuffle'\n"
                    "• 'repeat'\n"
                    "• 'stop music'"
                ),
            }

        action_info = self.ACTIONS[action]
        command = {
            "action": "media_control",
            "command": action_info["command"],
            "package": "com.google.android.music",
        }

        if song_name:
            command["query"] = song_name
            command["data"] = f"android.intent.action.VIEW;query={song_name}"

        if action == "play" and song_name:
            response = f"{action_info['emoji']} '{song_name}' bajaa raha hoon!"
        elif action == "play":
            response = f"{action_info['emoji']} Music chalu kar raha hoon!"
        elif action == "pause":
            response = f"{action_info['emoji']} Music rok diya! Jab bolo tab chalu kar dunga."
        elif action == "resume":
            response = f"{action_info['emoji']} Music phir se chalu kar raha hoon!"
        elif action == "next":
            response = f"{action_info['emoji']} Agla gaana chala raha hoon!"
        elif action == "previous":
            response = f"{action_info['emoji']} Pichla gaana wapas la raha hoon!"
        elif action == "shuffle":
            response = f"{action_info['emoji']} Shuffle on! Ab kya aayega pata nahi!"
        elif action == "repeat":
            response = f"{action_info['emoji']} Repeat mode on! Gaana baar baar bajega!"
        elif action == "stop":
            response = f"{action_info['emoji']} Music band kar diya!"
        else:
            response = f"{action_info['emoji']} Command ready hai!"

        return {
            "response": response,
            "data": command,
        }

    def _detect_action(self, message: str) -> str:
        priority_order = ["stop", "pause", "play", "resume", "next", "previous", "shuffle", "repeat"]
        for action_key in priority_order:
            action = self.ACTIONS[action_key]
            for kw in action["keywords"]:
                if kw in message:
                    return action_key
        return "unknown"

    def _extract_song_name(self, message: str, action: str) -> str | None:
        if action != "play":
            return None
        patterns = [
            r'(?:play|chalaao|chala|bajao|sunao)\s+(.+?)(?:\s+by\s+|\s+ka\s+|\s+ki\s+|\s+ke\s+|$)',
            r'(.+?)\s+(?:play|bajao|chalaao|sunao)',
        ]
        for pattern in patterns:
            match = re.search(pattern, message, re.I)
            if match:
                name = match.group(1).strip()
                name = re.sub(
                    r'\b(song|gaana|music|pe|par|mein|on|spotify|youtube|video)\b',
                    '', name, flags=re.I
                ).strip()
                if name and len(name) > 1:
                    return name
        return None
