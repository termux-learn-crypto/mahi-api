import re
import requests
from . import Plugin


class CurrencyPlugin(Plugin):
    CURRENCIES = {
        "inr": {"symbol": "₹", "name": "Indian Rupee", "hi": "Rupaye"},
        "usd": {"symbol": "$", "name": "US Dollar", "hi": "Dollar"},
        "eur": {"symbol": "€", "name": "Euro", "hi": "Euro"},
        "gbp": {"symbol": "£", "name": "British Pound", "hi": "Pound"},
        "jpy": {"symbol": "¥", "name": "Japanese Yen", "hi": "Yen"},
        "cny": {"symbol": "¥", "name": "Chinese Yuan", "hi": "Yuan"},
        "aud": {"symbol": "A$", "name": "Australian Dollar", "hi": "Australian Dollar"},
        "cad": {"symbol": "C$", "name": "Canadian Dollar", "hi": "Canadian Dollar"},
        "chf": {"symbol": "Fr", "name": "Swiss Franc", "hi": "Swiss Franc"},
        "sgd": {"symbol": "S$", "name": "Singapore Dollar", "hi": "Singapore Dollar"},
        "aed": {"symbol": "د.إ", "name": "UAE Dirham", "hi": "Dirham"},
        "sar": {"symbol": "﷼", "name": "Saudi Riyal", "hi": "Riyal"},
        "npr": {"symbol": "Rs", "name": "Nepalese Rupee", "hi": "Nepali Rupaye"},
        "pkr": {"symbol": "Rs", "name": "Pakistani Rupee", "hi": "Pakistani Rupaye"},
        "bdt": {"symbol": "৳", "name": "Bangladeshi Taka", "hi": "Taka"},
        "krw": {"symbol": "₩", "name": "South Korean Won", "hi": "Won"},
        "rub": {"symbol": "₽", "name": "Russian Ruble", "hi": "Ruble"},
        "brl": {"symbol": "R$", "name": "Brazilian Real", "hi": "Real"},
    }

    ALIASES = {
        "rupaye": "inr", "rupees": "inr", "rs": "inr", "₹": "inr",
        "dollar": "usd", "dollars": "usd", "$": "usd", "buck": "usd", "bucks": "usd",
        "euro": "eur", "euros": "eur", "€": "eur",
        "pound": "gbp", "pounds": "gbp", "£": "gbp",
        "yen": "jpy", "¥": "jpy",
        "dirham": "aed", "dirhams": "aed",
        "riyal": "sar", "riyals": "sar",
        "yuan": "cny",
    }

    def __init__(self):
        super().__init__(
            name="currency",
            description="Currency conversion - convert between INR, USD, EUR, GBP, JPY and more",
            version="1.0.0",
        )
        self.commands = ["convert", "currency", "exchange rate", "paise"]
        self.keywords = [
            "convert", "currency", "exchange", "rate", "paise", "rupaye",
            "dollar", "euro", "pound", "yen", "kitna", "how much",
        ]

    def can_handle(self, intent: str, message: str) -> bool:
        if intent in ("currency", "convert"):
            return True
        msg = message.lower()
        has_currency = any(c in msg for c in list(self.ALIASES.keys()) + list(self.CURRENCIES.keys()))
        has_convert = any(kw in msg for kw in ["convert", "kitna", "how much", "paise", "rate"])
        return has_currency and has_convert

    def execute(self, user_id: str, message: str, context: dict) -> dict:
        msg = message.lower().replace(",", "").strip()
        amount, from_curr, to_curr = self._parse_conversion(msg)

        if amount is None or not from_curr or not to_curr:
            return {
                "response": (
                    "💱 Currency conversion kaise karu?\n\n"
                    "Examples:\n"
                    "• '100 dollars to INR'\n"
                    "• '5000 rupees to USD'\n"
                    "• '1000 yen to INR'\n"
                    "• 'convert 200 EUR to INR'"
                ),
            }

        try:
            url = f"https://api.exchangerate-api.com/v4/latest/{from_curr.upper()}"
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            rates = data.get("rates", {})

            to_rate = rates.get(to_curr.upper())
            if not to_rate:
                return {"response": f"'{to_curr.upper()}' currency support nahi karti! 😅"}

            result = amount * to_rate
            from_info = self.CURRENCIES.get(from_curr.lower(), {})
            to_info = self.CURRENCIES.get(to_curr.lower(), {})
            from_sym = from_info.get("symbol", from_curr.upper())
            to_sym = to_info.get("symbol", to_curr.upper())

            inv_rate = 1 / to_rate if to_rate else 0
            formatted = f"{result:,.2f}"
            from_formatted = f"{amount:,.2f}"

            response = (
                f"💱 Currency Conversion:\n\n"
                f"{from_sym}{from_formatted} {from_curr.upper()} = {to_sym}{formatted} {to_curr.upper()}\n\n"
                f"📊 Exchange Rate:\n"
                f"1 {from_curr.upper()} = {to_sym}{to_rate:.4f} {to_curr.upper()}\n"
                f"1 {to_curr.upper()} = {from_sym}{inv_rate:.4f} {from_curr.upper()}\n\n"
                f"📅 Rate: {data.get('date', 'aaj ka')}"
            )
            return {
                "response": response,
                "data": {
                    "amount": amount, "from": from_curr.upper(),
                    "to": to_curr.upper(), "result": round(result, 2),
                    "rate": to_rate,
                },
            }

        except requests.Timeout:
            return {"response": "Exchange rate service slow hai! Thodi der baad try karo. ⏳"}
        except requests.RequestException:
            return {"response": "Currency rate lene mein dikkat! Baad mein try karo. 😔"}

    def _parse_conversion(self, msg: str) -> tuple:
        amount = None
        from_curr = None
        to_curr = None

        num_match = re.search(r'([\d.]+)', msg)
        if num_match:
            amount = float(num_match.group(1))

        for alias, code in self.ALIASES.items():
            if alias in msg:
                if from_curr is None:
                    from_curr = code
                else:
                    to_curr = code
                    break

        if not to_curr:
            for code in self.CURRENCIES:
                if code in msg and code != from_curr:
                    if from_curr is None:
                        from_curr = code
                    else:
                        to_curr = code
                        break

        if from_curr and not to_curr:
            to_curr = "inr" if from_curr != "inr" else "usd"

        return amount, from_curr, to_curr
