import re
import requests
from . import Plugin
from ..config import config


class NewsPlugin(Plugin):
    CATEGORIES = {
        "tech": {"en": "technology", "hi": "तकनीक"},
        "sports": {"en": "sports", "hi": "खेल"},
        "business": {"en": "business", "hi": "व्यापार"},
        "entertainment": {"en": "entertainment", "hi": "मनोरंजन"},
        "general": {"en": "general", "hi": "सामान्य"},
        "science": {"en": "science", "hi": "विज्ञान"},
        "health": {"en": "health", "hi": "स्वास्थ्य"},
    }

    CATEGORY_KEYWORDS = {
        "tech": ["tech", "technology", "takneek", "computer", "software", "ai", "app", "phone", "gadget"],
        "sports": ["sports", "cricket", "football", "khel", "ipl", "match", "player"],
        "business": ["business", "stock", "market", "paisa", "economy", "trade", "share"],
        "entertainment": ["entertainment", "movie", "film", "bollywood", "music", "actor", "actress", "celeb"],
        "science": ["science", "vignyan", "space", "nasa", "research", "discovery"],
        "health": ["health", "sehat", "doctor", "medicine", "fitness", "disease"],
    }

    def __init__(self):
        super().__init__(
            name="news",
            description="Latest news headlines by category - tech, sports, business, entertainment",
            version="1.0.0",
        )
        self.commands = ["news", "headlines", "khabar", "samachar", "taza khabar"]
        self.keywords = [
            "news", "headlines", "khabar", "samachar", "taza", "latest",
            "happening", "breaking",
        ]

    def can_handle(self, intent: str, message: str) -> bool:
        if intent == "news":
            return True
        msg = message.lower()
        return any(kw in msg for kw in self.keywords)

    def execute(self, user_id: str, message: str, context: dict) -> dict:
        api_key = config.NEWS_API_KEY
        if not api_key:
            return {"response": "News API key set nahi hai! Admin se baat karo. 🔑"}

        category = self._detect_category(message)
        count = self._detect_count(message)

        try:
            params = {
                "apiKey": api_key,
                "language": "en",
                "pageSize": min(count, 10),
            }
            if category and category != "general":
                params["category"] = category
                params["country"] = "in"
            else:
                params["country"] = "in"
                params["category"] = "general"

            url = "https://newsapi.org/v2/top-headlines"
            resp = requests.get(url, params=params, timeout=15)

            if resp.status_code == 401:
                return {"response": "News API key galat hai! Admin ko bolo. 🔑"}
            if resp.status_code == 426:
                return {"response": "News API upgrade chahiye! Free tier pe limit aa gayi. 😅"}
            resp.raise_for_status()

            data = resp.json()
            articles = data.get("articles", [])

            if not articles:
                cat_display = self.CATEGORIES.get(category, {}).get("hi", "सामान्य") if category else "सामान्य"
                return {"response": f"Abhi '{cat_display}' category mein koi news nahi mili! 📭"}

            cat_display = self.CATEGORIES.get(category, {}).get("hi", "सामान्य") if category else "भारत"
            lines = [f"📰 {cat_display} ki top headlines:\n"]
            for i, article in enumerate(articles[:count], 1):
                title = article.get("title", "Bina title ke")
                source = article.get("source", {}).get("name", "Unknown")
                title = title[:120] + "..." if len(title) > 120 else title
                lines.append(f"{i}. {title}")
                lines.append(f"   📌 Source: {source}\n")

            lines.append("Zyada news chahiye toh 'aur khabar bolo' bolo!")
            return {
                "response": "\n".join(lines),
                "data": {
                    "category": category or "general",
                    "count": len(articles[:count]),
                    "articles": [
                        {"title": a.get("title"), "source": a.get("source", {}).get("name"), "url": a.get("url")}
                        for a in articles[:count]
                    ],
                },
            }

        except requests.Timeout:
            return {"response": "News service slow hai! Thodi der baad try karo. ⏳"}
        except requests.RequestException:
            return {"response": "News lene mein dikkat aa rahi hai! Baad mein try karo. 😔"}

    def _detect_category(self, message: str) -> str | None:
        msg = message.lower()
        for cat, keywords in self.CATEGORY_KEYWORDS.items():
            for kw in keywords:
                if kw in msg:
                    return cat
        for cat in self.CATEGORIES:
            if cat in msg:
                return cat
        return None

    @staticmethod
    def _detect_count(message: str) -> int:
        match = re.search(r'(\d+)\s*(?:news|headline|khabar|article)', message.lower())
        if match:
            return min(int(match.group(1)), 10)
        if any(w in message.lower() for w in ["sab", "all", "poori", "zyada", "more"]):
            return 10
        return 5
