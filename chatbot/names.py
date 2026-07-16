import random


NAME_MEANINGS = {
    "aadhya": {"meaning": "The beginning, First power", "origin": "Sanskrit"},
    "aanand": {"meaning": "Bliss, Happiness", "origin": "Sanskrit"},
    "aanya": {"meaning": "Grace, Favor", "origin": "Sanskrit"},
    "aarav": {"meaning": "Peaceful", "origin": "Sanskrit"},
    "adhira": {"meaning": "Restless, Quick", "origin": "Sanskrit"},
    "aditya": {"meaning": "Sun, Lord of day", "origin": "Sanskrit"},
    "amit": {"meaning": "Infinite, Boundless", "origin": "Sanskrit"},
    "ananya": {"meaning": "Unique, Matchless", "origin": "Sanskrit"},
    "anika": {"meaning": "Grace, Brilliance", "origin": "Sanskrit"},
    "ankita": {"meaning": "Marked, Auspicious", "origin": "Sanskrit"},
    "arjun": {"meaning": "Bright, Shining, White", "origin": "Sanskrit"},
    "avya": {"meaning": "Sun, Earth", "origin": "Sanskrit"},
    "deepa": {"meaning": "Light, Lamp", "origin": "Sanskrit"},
    "dev": {"meaning": "God, Divine", "origin": "Sanskrit"},
    "diya": {"meaning": "Lamp, Light", "origin": "Sanskrit"},
    "gauri": {"meaning": "Fair, White, Goddess Parvati", "origin": "Sanskrit"},
    "harsh": {"meaning": "Happiness, Joy", "origin": "Sanskrit"},
    "isha": {"meaning": "Goddess, Wealth", "origin": "Sanskrit"},
    "kabir": {"meaning": "Great, Noble", "origin": "Arabic"},
    "kavya": {"meaning": "Poetry, Wisdom", "origin": "Sanskrit"},
    "kiara": {"meaning": "Dark haired, Precious", "origin": "Italian/Sanskrit"},
    "lakshya": {"meaning": "Target, Goal", "origin": "Sanskrit"},
    "mahi": {"meaning": "Earth, Beautiful, Great", "origin": "Sanskrit/Persian"},
    "mohan": {"meaning": "Charming, Attractive", "origin": "Sanskrit"},
    "naina": {"meaning": "Eyes", "origin": "Sanskrit"},
    "neha": {"meaning": "Love, Affection", "origin": "Sanskrit"},
    "om": {"meaning": "Sacred sound, Universe", "origin": "Sanskrit"},
    "pranav": {"meaning": "Sacred syllable, Lord Vishnu", "origin": "Sanskrit"},
    "priya": {"meaning": "Beloved, Dear one", "origin": "Sanskrit"},
    "priyanka": {"meaning": "Beautiful, Cute", "origin": "Sanskrit"},
    "rahul": {"meaning": "Moon, Able, Efficient", "origin": "Sanskrit"},
    "rani": {"meaning": "Queen", "origin": "Sanskrit"},
    "riya": {"meaning": "Singer, Graceful", "origin": "Sanskrit"},
    "rohan": {"meaning": "Ascending, Blossoming", "origin": "Sanskrit"},
    "sakshi": {"meaning": "Witness", "origin": "Sanskrit"},
    "sarah": {"meaning": "Princess, Pure", "origin": "Hebrew/Sanskrit"},
    "shanti": {"meaning": "Peace", "origin": "Sanskrit"},
    "shreya": {"meaning": "Auspicious, Beautiful", "origin": "Sanskrit"},
    "soham": {"meaning": "I am He, Self-awareness", "origin": "Sanskrit"},
    "sonam": {"meaning": "Beautiful", "origin": "Tibetan/Sanskrit"},
    "sunita": {"meaning": "Good manners, Well-behaved", "origin": "Sanskrit"},
    "tara": {"meaning": "Star, Goddess", "origin": "Sanskrit"},
    "ujjwal": {"meaning": "Bright, Lustrous", "origin": "Sanskrit"},
    "vaishnavi": {"meaning": "Goddess Lakshmi", "origin": "Sanskrit"},
    "varun": {"meaning": "Water, Lord of sea", "origin": "Sanskrit"},
    "veer": {"meaning": "Brave, Warrior", "origin": "Sanskrit"},
    "vilas": {"meaning": "Play, Sport, Entertainment", "origin": "Sanskrit"},
    "vivaan": {"meaning": "First rays of sun", "origin": "Sanskrit"},
    "yash": {"meaning": "Fame, Glory", "origin": "Sanskrit"},
    "zara": {"meaning": "Princess, Flower", "origin": "Arabic/Sanskrit"},
    "anjali": {"meaning": "Divine offering, Gift", "origin": "Sanskrit"},
    "akash": {"meaning": "Sky, Open space", "origin": "Sanskrit"},
    "amit": {"meaning": "Infinite, Boundless", "origin": "Sanskrit"},
    "ankush": {"meaning": "Control, Goad", "origin": "Sanskrit"},
    "chandan": {"meaning": "Sandalwood", "origin": "Sanskrit"},
    "deepak": {"meaning": "Lamp, Light", "origin": "Sanskrit"},
    "gopal": {"meaning": "Cowherd, Lord Krishna", "origin": "Sanskrit"},
    "jayesh": {"meaning": "Winner of victory", "origin": "Sanskrit"},
    "karan": {"meaning": "Skillful, Friend", "origin": "Sanskrit"},
    "manoj": {"meaning": "Born of mind, Cupid", "origin": "Sanskrit"},
    "naveen": {"meaning": "New, Fresh", "origin": "Sanskrit"},
    "pooja": {"meaning": "Worship, Prayer", "origin": "Sanskrit"},
    "ravi": {"meaning": "Sun", "origin": "Sanskrit"},
    "sachin": {"meaning": "Pure, Honest", "origin": "Sanskrit"},
    "sneha": {"meaning": "Love, Affection", "origin": "Sanskrit"},
    "suresh": {"meaning": "Lord of Gods", "origin": "Sanskrit"},
    "uma": {"meaning": "Flax, Turmeric", "origin": "Sanskrit"},
    "vineet": {"meaning": "Humble, Polite", "origin": "Sanskrit"},
    "yogesh": {"meaning": "Lord of Yoga", "origin": "Sanskrit"},
}


def get_name_meaning(name: str) -> dict | None:
    name_lower = name.lower().strip()
    return NAME_MEANINGS.get(name_lower)


def search_names(query: str) -> list[dict]:
    query_lower = query.lower().strip()
    results = []
    for name, data in NAME_MEANINGS.items():
        if query_lower in name or query_lower in data["meaning"].lower():
            results.append({"name": name.capitalize(), **data})
    return results
