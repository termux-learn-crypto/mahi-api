import re
from . import Plugin


class UnitConverterPlugin(Plugin):
    CONVERSIONS = {
        ("celsius", "fahrenheit"): lambda x: x * 9 / 5 + 32,
        ("celsius", "kelvin"): lambda x: x + 273.15,
        ("fahrenheit", "celsius"): lambda x: (x - 32) * 5 / 9,
        ("fahrenheit", "kelvin"): lambda x: (x - 32) * 5 / 9 + 273.15,
        ("kelvin", "celsius"): lambda x: x - 273.15,
        ("kelvin", "fahrenheit"): lambda x: (x - 273.15) * 9 / 5 + 32,
        ("kg", "lb"): lambda x: x * 2.20462,
        ("kg", "oz"): lambda x: x * 35.274,
        ("lb", "kg"): lambda x: x * 0.453592,
        ("lb", "oz"): lambda x: x * 16,
        ("oz", "kg"): lambda x: x * 0.0283495,
        ("oz", "lb"): lambda x: x / 16,
        ("km", "miles"): lambda x: x * 0.621371,
        ("km", "meters"): lambda x: x * 1000,
        ("miles", "km"): lambda x: x * 1.60934,
        ("meters", "km"): lambda x: x / 1000,
        ("miles", "meters"): lambda x: x * 1609.34,
        ("meters", "miles"): lambda x: x / 1609.34,
        ("liters", "ml"): lambda x: x * 1000,
        ("liters", "gallons"): lambda x: x * 0.264172,
        ("ml", "liters"): lambda x: x / 1000,
        ("ml", "gallons"): lambda x: x * 0.000264172,
        ("gallons", "liters"): lambda x: x * 3.78541,
        ("gallons", "ml"): lambda x: x * 3785.41,
    }

    ALIASES = {
        "c": "celsius", "celsius": "celsius", "°c": "celsius", "centigrade": "celsius",
        "f": "fahrenheit", "fahrenheit": "fahrenheit", "°f": "fahrenheit",
        "k": "kelvin", "kelvin": "kelvin", "°k": "kelvin",
        "kg": "kg", "kilogram": "kg", "kilograms": "kg", "kilo": "kg", "kilos": "kg",
        "lb": "lb", "lbs": "lb", "pound": "lb", "pounds": "lb",
        "oz": "oz", "ounce": "oz", "ounces": "oz",
        "km": "km", "kilometer": "km", "kilometers": "km", "kms": "km",
        "miles": "miles", "mile": "miles", "mi": "miles",
        "meters": "meters", "meter": "meters", "m": "meters", "metre": "meters", "metres": "meters",
        "l": "liters", "liter": "liters", "liters": "liters", "litre": "liters", "litres": "liters",
        "ml": "ml", "milliliter": "ml", "milliliters": "ml", "millilitre": "ml",
        "gal": "gallons", "gallons": "gallons", "gallon": "gallons",
    }

    UNIT_LABELS = {
        "celsius": "°C", "fahrenheit": "°F", "kelvin": "K",
        "kg": "kg", "lb": "lb", "oz": "oz",
        "km": "km", "miles": "miles", "meters": "m",
        "liters": "L", "ml": "ml", "gallons": "gal",
    }

    def __init__(self):
        super().__init__(
            name="unit_converter",
            description="Convert units - temperature, weight, distance, volume",
            version="1.0.0",
        )
        self.commands = ["convert", "unit", "temperature", "weight", "distance", "volume"]
        self.keywords = [
            "convert", "unit", "temperature", "celsius", "fahrenheit",
            "kg", "pound", "miles", "kilometer", "liter", "gallon",
            "weight", "distance", "volume", "kitna",
        ]

    def can_handle(self, intent: str, message: str) -> bool:
        if intent == "unit_convert":
            return True
        msg = message.lower()
        return any(kw in msg for kw in self.keywords)

    def execute(self, user_id: str, message: str, context: dict) -> dict:
        msg = message.lower().strip()
        num_match = re.search(r'([\d.]+)', msg)
        if not num_match:
            return {
                "response": (
                    "📏 Unit conversion kaise karu?\n\n"
                    "Examples:\n"
                    "• '30 celsius to fahrenheit'\n"
                    "• '75 kg to pounds'\n"
                    "• '100 miles to km'\n"
                    "• '5 liters to gallons'"
                ),
            }

        amount = float(num_match.group(1))
        words = re.findall(r'[a-z°]+', msg)

        from_unit = None
        to_unit = None
        candidates = []

        for w in words:
            resolved = self.ALIASES.get(w)
            if resolved:
                candidates.append(resolved)

        if len(candidates) >= 2:
            from_unit = candidates[0]
            to_unit = candidates[1]
        elif len(candidates) == 1:
            from_unit = candidates[0]
            to_unit = self._auto_target(from_unit)
            if not to_unit:
                return {"response": f"Kisme convert karna hai '{self.UNIT_LABELS.get(from_unit, from_unit)}' se? Target batao!"}

        if from_unit and to_unit:
            key = (from_unit, to_unit)
            converter = self.CONVERSIONS.get(key)
            if converter:
                result = converter(amount)
                from_label = self.UNIT_LABELS.get(from_unit, from_unit)
                to_label = self.UNIT_LABELS.get(to_unit, to_unit)
                return {
                    "response": f"📏 {amount:g} {from_label} = {result:g} {to_label}",
                    "data": {
                        "amount": amount, "from": from_unit,
                        "to": to_unit, "result": round(result, 6),
                    },
                }
            return {"response": f"Ye conversion support nahi hoti: {from_unit} → {to_unit} 😅"}

        return {
            "response": (
                "Samajh nahi aaya! Aise likho:\n"
                "• '30 c to f' (temperature)\n"
                "• '75 kg to lb' (weight)\n"
                "• '100 km to miles' (distance)\n"
                "• '5 l to gallons' (volume)"
            ),
        }

    def _auto_target(self, from_unit: str) -> str | None:
        groups = [
            ["celsius", "fahrenheit", "kelvin"],
            ["kg", "lb", "oz"],
            ["km", "miles", "meters"],
            ["liters", "ml", "gallons"],
        ]
        for group in groups:
            if from_unit in group:
                for u in group:
                    if u != from_unit:
                        return u
        return None
