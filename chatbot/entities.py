import re
from datetime import datetime, timedelta
from typing import Optional


class EntityExtractor:
    def __init__(self):
        self.patterns = {
            "email": r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            "phone": r'(?:\+91|91|0)?[6-9]\d{9}',
            "url": r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[/\w\-.~:/?#\[\]@!$&\'()*+,;=]*',
            "date": r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+\d{2,4}',
            "time": r'\d{1,2}:\d{2}\s*(?:am|pm|AM|PM)?',
            "number": r'\b\d+(?:\.\d+)?\b',
            "currency": r'(?:₹|Rs\.?|INR|\$|USD|€|EUR|£|GBP)\s*\d+(?:,\d{3})*(?:\.\d+)?',
            "pin_code": r'\b[1-9]\d{5}\b',
            " Aadhaar": r'\b\d{4}\s?\d{4}\s?\d{4}\b',
            "pan": r'\b[A-Z]{5}\d{4}[A-Z]\b',
        }

        self.hindi_names = [
            "rahul", "priya", "amit", "sneha", "vikram", "neha", "arjun", "pooja",
            "rohit", "divya", "karan", "anita", "sanjay", "meera", "vijay", "rekha",
            "ajay", "sunita", "manoj", "kavita", "deepak", "geeta", "rakesh", "asha",
            "suresh", "nisha", "mukesh", "sapna", "dinesh", "pushpa", "rajesh", "lata",
            "mahesh", "vidya", "ramesh", "anju", "sunil", "shima", "pawan", "mamta",
        ]

        self.places_india = [
            "mumbai", "delhi", "bangalore", "bengaluru", "chennai", "kolkata", "hyderabad",
            "pune", "ahmedabad", "jaipur", "lucknow", "kanpur", "nagpur", "indore",
            "thane", "bhopal", "patna", "vadodara", "ghaziabad", "ludhiana", "agra",
            "nashik", "faridabad", "meerut", "rajkot", "varanasi", "srinagar",
            "aurangabad", "dhanbad", "amritsar", "allahabad", "ranchi", "howrah",
            "coimbatore", "jabalpur", "gwalior", "vijayawada", "jodhpur", "madurai",
            "raipur", "kochi", "chandigarh", "thiruvananthapuram", "dehradun",
        ]

        self.food_items = [
            "chai", "coffee", "pizza", "burger", "biryani", "paneer", "roti", "dal",
            "rice", "samosa", "dosa", "idli", "paratha", "noodles", "pasta",
            "sandwich", "momos", "vada pav", "pav bhaji", "chole bhature",
            "uttapam", "kulcha", "naan", "tandoori", "butter chicken",
        ]

    def extract(self, text: str) -> dict:
        entities = {
            "emails": self._extract_pattern(text, "email"),
            "phones": self._extract_pattern(text, "phone"),
            "urls": self._extract_pattern(text, "url"),
            "dates": self._extract_dates(text),
            "times": self._extract_times(text),
            "numbers": self._extract_numbers(text),
            "currency": self._extract_currency(text),
            "names": self._extract_names(text),
            "places": self._extract_places(text),
            "food": self._extract_food(text),
            "persons_mentioned": [],
            "locations_mentioned": [],
        }

        entities["persons_mentioned"] = entities["names"]
        entities["locations_mentioned"] = entities["places"]

        entities["primary"] = self._get_primary_entity(entities)

        return entities

    def _extract_pattern(self, text: str, pattern_name: str) -> list[str]:
        pattern = self.patterns.get(pattern_name, "")
        if not pattern:
            return []
        matches = re.findall(pattern, text, re.IGNORECASE)
        return list(set(matches)) if matches else []

    def _extract_dates(self, text: str) -> list[dict]:
        dates = []

        date_patterns = [
            (r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})', "dmy"),
            (r'(\d{1,2})\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*(?:\s+(\d{2,4}))?', "text"),
        ]

        for pattern, fmt in date_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    if fmt == "dmy":
                        day, month, year = match.groups()
                        if len(year) == 2:
                            year = "20" + year
                        dates.append({
                            "raw": match.group(),
                            "day": int(day),
                            "month": int(month),
                            "year": int(year),
                        })
                except (ValueError, TypeError):
                    pass

        today = datetime.now()
        relative_dates = {
            "aaj": today,
            "kal": today + timedelta(days=1),
            "parson": today + timedelta(days=2),
            "today": today,
            "tomorrow": today + timedelta(days=1),
            "day after tomorrow": today + timedelta(days=2),
            "yesterday": today - timedelta(days=1),
        }

        text_lower = text.lower()
        for word, date in relative_dates.items():
            if word in text_lower:
                dates.append({
                    "raw": word,
                    "date": date.strftime("%Y-%m-%d"),
                    "relative": True,
                })

        return dates

    def _extract_times(self, text: str) -> list[dict]:
        times = []
        pattern = r'(\d{1,2}):(\d{2})\s*(am|pm|AM|PM)?'
        matches = re.finditer(pattern, text)

        for match in matches:
            hour, minute, period = match.groups()
            hour = int(hour)
            minute = int(minute)

            if period:
                period = period.lower()
                if period == "pm" and hour != 12:
                    hour += 12
                elif period == "am" and hour == 12:
                    hour = 0

            times.append({
                "raw": match.group(),
                "hour": hour,
                "minute": minute,
                "24h": f"{hour:02d}:{minute:02d}",
            })

        return times

    def _extract_numbers(self, text: str) -> list[dict]:
        numbers = []
        pattern = r'\b(\d+(?:\.\d+)?)\s*(hazaar|lakh|crore|k|m|b|thousand|million|billion)?\b'
        matches = re.finditer(pattern, text, re.IGNORECASE)

        for match in matches:
            num_str, multiplier = match.groups()
            num = float(num_str)

            if multiplier:
                multiplier = multiplier.lower()
                multipliers = {
                    "hazaar": 1000, "thousand": 1000, "k": 1000,
                    "lakh": 100000, "m": 1000000, "million": 1000000,
                    "crore": 10000000, "b": 1000000000, "billion": 1000000000,
                }
                num *= multipliers.get(multiplier, 1)

            numbers.append({
                "raw": match.group(),
                "value": num,
                "is_float": "." in num_str,
            })

        return numbers

    def _extract_currency(self, text: str) -> list[dict]:
        currencies = []
        pattern = r'(₹|Rs\.?|INR|\$|USD|€|EUR|£|GBP)\s*(\d+(?:,\d{3})*(?:\.\d+)?)'
        matches = re.finditer(pattern, text, re.IGNORECASE)

        symbol_map = {
            "₹": "INR", "rs": "INR", "inr": "INR",
            "$": "USD", "usd": "USD",
            "€": "EUR", "eur": "EUR",
            "£": "GBP", "gbp": "GBP",
        }

        for match in matches:
            symbol, amount = match.groups()
            amount_float = float(amount.replace(",", ""))
            currencies.append({
                "raw": match.group(),
                "amount": amount_float,
                "currency": symbol_map.get(symbol.lower(), symbol),
            })

        return currencies

    def _extract_names(self, text: str) -> list[str]:
        found_names = []
        text_lower = text.lower()

        for name in self.hindi_names:
            if name in text_lower:
                found_names.append(name.capitalize())

        name_patterns = [
            r'(?:mera naam|my name is|i am|i\'m|main|hoon)\s+([A-Z][a-z]+)',
            r'([A-Z][a-z]+)\s+(?:bolo|se baat|ko bhejo|naam)',
        ]

        for pattern in name_patterns:
            matches = re.findall(pattern, text)
            found_names.extend(matches)

        return list(set(found_names))

    def _extract_places(self, text: str) -> list[str]:
        found_places = []
        text_lower = text.lower()

        for place in self.places_india:
            if place in text_lower:
                found_places.append(place.capitalize())

        return list(set(found_places))

    def _extract_food(self, text: str) -> list[str]:
        found_food = []
        text_lower = text.lower()

        for food in self.food_items:
            if food in text_lower:
                found_food.append(food.capitalize())

        return list(set(found_food))

    def _get_primary_entity(self, entities: dict) -> Optional[str]:
        if entities["emails"]:
            return {"type": "email", "value": entities["emails"][0]}
        if entities["phones"]:
            return {"type": "phone", "value": entities["phones"][0]}
        if entities["dates"]:
            return {"type": "date", "value": entities["dates"][0]}
        if entities["times"]:
            return {"type": "time", "value": entities["times"][0]}
        if entities["currency"]:
            return {"type": "currency", "value": entities["currency"][0]}
        if entities["places"]:
            return {"type": "place", "value": entities["places"][0]}
        if entities["names"]:
            return {"type": "name", "value": entities["names"][0]}
        if entities["food"]:
            return {"type": "food", "value": entities["food"][0]}
        if entities["numbers"]:
            return {"type": "number", "value": entities["numbers"][0]}
        return None


entity_extractor = EntityExtractor()
