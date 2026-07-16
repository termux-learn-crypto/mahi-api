import random


INSPIRATIONAL_QUOTES = [
    {"text": "Sapno ke peeche bhaago, results apne aap aayenge.", "author": "APJ Abdul Kalam"},
    {"text": "Koshish karne walon ki kabhi haar nahi hoti.", "author": "Harivansh Rai Bachchan"},
    {"text": "Safalta ek journey hai, destination nahi.", "author": "Unknown"},
    {"text": "Jo log kehte hain ki ye impossible hai, woh log use karne se pehle ruk jaate hain.", "author": "Unknown"},
    {"text": "Mehnat itni khamoshi se karo ki safalta shor machaye.", "author": "Unknown"},
    {"text": "Girte hain sheh sawariyon ke, mucchalon ke nishaane pe.", "author": "Allama Iqbal"},
    {"text": "Zindagi mein woh cheez mat chuno jo aasan ho, woh cheez chuno jo kabil ho.", "author": "Unknown"},
    {"text": "Sapne woh nahi jo sote waqt aaye, sapne woh hain jo sone na de.", "author": "APJ Abdul Kalam"},
    {"text": "Haar tab hoti hai jab hum haar maan lete hain.", "author": "Unknown"},
    {"text": "Kamyabi un logon milti hai jo apne kaam se pyar karte hain.", "author": "Unknown"},
    {"text": "Duniya mein sabse bada rog hai - logon ka sochna ki wo bechaare hain.", "author": "Unknown"},
    {"text": "Jab tak todo nahi, tab tak chhodo mat.", "author": "Unknown"},
    {"text": "Aaj ka kaam kal pe mat chhoddo.", "author": "Unknown"},
    {"text": "Jo apni kamzori ko apni takat bana le, usse koi nahi hara sakta.", "author": "Unknown"},
    {"text": "Soch badlo, duniya badal jayegi.", "author": "Unknown"},
]

LIFE_QUOTES = [
    {"text": "Life is what happens when you're busy making other plans.", "author": "John Lennon"},
    {"text": "In the end, it's not the years in your life that count, it's the life in your years.", "author": "Abraham Lincoln"},
    {"text": "Life is really simple, but we insist on making it complicated.", "author": "Confucius"},
    {"text": "Zindagi ek safar hai suhana, yahan kal kya ho kisne jaana.", "author": "Sahir Ludhianvi"},
    {"text": "Life is 10% what happens to you and 90% how you react to it.", "author": "Charles Swindoll"},
    {"text": "The purpose of our lives is to be happy.", "author": "Dalai Lama"},
    {"text": "Life is a dream for the wise, a game for the fool, a comedy for the rich, a tragedy for the poor.", "author": "Sholay Dialogue"},
    {"text": "Zindagi naa milagi dobara.", "author": "Movie"},
    {"text": "Life is too short to be serious all the time.", "author": "Unknown"},
    {"text": "Jo log apni zindagi se pyar karte hain, woh zindagi se pyar paate hain.", "author": "Unknown"},
]

FRIENDSHIP_QUOTES = [
    {"text": "Dost woh nahi jo saath baithe, dost woh hai jo saath khade ho.", "author": "Unknown"},
    {"text": "Asli dost woh hota hai jo mushkil mein saath de.", "author": "Unknown"},
    {"text": "Dosti mein koi rule nahi hota, bas ek hi rule hai - waada nibhana.", "author": "Unknown"},
    {"text": "Ek sachha dost hazaar rishtedaron ke barabar hota hai.", "author": "Unknown"},
    {"text": "Dost woh nahi jo tumhari har baat maane, dost woh hai jo sahi baat samjhaye.", "author": "Unknown"},
    {"text": "Zindagi mein dost kam honi chahiye par asli honi chahiye.", "author": "Unknown"},
    {"text": "Dosti ek aisa phool hai jo kabhi murjhaata nahi.", "author": "Unknown"},
    {"text": "True friendship is rare in this world. Be thankful for true friends.", "author": "Unknown"},
    {"text": "Dost apne liye nahi, apne dost ke liye jeeta hai.", "author": "Unknown"},
    {"text": "Duniya mein sabse pyaara rishta dosti ka hota hai.", "author": "Unknown"},
]

FUNNY_QUOTES = [
    {"text": "Mein itna rich hu ki mere pockets mein bhi pockets hain.", "author": "Unknown"},
    {"text": "Zindagi mein kuch karna ho toh excuses mat banao!", "author": "Unknown"},
    {"text": "Sabse bada rog hai - kya sochenge log.", "author": "Unknown"},
    {"text": "Naach na jaane, aangan tedha.", "author": "Proverb"},
    {"text": "Ghar ki murgi daal barabar.", "author": "Proverb"},
    {"text": "Bhagwan bharose baithoge toh kutta kaat lega.", "author": "Sardar Patel"},
    {"text": "Padosi ki gaadi zyada chamakti hai.", "author": "Unknown"},
    {"text": "Padhai likhai kiye bina, life mein kuch nahi milega - except WiFi.", "author": "Unknown"},
    {"text": "Suno sabki karo apni karo.", "author": "Proverb"},
    {"text": "Dil chhota mat karo, budget chhota karo.", "author": "Unknown"},
]

MOTIVATIONAL_QUOTES = [
    {"text": "Agar tumhen kuch naya karna hai, toh purane tarike chhodne padenge.", "author": "Unknown"},
    {"text": "Mehnat rang layegi, waqt lagega par result aayega.", "author": "Unknown"},
    {"text": "Jo cheez tumhen darrati hai, wohi cheez tumhe badlegi.", "author": "Unknown"},
    {"text": "Apne aap pe bharosa rakho, duniya jhuk jayegi.", "author": "Unknown"},
    {"text": "Subah ki walk 100 problems ka solution hai.", "author": "Unknown"},
    {"text": "Apna waqt aayega!", "author": "Movie"},
    {"text": "Raat guzar jaayegi, savera zaroor aayega.", "author": "Unknown"},
    {"text": "Tumhari himmat hi tumhari sabse badi taqat hai.", "author": "Unknown"},
    {"text": "Gir kar uthna hi zindagi hai.", "author": "Unknown"},
    {"text": "Ek din sab theek ho jayega, aaj ke liye bas himmat rakho.", "author": "Unknown"},
]


ALL_QUOTES = {
    "inspirational": INSPIRATIONAL_QUOTES,
    "life": LIFE_QUOTES,
    "friendship": FRIENDSHIP_QUOTES,
    "funny": FUNNY_QUOTES,
    "motivation": MOTIVATIONAL_QUOTES,
}


def get_random_quote(category: str | None = None) -> dict:
    if category and category in ALL_QUOTES:
        quotes = ALL_QUOTES[category]
    else:
        quotes = []
        for cat_quotes in ALL_QUOTES.values():
            quotes.extend(cat_quotes)

    return random.choice(quotes)


def get_quote_categories() -> list[str]:
    return list(ALL_QUOTES.keys())
