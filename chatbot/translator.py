import random


HINDI_TO_ENGLISH = {
    "namaste": "Hello",
    "dhanyavaad": "Thank you",
    "shukriya": "Thanks",
    "kripya": "Please",
    "haan": "Yes",
    "nahi": "No",
    "acha": "Good",
    "bura": "Bad",
    "kya haal hai": "How are you",
    "theek hai": "Okay",
    "alvida": "Goodbye",
    "fir milenge": "See you again",
    "pyar": "Love",
    "dosti": "Friendship",
    "khushi": "Happiness",
    "dukh": "Sadness",
    "ghar": "Home",
    "paani": "Water",
    "khana": "Food",
    "soona": "Sleep",
    "uthna": "Wake up",
    "baithna": "Sit",
    "chlna": "Walk",
    "bhaagna": "Run",
    "dekho": "Look",
    "sunno": "Listen",
    "bolo": "Speak",
    "likho": "Write",
    "padho": "Read",
    "samjho": "Understand",
    "karo": "Do",
    "mat karo": "Don't do",
    "kahan": "Where",
    "kab": "When",
    "kyun": "Why",
    "kaise": "How",
    "kaun": "Who",
    "kya": "What",
    "kitna": "How much",
    "mera naam": "My name is",
    "tumhara naam": "Your name is",
    "mujhe chahiye": "I need",
    "mujhe pasand hai": "I like",
    "mujhe nahi pasand": "I don't like",
    "accha lagta hai": "Feels good",
    "bura lagta hai": "Feels bad",
    "mazak": "Joke",
    "kahaani": "Story",
    "gaana": "Song",
    "photo": "Photo",
    "video": "Video",
    "mobile": "Mobile",
    "phone": "Phone",
    "computer": "Computer",
    "internet": "Internet",
    "password": "Password",
    "naam": "Name",
    "umra": "Age",
    "shaadi": "Marriage",
    "bachche": "Children",
    "maa": "Mother",
    "papa": "Father",
    "bhai": "Brother",
    "behen": "Sister",
    "dost": "Friend",
    "teacher": "Teacher",
    "student": "Student",
    "school": "School",
    "college": "College",
    "kamra": "Room",
    "darwaza": "Door",
    "khidki": "Window",
    "kursi": "Chair",
    "mez": "Table",
    "kitab": "Book",
    "kalam": "Pen",
    "mitti": "Soil",
    "paudha": "Plant",
    "phool": "Flower",
    "ped": "Tree",
    "nadi": "River",
    "pahaad": "Mountain",
    "samundar": "Sea",
    "aasmaan": "Sky",
    "suraj": "Sun",
    "chand": "Moon",
    "taare": "Stars",
    "barish": "Rain",
    "dhoop": "Sunlight",
    "hawa": "Wind",
    "aag": "Fire",
    "dharti": "Earth",
}

ENGLISH_TO_HINDI = {v: k for k, v in HINDI_TO_ENGLISH.items()}


def translate(text: str, direction: str = "auto") -> dict | None:
    text_lower = text.lower().strip()

    if direction == "auto" or direction == "hi_to_en":
        for hindi, english in HINDI_TO_ENGLISH.items():
            if hindi in text_lower:
                translated = text_lower.replace(hindi, english)
                return {
                    "original": text,
                    "translated": translated.title(),
                    "direction": "Hindi → English",
                }

    if direction == "auto" or direction == "en_to_hi":
        for english, hindi in ENGLISH_TO_HINDI.items():
            if english.lower() in text_lower:
                translated = text_lower.replace(english.lower(), hindi)
                return {
                    "original": text,
                    "translated": translated.title(),
                    "direction": "English → Hindi",
                }

    return None


def get_random_hindi_word() -> dict:
    hindi, english = random.choice(list(HINDI_TO_ENGLISH.items()))
    return {"hindi": hindi, "english": english}
