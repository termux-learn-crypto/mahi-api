import json
import random
from datetime import datetime, timedelta
from . import Plugin


class TravelPlugin(Plugin):
    def __init__(self):
        super().__init__("travel", "Travel planning and suggestions", "1.0.0")
        self.commands = ["plan trip", "flight", "hotel", "travel", "vacation"]
        self.keywords = ["travel", "trip", "flight", "hotel", "vacation", "visit", "ghumna", "tour"]

        self.destinations = {
            "beach": [
                {"name": "Goa", "best_time": "Oct-Mar", "budget": "₹15,000-30,000"},
                {"name": "Kerala", "best_time": "Sep-Mar", "budget": "₹20,000-40,000"},
                {"name": "Andaman", "best_time": "Oct-May", "budget": "₹25,000-50,000"},
            ],
            "mountain": [
                {"name": "Manali", "best_time": "Mar-Jun, Dec-Jan", "budget": "₹12,000-25,000"},
                {"name": "Shimla", "best_time": "Mar-Jun", "budget": "₹10,000-20,000"},
                {"name": "Darjeeling", "best_time": "Apr-Jun, Oct-Dec", "budget": "₹8,000-18,000"},
            ],
            "heritage": [
                {"name": "Rajasthan", "best_time": "Oct-Mar", "budget": "₹15,000-35,000"},
                {"name": "Agra", "best_time": "Oct-Mar", "budget": "₹8,000-15,000"},
                {"name": "Varanasi", "best_time": "Oct-Mar", "budget": "₹6,000-12,000"},
            ],
        }

    def can_handle(self, intent: str, message: str) -> bool:
        travel_keywords = [
            "travel", "trip", "flight", "hotel", "vacation", "visit",
            "ghumna", "tour", "holiday", "journey", "destination",
            "beach", "mountain", "heritage",
        ]
        msg_lower = message.lower()
        return any(kw in msg_lower for kw in travel_keywords)

    def execute(self, user_id: str, message: str, context: dict) -> dict:
        msg_lower = message.lower()

        if any(word in msg_lower for word in ["flight", "udaan", "plane"]):
            return self._search_flights(message)
        elif any(word in msg_lower for word in ["hotel", "stays", "raha"]):
            return self._search_hotels(message)
        elif any(word in msg_lower for word in ["plan", "yatra", "vacation", "holiday"]):
            return self._plan_trip(message)
        elif any(word in msg_lower for word in ["beach", "samundar", "sea"]):
            return self._suggest_destination("beach")
        elif any(word in msg_lower for word in ["mountain", "pahad", "hill"]):
            return self._suggest_destination("mountain")
        elif any(word in msg_lower for word in ["heritage", "temple", "historical"]):
            return self._suggest_destination("heritage")
        else:
            return self._get_travel_tips()

    def _search_flights(self, message: str) -> dict:
        return {
            "response": "✈️ Flight Search:\n\n"
                       "Delhi → Mumbai:\n"
                       "1. IndiGo - ₹4,500 (6:00 AM)\n"
                       "2. Air India - ₹5,200 (9:30 AM)\n"
                       "3. SpiceJet - ₹4,100 (2:00 PM)\n\n"
                       "Cheapest: ₹4,100 (SpiceJet)\n\n"
                       "Real API lagegi flight search ke liye!",
            "command": {"type": "travel_flights"},
            "intent": "travel",
        }

    def _search_hotels(self, message: str) -> dict:
        return {
            "response": "🏨 Hotel Search:\n\n"
                       "Mumbai Hotels:\n"
                       "1. Taj Mahal Palace - ₹12,000/night ⭐5\n"
                       "2. Oberoi Trident - ₹8,000/night ⭐5\n"
                       "3. ITC Grand - ₹6,000/night ⭐4\n"
                       "4. Budget Stay - ₹1,500/night ⭐3\n\n"
                       "Book on MakeMyTrip for best prices!",
            "command": {"type": "travel_hotels"},
            "intent": "travel",
        }

    def _plan_trip(self, message: str) -> dict:
        return {
            "response": "📋 Trip Planner:\n\n"
                       "Duration: 3-5 days\n"
                       "Budget: ₹20,000-40,000\n\n"
                       "Suggested Itinerary:\n"
                       "Day 1: Arrival + Local Sightseeing\n"
                       "Day 2: Main Attractions\n"
                       "Day 3: Adventure/Activity\n"
                       "Day 4: Shopping + Relax\n"
                       "Day 5: Departure\n\n"
                       "Where jaana hai? Beach, Mountain, ya Heritage?",
            "command": {"type": "travel_plan"},
            "intent": "travel",
        }

    def _suggest_destination(self, category: str) -> dict:
        destinations = self.destinations.get(category, self.destinations["beach"])
        dest = random.choice(destinations)

        return {
            "response": f"📍 {category.title()} Destination: {dest['name']}\n\n"
                       f"Best Time: {dest['best_time']}\n"
                       f"Budget: {dest['budget']}\n\n"
                       f"Highlights:\n"
                       f"• Beautiful scenery\n"
                       f"• Local cuisine\n"
                       f"• Cultural experience\n\n"
                       f"Plan karein?",
            "command": {"type": "travel_suggest", "destination": dest["name"]},
            "intent": "travel",
        }

    def _get_travel_tips(self) -> dict:
        return {
            "response": "🌍 Travel Tips:\n\n"
                       "1. Book flights 2-3 weeks in advance\n"
                       "2. Carry basic medicines\n"
                       "3. Keep digital copies of documents\n"
                       "4. Learn few local phrases\n"
                       "5. Respect local customs\n\n"
                       "Kya help chahiye? Flights, Hotels, ya Destinations?",
            "command": {"type": "travel_tips"},
            "intent": "travel",
        }
