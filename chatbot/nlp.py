import re
from difflib import SequenceMatcher


HINDI_STOPWORDS = {
    "mai", "mein", "mera", "meri", "mere", "tu", "tum", "tumhara", "tumhari",
    "apna", "apni", "woh", "wo", "yeh", "ye", "kya", "kab", "kaha", "kaise",
    "kaun", "kaunsa", "kaunsi", "kyun", "kyu", "se", "ke", "ko", "ka", "ki",
    "me", "pe", "par", "hai", "ho", "hun", "hu", "tha", "thi", "the", "hoga",
    "hogi", "honge", "hain", "he", "hein", "na", "nahi", "nahin", "ek", "do",
    "aur", "ya", "to", "toh", "ki", "ke", "se", "ko", "ne", "par", "pe",
    "mein", "mai", "abhi", "phir", "bhi", "sirf", "bas", "chahiye", "karo",
    "batao", "bata", "suno", "suno", "bolo", "bol", "kar", "karna", "ho",
    "raha", "rahi", "rahe", "gaya", "gayi", "gaye", "aaya", "aayi", "aaye",
    "do", "de", "dega", "degi", "dunga", "dungi", "lunga", "lungi"
}

HINDI_TO_ROMAN = {
    "नमस्ते": "namaste",
    "कैसे": "kaise",
    "क्या": "kya",
    "मुझे": "mujhe",
    "तुम": "tum",
    "बहुत": "bahut",
    "अच्छा": "achha",
    "ठीक": "theek",
    "धन्यवाद": "dhanyavaad",
    "शुक्रिया": "shukriya",
    "मदद": "madad",
    "हाँ": "haan",
    "नहीं": "nahi",
    "है": "hai",
    "हो": "ho",
    "रहा": "raha",
    "रही": "rahi",
    "मैं": "mai",
    "आप": "aap",
    "मेरा": "mera",
    "मेरी": "meri",
    "मेरे": "mere",
    "तुम्हारा": "tumhara",
    "बोलो": "bolo",
    "बताओ": "batao",
    "समझ": "samajh",
    "जाओ": "jao",
    "आओ": "aao",
    "खुश": "khush",
    "दुखी": "dukhhi",
    "गुस्सा": "gussa",
    "बोर": "bore",
    "थकान": "thakan",
    "प्यार": "pyar",
    "दोस्त": "dost",
    "जिंदगी": "zindagi",
    "मतलब": "matlab",
    "क्यों": "kyun",
    "कब": "kab",
    "कहाँ": "kaha",
    "कौन": "kaun",
}


def transliterate_hindi(text: str) -> str:
    result = text
    for hindi, roman in HINDI_TO_ROMAN.items():
        result = result.replace(hindi, roman)
    return result


def preprocess(text: str) -> str:
    text = text.lower().strip()
    text = transliterate_hindi(text)
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def tokenize(text: str) -> list[str]:
    cleaned = preprocess(text)
    return [t for t in cleaned.split() if t not in HINDI_STOPWORDS and len(t) > 1]


def fuzzy_match(query: str, target: str, threshold: int = 70) -> bool:
    ratio = SequenceMatcher(None, query.lower(), target.lower()).ratio()
    if ratio * 100 >= threshold:
        return True
    q_words = query.lower().split()
    t_words = target.lower().split()
    for qw in q_words:
        if len(qw) < 4:
            continue
        for tw in t_words:
            if len(tw) < 4:
                continue
            if SequenceMatcher(None, qw, tw).ratio() * 100 >= threshold:
                return True
    return False


def similarity_score(text1: str, text2: str) -> int:
    return int(SequenceMatcher(None, text1.lower(), text2.lower()).ratio() * 100)


def contains_any(text: str, keywords: list[str]) -> bool:
    text_lower = text.lower()
    return any(kw in text_lower for kw in keywords)


def extract_name(text: str, after_words: list[str] = None) -> str | None:
    if after_words is None:
        after_words = ["mera naam", "mai hun", "main hun", "my name is", "i am", "i'm", "main hoon"]
    text_lower = text.lower()
    for word in after_words:
        idx = text_lower.find(word)
        if idx != -1:
            name_part = text[idx + len(word):].strip()
            name = name_part.split()[0] if name_part else None
            if name and len(name) > 1:
                return name.capitalize()
    return None


INTENSITY_LOW = {"thoda", "halka", "kabhi", "thodi", "kuch", "bas", "jaise"}
INTENSITY_HIGH = {"bahut", "ekdum", "zyada", "bohot", "sach", "bilkul", "poora", "poori", "sara", "sari", "totally", "really", "very"}

EMOTION_KEYWORDS = {
    "happy": ["khush", "happy", "achha", "maza", "mast", "badhiya", "awesome", "great", "nice", "amazing", "excellent", "wonderful"],
    "sad": ["sad", "dukhi", "dukh", "bura", "udas", "roya", "rona", "hurt", "broken", "toota", "toot gaya", "dil toota"],
    "angry": ["gussa", "angry", "irritate", "naraz", "krodh", "furious"],
    "frustrated": ["frustrated", "pareshan", "thak gaya", "nahi ho raha", "overwhelmed", "tang", "mood off"],
    "excited": ["excited", "josh", "waiting", "cant wait", "intezar"],
    "confused": ["confuse", "samajh nahi", "pata nahi", "unclear", "doubt"],
}


def detect_emotion_intensity(text: str) -> dict:
    text_lower = text.lower().strip()
    words = set(text_lower.split())

    detected_emotion = "neutral"
    intensity = "medium"

    for emotion, keywords in EMOTION_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                detected_emotion = emotion
                break
        if detected_emotion != "neutral":
            break

    has_low = bool(words & INTENSITY_LOW)
    has_high = bool(words & INTENSITY_HIGH)

    exclamation_count = text.count("!")
    caps_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)

    if has_high or exclamation_count >= 2 or caps_ratio > 0.3:
        intensity = "high"
    elif has_low:
        intensity = "low"

    return {
        "emotion": detected_emotion,
        "intensity": intensity,
    }
