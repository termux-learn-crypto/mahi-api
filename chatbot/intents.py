from dataclasses import dataclass, field
from .nlp import fuzzy_match


@dataclass
class Intent:
    name: str
    keywords: list[str] = field(default_factory=list)
    phrases: list[str] = field(default_factory=list)
    follow_ups: list[str] = field(default_factory=list)
    priority: int = 0


INTENTS = [
    Intent(
        name="greeting",
        keywords=["namaste", "hello", "hi", "hey", "hii", "helo", "sup", "yo", "kaise", "kaisa", "kaisi", "haal", "khabar", "ram ram", "radhe radhe", "good morning", "good evening", "good night"],
        phrases=["kaise ho", "kaisa hai", "kaisi ho", "kya haal", "kaise ho tum", "kaisa chal", "sup", "kya scene", "hello kaise ho", "namaste kaise ho"],
    ),
    Intent(
        name="identity",
        keywords=["kaun", "name", "who", "tumhara", "tera"],
        phrases=["tumhara naam kya hai", "tera naam kya", "kaun ho tum", "naam batao", "naam kya hai", "who are you", "kya naam hai"],
    ),
    Intent(
        name="user_name",
        keywords=["mera naam", "my name"],
        phrases=["mera naam", "my name is", "mera naam kya hai", "my name is"],
        priority=20,
    ),
    Intent(
        name="how_are_you",
        keywords=["kaise", "ho", "tum", "haal", "khabar"],
        phrases=["kaise ho", "kaisa hai", "kaisi ho", "tum kaise ho", "kya haal hai", "how are you"],
    ),
    Intent(
        name="emotion_happy",
        keywords=["khush", "happy", "achha", "maza", "majja", "mast", "badhiya", "lajawab", "zabardast", "fantastic", "awesome", "great"],
        phrases=["bahut khush hu", "maza aa gaya", "ekdum mast", "bahut achha lag", "feel good", "amazing"],
    ),
    Intent(
        name="emotion_sad",
        keywords=["dukh", "sad", "dukhi", "giraya", "roya", "rona", "pareshan", "takleef", "dard", "hurt", "broken", "toot", "udas", "hil", "toot gaya"],
        phrases=["mujhe dukh hai", "bahut bura lag", "mann udas", "dil toota", "feeling sad", "dukhi hu", "bahut bura laga"],
    ),
    Intent(
        name="emotion_angry",
        keywords=["gussa", "angry", "naraz", "krodh", "gussa hai", "irritate", "frustrate"],
        phrases=["mujhe gussa aa", "bahut gussa hai", "irritate ho", "frustrated hu"],
    ),
    Intent(
        name="emotion_bored",
        keywords=["bore", "boring", "alas", "waqt", "khali", "free", "lonely", "akela", "tanhai"],
        phrases=["bore ho raha", "bore hu", "kuch nahi ho raha", "waqt nahi kat raha", "feel bored"],
    ),
    Intent(
        name="compliment",
        keywords=["achhe", "achhi", "smart", "cute", "pyaara", "sundar", "lajawab", "kamaal", "best", "awesome", "wah", "mast", "zabardast"],
        phrases=["tum bahut achhe ho", "tum smart ho", "tum pyaari ho", "you are best", "tum kamaal ho", "tum bahut achhi ho", "tum bahut achhe ho"],
    ),
    Intent(
        name="thanks",
        keywords=["shukriya", "dhanyavaad", "thanks", "thank", "meherbani", "abhari"],
        phrases=["shukriya", "thank you", "bahut dhanyavaad", "thanks a lot"],
    ),
    Intent(
        name="joke",
        keywords=["joke", "jokes", "hasao", "mazaak", "mazak", "funny", "laugh", "hans"],
        phrases=["joke sunao", "kuch hasao", "mazaak karo", "funny sunao", "tell me a joke"],
    ),
    Intent(
        name="motivation",
        keywords=["motivation", "motivate", "hosla", "himmat", "inspire", "prerna", "josh"],
        phrases=["motivate karo", "hosla do", "kuch bolo", "inspire karo", "need motivation"],
    ),
    Intent(
        name="health",
        keywords=["neend", "dard", "thakan", "bimar", "sick", "fever", "cold", "khasi", "takleef", "health", "sehat"],
        phrases=["neend nahi aa rahi", "sar dard hai", "pet dard", "thak gaya", "bimar hu", "fever hai"],
    ),
    Intent(
        name="time",
        keywords=["time", "waqt", "samay", "kitne", "baje"],
        phrases=["kya time hai", "kitne baje", "time kya hai", "what time is it"],
    ),
    Intent(
        name="date",
        keywords=["date", "din", "tarikh", "aaj", "day", "month", "mahina", "saal", "year"],
        phrases=["aaj kya hai", "tarikh kya hai", "aaj ka date", "what is the date", "kaun sa din hai"],
    ),
    Intent(
        name="weather",
        keywords=["mausam", "weather", "barish", "dhoop", "thand", "garmi", "temperature"],
        phrases=["mausam kaisa hai", "barish ho rahi", "weather kaisa hai", "garmi hai ya thand"],
    ),
    Intent(
        name="love",
        keywords=["pyar", "love", "ishq", "mohabbat", "dil", "heart"],
        phrases=["mujhe pyar hai", "i love you", "tumse pyar hai", "love you"],
    ),
    Intent(
        name="purpose",
        keywords=["kaam", "purpose", "kya karti", "kya karte", "role", "kaam karti"],
        phrases=["tumhara kaam kya hai", "tum kya karti ho", "tumhara purpose kya hai", "what do you do"],
    ),
    Intent(
        name="capability",
        keywords=["kya", "kar", "sakti", "skti", "capability", "features", "ability"],
        phrases=["tum kya kar sakti ho", "kya kar sakti ho", "tumhari features", "what can you do"],
    ),
    Intent(
        name="bye",
        keywords=["bye", "alvida", "tata", "chalo", "jana", "chalta", "goodbye", "see you"],
        phrases=["bye bye", "alvida", "chalo bye", "tata", "good bye", "see you later"],
    ),
    Intent(
        name="life",
        keywords=["zindagi", "life", "jeevan", "jee", "exist", "meaning"],
        phrases=["zindagi kya hai", "life kya hai", "meaning of life", "hum kyu jeete hain"],
    ),
    Intent(
        name="knowledge",
        keywords=["pata", "jankari", "info", "information", "batao", "tell", "explain"],
        phrases=["mujhe batao", "kya pata hai", "tell me about", "explain karo"],
    ),
    Intent(
        name="tech",
        keywords=["tech", "technology", "ai", "coding", "programming", "computer", "phone", "app", "software"],
        phrases=["technology kya hai", "ai kya hai", "coding sikhao", "tech news"],
    ),
    Intent(
        name="music",
        keywords=["gaana", "song", "music", "gana", "suno", "sunao"],
        phrases=["gaana sunao", "kuch sunao", "music lagaao", "koi gaana"],
    ),
    Intent(
        name="food",
        keywords=["khana", "food", "bhookh", "khana hai", "recipe"],
        phrases=["kuch khana hai", "bhookh lagi hai", "kya khayein", "recipe batao"],
    ),
    Intent(
        name="fear",
        keywords=["dar", "fear", "scared", "darr", "khauf", "ghabra", "dar lag"],
        phrases=["mujhe dar lag raha", "i am scared", "darr lagta hai", "dar lag raha hai"],
        priority=5,
    ),
    Intent(
        name="insult",
        keywords=["bewakoof", "stupid", "pagal", "galat", "bad", "kharab", "bura"],
        phrases=["tum bewakoof ho", "tum pagal ho", "kharab ho"],
    ),
    Intent(
        name="celebration",
        keywords=["celebrate", "party", "jeet", "win", "success", "ban gaya", "ho gaya", "milega", "congratulations", "congrats"],
        phrases=["kaam ban gaya", "jeet gaye", "success mil gayi", "ho gaya kaam", "party karo", "celebrate karo"],
    ),
    Intent(
        name="gossip",
        keywords=["bata", "sunao", "kya hua", "khabar", "story", "happened"],
        phrases=["kya hua", "batao kya hua", "sunao kya hua", "khabar kya hai", "kya scene hai"],
    ),
    Intent(
        name="advice",
        keywords=["suggest", "advice", "kya karu", "kya sahi hai", "guidance", "rai", "suggestion"],
        phrases=["kya karu", "kya sahi hai", "suggest karo", "advice do", "help me decide", "kya karna chahiye"],
    ),
    Intent(
        name="frustration",
        keywords=["frustrated", "pareshan", "thak gaya", "nahi ho raha", "overwhelmed", "tang", "mood off"],
        phrases=["nahi ho raha", "frustrated hu", "pareshan hu", "thak gaya hu", "mood off hai", "sab kharab hai"],
    ),
    Intent(
        name="confusion",
        keywords=["samajh nahi", "confuse", "unclear", "pata nahi", "confused"],
        phrases=["samajh nahi aaya", "confuse ho raha hu", "pata nahi kya karu", "kya hai ye"],
    ),
    Intent(
        name="story",
        keywords=["story", "kahani", "sunao", "fairy tale", "tale"],
        phrases=["story sunao", "kahani sunao", "kuch sunao", "kuch batao"],
    ),
    Intent(
        name="riddle",
        keywords=["puzzle", "riddle", "paheli", "dimag lagao"],
        phrases=["puzzle do", "riddle sunao", "paheli batao", "dimag lagao"],
    ),
    Intent(
        name="miss_you",
        keywords=["miss", "yaad", "kahan", "kaha", "gayab", "long time"],
        phrases=["miss you", "yaad aa rahi", "kahan ho", "kaha gaye", "long time no see"],
    ),
    Intent(
        name="sleepy",
        keywords=["neend", "sounga", "so jao", "good night", "alvida raat", "so raha"],
        phrases=["neend aa rahi", "so jao", "good night", "so raha hu", "raat ho gayi"],
    ),
    Intent(
        name="morning",
        keywords=["good morning", "subah", "uth gaya", "morning"],
        phrases=["good morning", "subah ho gayi", "uth gaya hu", "morning"],
    ),
    Intent(
        name="daily_fact",
        keywords=["fact", "facts", "kuch pata", "interesting fact", "did you know"],
        phrases=["fact sunao", "kuch fact batao", "interesting fact", "did you know", "kuch pata hai"],
    ),
    Intent(
        name="quote",
        keywords=["quote", "quotes", "vachan", "kathan", "suvichar"],
        phrases=["quote sunao", "kuch quote batao", "suvichar sunao", "motivational quote"],
    ),
    Intent(
        name="tongue_twister",
        keywords=["tongue twister", "ultrajhulha", "jibba kabba"],
        phrases=["tongue twister sunao", "tongue twister batao", "ultrajhulha batao", "jibba kabba sunao"],
        priority=10,
    ),
    Intent(
        name="name_meaning",
        keywords=["naam ka matlab", "name meaning", "naam ka arth"],
        phrases=["naam ka matlab", "meaning of", "naam ka arth", "ka matlab kya hai", "ka meaning batao", "ka arth"],
        priority=20,
    ),
    Intent(
        name="would_you",
        keywords=["would you rather", "kya karoge", "choose karo"],
        phrases=["would you rather", "kya karoge tum", "choose karo"],
    ),
    Intent(
        name="truth_lie",
        keywords=["truth lie", "two truths", "sach jhooth"],
        phrases=["two truths one lie", "sach jhooth batao", "truth lie khelo"],
    ),
    Intent(
        name="affirmation",
        keywords=["affirm", "positive", "self love", "self care", "confidence"],
        phrases=["positive bolo", "affirmation do", "self love", "confidence badhao"],
    ),
    Intent(
        name="calculator",
        keywords=["calculate", "calc", "solve", "jod", "guna", "bhaag", "minus", "plus", "sqrt", "square", "cube", "percentage", "percent"],
        phrases=["calculate karo", "solve karo", "kitna hota hai", "batao kitna", "jod ke batao", "square root", "cube root", "percentage"],
        priority=18,
    ),
    Intent(
        name="translator",
        keywords=["translate", "anuvaad", "tarjuma", " matlab"],
        phrases=["translate karo", "english mein bolo", "hindi mein bolo", " matlab kya hai", "ka matlab kya"],
        priority=18,
    ),
    Intent(
        name="mobile_command",
        keywords=["youtube", "whatsapp", "call", "sms", "alarm", "open", "kholo", "brightness", "wifi", "bluetooth", "volume", "share", "app", "chalao", "play store", "spotify", "instagram", "facebook", "chrome", "camera", "gallery", "maps", "settings"],
        phrases=["youtube pe", "whatsapp pe", "call karo", "alarm lagao", "brightness badhao", "wifi on", "bluetooth on", "volume up", "app kholo", "kholo", "share karo", "chalao"],
        priority=12,
    ),
]


def classify_intent(text: str) -> str:
    text_lower = text.lower().strip()
    words = set(text_lower.split())
    scores: dict[str, int] = {}

    for intent in INTENTS:
        score = 0
        for phrase in intent.phrases:
            if phrase in text_lower:
                score += 30
            elif len(phrase) > 8 and fuzzy_match(text_lower, phrase, 90):
                score += 15

        for keyword in intent.keywords:
            if keyword in words:
                score += 20
            elif len(keyword) >= 4 and keyword in text_lower:
                score += 20
            elif len(keyword) > 5 and fuzzy_match(text_lower, keyword, 90):
                score += 10

        if score > 0:
            score += intent.priority
            scores[intent.name] = score

    if not scores:
        return "unknown"

    return max(scores, key=scores.get)
