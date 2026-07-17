import re
import requests
from . import Plugin


class DictionaryPlugin(Plugin):
    def __init__(self):
        super().__init__(
            name="dictionary",
            description="Word definitions, synonyms, antonyms, and example sentences using free dictionary API",
            version="1.0.0",
        )
        self.commands = ["define", "dictionary", "meaning", "word"]
        self.keywords = [
            "define", "definition", "meaning", "matlab", "dictionary",
            "word", "shabd", "synonym", "antonym", "artha",
            "what does", "kya hota hai", "kya matlab",
        ]

    def can_handle(self, intent: str, message: str) -> bool:
        if intent in ("name_meaning", "mobile_command", "calculator", "translator"):
            return False
        if intent in ("definition", "dictionary", "word_meaning"):
            return True
        msg = message.lower()
        if "naam ka matlab" in msg or "naam ka arth" in msg:
            return False
        return any(kw in msg for kw in self.keywords)

    def execute(self, user_id: str, message: str, context: dict) -> dict:
        word = self._extract_word(message)
        if not word:
            return {
                "response": (
                    "📖 Kis word ka matlab jaanna hai?\n\n"
                    "Examples:\n"
                    "• 'define serendipity'\n"
                    "• 'meaning of ephemeral'\n"
                    "• 'what does ephemeral mean'\n"
                    "• 'word resilience ka matlab'"
                ),
            }

        try:
            url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
            resp = requests.get(url, timeout=10)

            if resp.status_code == 404:
                return {
                    "response": (
                        f"📖 '{word}' ye word dictionary mein nahi mila!\n"
                        f"Sahi spelling check karo ya koi aur word try karo. 🔍"
                    ),
                }
            resp.raise_for_status()

            data = resp.json()
            if not data or not isinstance(data, list):
                return {"response": f"'{word}' ka data nahi mila! 😅"}

            entry = data[0]
            word_display = entry.get("word", word)
            phonetic = entry.get("phonetic", "")
            phonetics = entry.get("phonetics", [])
            audio_url = None
            for p in phonetics:
                if p.get("audio"):
                    audio_url = p["audio"]
                    break

            lines = [f"📖 **{word_display}**"]
            if phonetic:
                lines.append(f"🔊 Pronunciation: {phonetic}")
            lines.append("")

            all_synonyms = set()
            all_antonyms = set()

            for meaning in entry.get("meanings", []):
                pos = meaning.get("partOfSpeech", "unknown")
                pos_emoji = {
                    "noun": "📝", "verb": "🏃", "adjective": "🎨",
                    "adverb": "📌", "pronoun": "👥", "preposition": "🔗",
                    "conjunction": "🔗", "interjection": "💬", "exclamation": "💬",
                }.get(pos, "📝")

                lines.append(f"{pos_emoji} {pos.upper()}:")
                for i, defn in enumerate(meaning.get("definitions", [])[:3], 1):
                    definition = defn.get("definition", "")
                    lines.append(f"  {i}. {definition}")
                    example = defn.get("example")
                    if example:
                        lines.append(f'     💬 Example: "{example}"')
                    for s in defn.get("synonyms", []):
                        all_synonyms.add(s)
                    for a in defn.get("antonyms", []):
                        all_antonyms.add(a)

                for s in meaning.get("synonyms", []):
                    all_synonyms.add(s)
                for a in meaning.get("antonyms", []):
                    all_antonyms.add(a)

                lines.append("")

            if all_synonyms:
                syn_list = list(all_synonyms)[:8]
                lines.append(f"🔄 Synonyms: {', '.join(syn_list)}")
            if all_antonyms:
                ant_list = list(all_antonyms)[:8]
                lines.append(f"🔀 Antonyms: {', '.join(ant_list)}")

            if audio_url:
                lines.append(f"\n🔊 Audio: {audio_url}")

            return {
                "response": "\n".join(lines),
                "data": {
                    "word": word_display,
                    "phonetic": phonetic,
                    "audio": audio_url,
                    "synonyms": list(all_synonyms)[:20],
                    "antonyms": list(all_antonyms)[:20],
                    "definitions_count": sum(
                        len(m.get("definitions", []))
                        for m in entry.get("meanings", [])
                    ),
                },
            }

        except requests.Timeout:
            return {"response": "Dictionary service slow hai! Thodi der baad try karo. ⏳"}
        except requests.RequestException:
            return {"response": "Dictionary se data lene mein dikkat! Baad mein try karo. 😔"}

    def _extract_word(self, message: str) -> str | None:
        msg = message.strip()
        patterns = [
            r'(?:define|definition of|meaning of|matlab|kya hota hai|kya matlab|artha|shabd)\s+(.+?)(?:\?|$)',
            r'(.+?)\s+(?:ka matlab|ka artha|meaning|matlab kya|definition|define)',
            r'what does\s+(.+?)\s+mean',
            r'(.+?)\s+ka\s+meaning',
        ]
        for pattern in patterns:
            match = re.search(pattern, msg, re.I)
            if match:
                word = match.group(1).strip()
                word = re.sub(
                    r'\b(word|shabd|hai|hain|ka|ki|ke|ko|kya|batao|bolo|ho|the|is|of|does|mean|please|jaanna)\b',
                    '', word, flags=re.I
                ).strip()
                word = word.strip('".!?,')
                if word and len(word) > 1 and len(word.split()) <= 3:
                    return word.lower()
        cleaned = re.sub(
            r'\b(define|definition|meaning|matlab|dictionary|word|shabd|ka|ki|ke|ko|kya|batao|bolo|ho|hain|hai|of|please|jaanna|what does|artha|kya hota hai|kya matlab)\b',
            '', msg, flags=re.I
        ).strip()
        cleaned = cleaned.strip('".!?,')
        if cleaned and 1 < len(cleaned.split()) <= 3:
            return cleaned.lower()
        return None
