import re


class MultiLanguageEngine:
    def __init__(self):
        self.supported_languages = {
            "hi": {"name": "Hindi", "native": "हिन्दी", "greeting": "Namaste"},
            "ta": {"name": "Tamil", "native": "தமிழ்", "greeting": "Vanakkam"},
            "te": {"name": "Telugu", "native": "తెలుగు", "greeting": "Namaskaram"},
            "bn": {"name": "Bengali", "native": "বাংলা", "greeting": "Namaskar"},
            "mr": {"name": "Marathi", "native": "मराठी", "greeting": "Namaskar"},
            "gu": {"name": "Gujarati", "native": "ગુજરાતી", "greeting": "Namaste"},
            "kn": {"name": "Kannada", "native": "ಕನ್ನಡ", "greeting": "Namaskara"},
            "ml": {"name": "Malayalam", "native": "മലയാളം", "greeting": "Namaskaram"},
            "pa": {"name": "Punjabi", "native": "ਪੰਜਾਬੀ", "greeting": "Sat Sri Akal"},
            "ur": {"name": "Urdu", "native": "اردو", "greeting": "Adaab"},
        }

        self.common_words = {
            "hi": {
                "hello": "namaste", "thanks": "shukriya", "yes": "haan",
                "no": "nahi", "good": "achha", "bad": "bura",
                "friend": "dost", "how": "kaise", "what": "kya",
                "where": "kahan", "when": "kab", "why": "kyun",
                "please": "kripya", "sorry": "maaf", "love": "pyaar",
                "water": "paani", "food": "khana", "home": "ghar",
                "school": "school", "work": "kaam", "time": "waqt",
            },
            "ta": {
                "hello": "vanakkam", "thanks": "nandri", "yes": "aama",
                "no": "illai", "good": "nallathu", "bad": "mosam",
                "friend": "nanban", "how": "eppadi", "what": "enna",
                "where": "engal", "when": "eppothu", "why": "yennu",
                "please": "thayavu", "sorry": "mannikavum", "love": "anbu",
                "water": "neer", "food": "saapadu", "home": "veedu",
            },
            "te": {
                "hello": "namaskaram", "thanks": "dhanyavaadalu", "yes": "avunu",
                "no": "kadhu", "good": "manchidi", "bad": "chandam",
                "friend": "mitrudi", "how": "ela", "what": "enti",
                "where": "ekkada", "when": "eppudu", "why": "enduku",
                "please": "dayachesi", "sorry": "kshaminchandi", "love": "prema",
                "water": "neellu", "food": "tinadam", "home": "inti",
            },
            "bn": {
                "hello": "namaskar", "thanks": "dhonnobad", "yes": "haan",
                "no": "naa", "good": "bhalo", "bad": "kharap",
                "friend": "bondhu", "how": "kemon", "what": "ki",
                "where": "kothay", "when": "kothai", "why": "kano",
                "please": "doya kore", "sorry": "khoma", "love": "bhalobasha",
                "water": "jol", "food": "khabar", "home": "bari",
            },
            "mr": {
                "hello": "namaskar", "thanks": "dhanyavaad", "yes": "ho",
                "no": "nahi", "good": "chhan", "bad": "vait",
                "friend": "mitra", "how": "kas", "what": "kaay",
                "where": "kuth", "when": "keti", "why": "kyaa",
                "please": "krupaya", "sorry": "maaph", "love": "prem",
                "water": "paani", "food": "khana", "home": "ghar",
            },
        }

        self.greetings = {
            "hi": ["namaste", "namaskar", "kaise ho", "kya haal", "aur batao"],
            "ta": ["vanakkam", "epdi irukkinga", "lam kana"],
            "te": ["namaskaram", "ela unaru", "bagunnara"],
            "bn": ["namaskar", "kemon achen", "ki khobor"],
            "mr": ["namaskar", "kase ahat", "kaay zhala"],
        }

        self.farewells = {
            "hi": ["alvida", "phir milenge", "bye bye", "take care"],
            "ta": ["poitu varum", "bye", "take care"],
            "te": ["veltunna", "bye", "take care"],
            "bn": ["aaste", "bye", "take care"],
            "mr": ["bye", "take care", "puna bhetu"],
        }

    def detect_language(self, text: str) -> str:
        text_lower = text.lower()

        for lang_code, words in self.common_words.items():
            matches = sum(1 for word in words.values() if word in text_lower)
            if matches >= 2:
                return lang_code

        if re.search(r'[\u0900-\u097F]', text):
            return "hi"
        if re.search(r'[\u0B80-\u0BFF]', text):
            return "ta"
        if re.search(r'[\u0C00-\u0C7F]', text):
            return "te"
        if re.search(r'[\u0980-\u09FF]', text):
            return "bn"
        if re.search(r'[\u0900-\u097F]', text):
            return "mr"
        if re.search(r'[\u0A80-\u0AFF]', text):
            return "gu"
        if re.search(r'[\u0C80-\u0CFF]', text):
            return "kn"
        if re.search(r'[\u0D00-\u0D7F]', text):
            return "ml"
        if re.search(r'[\u0A00-\u0A7F]', text):
            return "pa"
        if re.search(r'[\u0600-\u06FF]', text):
            return "ur"

        return "en"

    def get_greeting(self, lang_code: str) -> str:
        greetings = self.greetings.get(lang_code, ["hello"])
        return greetings[0].capitalize()

    def get_farewell(self, lang_code: str) -> str:
        farewells = self.farewells.get(lang_code, ["bye"])
        return farewells[0].capitalize()

    def get_common_words(self, lang_code: str) -> dict:
        return self.common_words.get(lang_code, {})

    def get_language_info(self, lang_code: str) -> dict:
        return self.supported_languages.get(lang_code, {
            "name": "Unknown",
            "native": lang_code,
            "greeting": "Hello",
        })

    def get_all_languages(self) -> list[dict]:
        return [
            {"code": code, **info}
            for code, info in self.supported_languages.items()
        ]

    def translate_word(self, word: str, from_lang: str, to_lang: str) -> str:
        if from_lang == "en" and to_lang in self.common_words:
            reverse_map = {v: k for k, v in self.common_words[to_lang].items()}
            return reverse_map.get(word.lower(), word)

        if to_lang == "en" and from_lang in self.common_words:
            return self.common_words[from_lang].get(word.lower(), word)

        if from_lang in self.common_words and to_lang in self.common_words:
            english_word = self.common_words[from_lang].get(word.lower())
            if english_word:
                return self.common_words[to_lang].get(english_word, word)

        return word

    def get_localized_response(self, responses: dict, lang_code: str) -> str:
        return responses.get(lang_code, responses.get("en", "I don't understand."))


multi_lang = MultiLanguageEngine()
