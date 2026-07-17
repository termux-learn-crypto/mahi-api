import json
from . import Plugin


class ShoppingPlugin(Plugin):
    def __init__(self):
        super().__init__("shopping", "Shopping assistance and price comparison", "1.0.0")
        self.commands = ["buy", "price", "shop", "discount", "offer", "compare"]
        self.keywords = ["buy", "price", "shop", "discount", "offer", "sale", "cheap", "kharid"]

    def can_handle(self, intent: str, message: str) -> bool:
        shopping_keywords = [
            "buy", "kharid", "price", "shop", "discount", "offer",
            "sale", "cheap", "sasta", "mahnga", "compare", "deal",
            "amazon", "flipkart", "myntra",
        ]
        msg_lower = message.lower()
        return any(kw in msg_lower for kw in shopping_keywords)

    def execute(self, user_id: str, message: str, context: dict) -> dict:
        msg_lower = message.lower()

        if any(word in msg_lower for word in ["compare", "tulna", "konsa"]):
            return self._compare_prices(message)
        elif any(word in msg_lower for word in ["deal", "offer", "discount", "sale"]):
            return self._get_deals()
        elif any(word in msg_lower for word in ["price", "kimat", "kitna"]):
            return self._get_price(message)
        else:
            return self._search_products(message)

    def _search_products(self, message: str) -> dict:
        import re
        product_match = re.search(r'(?:buy|kharid|shop|search)\s+(.+)', message, re.IGNORECASE)
        product = product_match.group(1).strip() if product_match else "product"

        return {
            "response": f"🛒 Searching for: {product}\n\n"
                       f"Results:\n"
                       f"1. {product} - ₹999 (Amazon)\n"
                       f"2. {product} - ₹1,299 (Flipkart)\n"
                       f"3. {product} - ₹899 (Meesho)\n\n"
                       f"Best price: ₹899 on Meesho\n\n"
                       f"Real API lagegi price check ke liye!",
            "command": {"type": "shopping_search", "query": product},
            "intent": "shopping",
        }

    def _compare_prices(self, message: str) -> dict:
        import re
        product_match = re.search(r'compare\s+(.+)', message, re.IGNORECASE)
        product = product_match.group(1).strip() if product_match else "product"

        return {
            "response": f"📊 Price Comparison: {product}\n\n"
                       f"Amazon:   ₹1,299 ⭐4.2\n"
                       f"Flipkart: ₹1,199 ⭐4.0\n"
                       f"Meesho:   ₹899  ⭐3.8\n"
                       f"JioMart:  ₹999  ⭐4.1\n\n"
                       f"Best Deal: Meesho @ ₹899\n"
                       f"Best Value: JioMart @ ₹999 (good rating)\n\n"
                       f"Real API lagegi!",
            "command": {"type": "shopping_compare", "product": product},
            "intent": "shopping",
        }

    def _get_deals(self) -> dict:
        return {
            "response": "🔥 Today's Top Deals:\n\n"
                       "1. iPhone 15 - ₹59,999 (15% off)\n"
                       "2. Samsung S24 - ₹49,999 (20% off)\n"
                       "3. Nike Shoes - ₹2,999 (40% off)\n"
                       "4. Sony Headphones - ₹4,999 (25% off)\n"
                       "5. MacBook Air - ₹89,999 (10% off)\n\n"
                       "Limited time offers!",
            "command": {"type": "shopping_deals"},
            "intent": "shopping",
        }

    def _get_price(self, message: str) -> dict:
        import re
        product_match = re.search(r'price\s+(?:of\s+)?(.+)', message, re.IGNORECASE)
        product = product_match.group(1).strip() if product_match else "product"

        return {
            "response": f"💰 Price Check: {product}\n\n"
                       f"Current Price: ₹1,499\n"
                       f"Lowest Price: ₹999 (3 months ago)\n"
                       f"Average Price: ₹1,299\n\n"
                       f"Price Trend: Stable\n"
                       f"Recommendation: {'Buy now!' if True else 'Wait for sale'}",
            "command": {"type": "shopping_price", "product": product},
            "intent": "shopping",
        }
