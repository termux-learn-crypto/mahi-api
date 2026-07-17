import re
from urllib.parse import quote
from . import Plugin


class NavigationPlugin(Plugin):
    def __init__(self):
        super().__init__(
            name="navigation",
            description="Google Maps navigation - get directions intent to open on Android",
            version="1.0.0",
        )
        self.commands = ["navigate", "directions", "map", "raasta", "kaise jaun"]
        self.keywords = [
            "navigate", "directions", "direction", "map", "raasta", "rasta",
            "kaise jaun", "kaise jaaye", "drive", "walking", "location",
            "google maps", "gps",
        ]

    def can_handle(self, intent: str, message: str) -> bool:
        if intent in ("navigation", "directions", "maps"):
            return True
        msg = message.lower()
        return any(kw in msg for kw in self.keywords)

    def execute(self, user_id: str, message: str, context: dict) -> dict:
        destination, origin, mode = self._parse_navigation(message)

        if not destination:
            return {
                "response": (
                    "🗺 Navigation ke liye destination batao!\n\n"
                    "Examples:\n"
                    "• 'navigate to Connaught Place Delhi'\n"
                    "• 'directions from Mumbai to Pune'\n"
                    "• 'kaise jaun India Gate'\n"
                    "• 'drive to airport'"
                ),
            }

        gmaps_url = self._build_google_maps_url(origin, destination, mode)
        directions_intent = self._build_directions_intent(origin, destination, mode)

        mode_display = {
            "driving": "🚗 Driving", "walking": "🚶 Walking",
            "bicycling": "🚴 Cycling", "transit": "🚌 Transit",
        }.get(mode, "🚗 Driving")

        origin_display = origin if origin else "Current Location"
        response = (
            f"🗺 Navigation Details:\n\n"
            f"📍 Se: {origin_display}\n"
            f"🏁 Tak: {destination}\n"
            f"🚗 Mode: {mode_display}\n\n"
            f"📱 Google Maps kholne ke liye action use karo!"
        )

        return {
            "response": response,
            "data": {
                "destination": destination,
                "origin": origin,
                "mode": mode,
                "google_maps_url": gmaps_url,
                "intent": directions_intent,
                "action": {
                    "type": "open_maps",
                    "url": gmaps_url,
                    "package": "com.google.android.apps.maps",
                },
            },
        }

    def _parse_navigation(self, message: str) -> tuple:
        msg = message.strip()
        destination = None
        origin = None
        mode = "driving"

        for m, keywords in {
            "driving": ["drive", "car", "gaadi", "car se"],
            "walking": ["walk", "pedestrian", "paidal", "chalke"],
            "bicycling": ["bike", "bicycle", "cycling", "cycle", "cycle se"],
            "transit": ["transit", "bus", "train", "metro", "public"],
        }.items():
            if any(kw in msg.lower() for kw in keywords):
                mode = m
                break

        origin_match = re.search(
            r'(?:from|se|starting from|origin)\s+(.+?)(?:\s+to\s+|\s+tak\s+|\s+pe\s+)',
            msg, re.I,
        )
        if origin_match:
            origin = origin_match.group(1).strip()
            origin = re.sub(
                r'\b(driving|walking|bike|car|paidal|chalke|cycle|bus|train|metro)\b',
                '', origin, flags=re.I
            ).strip()

        dest_match = re.search(
            r'(?:to|tak|pe|par|navigate|directions?|kaise jaun|kaise jaaye)\s+(.+)',
            msg, re.I,
        )
        if dest_match:
            destination = dest_match.group(1).strip()
            destination = re.sub(
                r'\b(driving|walking|bike|car|paidal|chalke|cycle|bus|train|metro|google maps|maps|directions?|navigate)\b',
                '', destination, flags=re.I
            ).strip()

        if not destination:
            patterns = [
                r'(?:navigate|directions?|map)\s+(?:to\s+)?(.+)',
                r'(?:kaise jaun|kaise jaaye|raasta|rasta)\s+(.+)',
                r'(.+?)\s+(?:ka|ki|ko)\s+(?:raasta|rasta|directions?)',
            ]
            for pattern in patterns:
                match = re.search(pattern, msg, re.I)
                if match:
                    destination = match.group(1).strip()
                    break

        if destination:
            destination = destination.rstrip('?!.,')
        if origin:
            origin = origin.rstrip('?!.,')

        return destination, origin, mode

    @staticmethod
    def _build_google_maps_url(origin: str | None, destination: str, mode: str) -> str:
        base = "https://www.google.com/maps/dir/"
        mode_param = {"driving": "", "walking": "walking", "bicycling": "bicycling", "transit": "transit"}
        params = mode_param.get(mode, "")

        if origin:
            url = f"{base}{quote(origin)}/{quote(destination)}"
        else:
            url = f"{base}/{quote(destination)}"

        if params:
            url += f"?travelmode={params}"
        return url

    @staticmethod
    def _build_directions_intent(origin: str | None, destination: str, mode: str) -> dict:
        gmaps_package = "com.google.android.apps.maps"
        if origin:
            uri = f"google.navigation:q={quote(destination)}&daddr={quote(origin)}&mode={mode}"
        else:
            uri = f"google.navigation:q={quote(destination)}&mode={mode}"
        return {
            "action": "android.intent.action.VIEW",
            "data": uri,
            "package": gmaps_package,
        }
