import re
import requests
from . import Plugin
from ..config import config


class WeatherPlugin(Plugin):
    CITY_MAP = {
        "मुंबई": "Mumbai", "दिल्ली": "Delhi", "बेंगलुरु": "Bangalore",
        "बैंगलोर": "Bangalore", "चेन्नई": "Chennai", "कोलकाता": "Kolkata",
        "हैदराबाद": "Hyderabad", "पुणे": "Pune", "अहमदाबाद": "Ahmedabad",
        "जयपुर": "Jaipur", "लखनऊ": "Lucknow", "वाराणसी": "Varanasi",
        "गोवा": "Goa", "शिमला": "Shimla", "मनाली": "Manali",
        "आगरा": "Agra", "नागपुर": "Nagpur", "इंदौर": "Indore",
        "भोपाल": "Bhopal", "पटना": "Patna", "चंडीगढ़": "Chandigarh",
        "रांची": "Ranchi", "रायपुर": "Raipur", "बोकारो": "Bokaro",
        "धनबाद": "Dhanbad", "सूरत": "Surat", "विशाखापत्तनम": "Visakhapatnam",
        "कोच्चि": "Kochi", "तिरुवनंतपुरम": "Thiruvananthapuram",
        "गुवाहाटी": "Guwahati", "भुवनेश्वर": "Bhubaneswar",
        "देहरादून": "Dehradun", "नैनीताल": "Nainital",
    }

    def __init__(self):
        super().__init__(
            name="weather",
            description="Weather information for any city - temperature, conditions, humidity, wind",
            version="1.0.0",
        )
        self.commands = ["weather", "mausam", "mausam batao", "temperature"]
        self.keywords = [
            "weather", "mausam", "temperature", "tapman", "thand", "garmi",
            "barish", "rain", "sun", "cloud", "humidity", "wind",
        ]

    def can_handle(self, intent: str, message: str) -> bool:
        if intent in ("weather", "temperature"):
            return True
        if intent not in ("weather", "unknown", "greeting", "identity"):
            return False
        msg = message.lower()
        weather_words = ["weather", "mausam", "temperature", "tapman", "thand", "garmi", "barish"]
        return any(w in msg for w in weather_words)

    def execute(self, user_id: str, message: str, context: dict) -> dict:
        api_key = config.WEATHER_API_KEY
        if not api_key:
            return {"response": "Weather API key set nahi hai! Admin se baat karo. 🔑"}

        city = self._extract_city(message)
        if not city:
            return {"response": "Kis city ka mausam jaanna hai? Naam batao! 🌆"}

        try:
            url = "https://api.openweathermap.org/data/2.5/weather"
            params = {"q": city, "appid": api_key, "units": "metric", "lang": "hi"}
            resp = requests.get(url, params=params, timeout=10)

            if resp.status_code == 404:
                return {"response": f"'{city}' naam ki city nahi mili! Sahi naam likho. 😅"}
            if resp.status_code == 401:
                return {"response": "Weather API key galat hai! Admin ko bolo. 🔑"}
            resp.raise_for_status()

            data = resp.json()
            temp = data["main"]["temp"]
            feels = data["main"]["feels_like"]
            humidity = data["main"]["humidity"]
            desc = data["weather"][0]["description"].capitalize()
            wind = data["wind"]["speed"]
            city_name = data["name"]
            country = data["sys"].get("country", "")
            temp_min = data["main"]["temp_min"]
            temp_max = data["main"]["temp_max"]
            visibility = data.get("visibility", 0) / 1000

            emoji = self._weather_emoji(data["weather"][0]["main"])

            response = (
                f"{emoji} {city_name}, {country} ka mausam:\n\n"
                f"🌡 Temperature: {temp}°C (feels like {feels}°C)\n"
                f"📊 Range: {temp_min}°C - {temp_max}°C\n"
                f"☁ Halat: {desc}\n"
                f"💧 Nami (Humidity): {humidity}%\n"
                f"💨 Hawa: {wind} m/s\n"
                f"👁 Visibility: {visibility:.1f} km"
            )
            return {"response": response, "data": {
                "city": city_name, "country": country,
                "temp": temp, "feels_like": feels,
                "humidity": humidity, "description": desc,
                "wind": wind, "temp_min": temp_min, "temp_max": temp_max,
            }}

        except requests.Timeout:
            return {"response": "Weather service se response nahi aaya! Thodi der baad try karo. ⏳"}
        except requests.RequestException as e:
            return {"response": "Weather data lene mein dikkat aa rahi hai! Baad mein try karo. 😔"}

    def _extract_city(self, message: str) -> str | None:
        msg = message.strip()
        patterns = [
            r"(?:weather|mausam|temperature|tapman)\s+(?:of|ka|ki|in|for|mein)?\s*(.+)",
            r"(.+?)\s+(?:ka|ki|mein|ka|ko)?\s*(?:weather|mausam|temperature|tapman)",
            r"(?:batao|jaanna|pata|kya hai)\s+(?:weather|mausam)\s*(?:of|ka|ki|in|for|mein)?\s*(.+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, msg, re.IGNORECASE)
            if match:
                city = match.group(1).strip()
                city = re.sub(r'\b(ka|ki|ke|ko|hai|hain|ho|batao|jaanna|kya|the|is|of|in|for|mein)\b', '', city, flags=re.IGNORECASE).strip()
                if city:
                    return self.CITY_MAP.get(city, city)
        for hindi, english in self.CITY_MAP.items():
            if hindi in msg:
                return english
        words = msg.split()
        if len(words) <= 3:
            cleaned = ' '.join(words)
            cleaned = re.sub(r'\b(weather|mausam|temperature|tapman|ka|ki|ke|ko|hai|batao|kya|the|of|in|for|mein)\b', '', cleaned, flags=re.IGNORECASE).strip()
            if cleaned:
                return self.CITY_MAP.get(cleaned, cleaned)
        return None

    @staticmethod
    def _weather_emoji(condition: str) -> str:
        mapping = {
            "Clear": "☀", "Clouds": "☁", "Rain": "🌧", "Drizzle": "🌦",
            "Thunderstorm": "⛈", "Snow": "❄", "Mist": "🌫", "Fog": "🌫",
            "Haze": "🌫", "Smoke": "🌫", "Dust": "🌫", "Sand": "🌫",
            "Ash": "🌫", "Squall:": "💨", "Tornado": "🌪",
        }
        return mapping.get(condition, "🌤")
