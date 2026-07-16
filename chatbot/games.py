import random


WOULD_YOU_RATHER = [
    {"option_a": "Time travel karna past mein", "option_b": "Future dekhna"},
    {"option_a": "Invisible hona", "option_b": "Flying karna"},
    {"option_a": "Duniya ki sabse tez train mein baithna", "option_b": "Sabse lambi flight mein"},
    {"option_a": "Ek saal jungle mein rehna", "option_b": "Ek saal internet ke bina"},
    {"option_a": "1 crore jeetna", "option_b": "10 saal extra jeena"},
    {"option_a": "Hamesha sach bolna", "option_b": "Hamesha jhooth bolna"},
    {"option_a": "Super intelligence hona", "option_b": "Super strength hona"},
    {"option_a": "Duniya ghoonna", "option_b": "Ghar pe baith ke book padhna"},
    {"option_a": "Raat ko uth ke padhna", "option_b": "Subah 5 baje uth ke exercise karna"},
    {"option_a": "Apni pasandida dish roz khana", "option_b": "Roz naya khaana try karna"},
    {"option_a": "Dost ke saath road trip", "option_b": "Akele mountains pe jaana"},
    {"option_a": "Sab ke thoughts padhna", "option_b": "Invisible hona"},
    {"option_a": "Ek din ke liye Shah Rukh Khan banana", "option_b": "Ek din ke liye Virat Kohli banana"},
    {"option_a": "Duniya ka sabse spicy khaana khana", "option_b": "Duniya ka sabse mehenga khaana khana"},
    {"option_a": "Hamesha phone charge 100% rehta", "option_b": "Hamesha WiFi free milta"},
    {"option_a": "Ek saal sirf dal-chawal khana", "option_b": "Ek saal sirf pizza khana"},
    {"option_a": "Apne baare mein future dekhna", "option_b": "Apne doston ke baare mein future dekhna"},
    {"option_a": "Duniya ka sabse bada ghar", "option_b": "Duniya ka sabse chhota ghar lekin beach pe"},
]

TWO_TRUTHS_ONE_LIE = [
    {
        "statement_a": "Elephants sirf ek cheez sun sakti hain ek saath mein",
        "statement_b": "Cows best friends ke liye ro sakti hain",
        "statement_c": "Dolphins humans ki tarah sapne dekhte hain",
        "lie": "c",
        "explanation": "Dolphins actually khade hokar so jaate hain, sapne nahi dekhte! Baaki dono sach hain."
    },
    {
        "statement_a": "Octopus ke 3 hearts hote hain",
        "statement_b": "Honey 3000 saal tak kharab nahi hota",
        "statement_c": "Goldfish ka memory 3 second ka hota hai",
        "lie": "c",
        "explanation": "Goldfish actually 5 months tak yaad rakh sakte hain! Ye ek famous myth hai."
    },
    {
        "statement_a": "Penguins life mein sirf ek baar partner choose karte hain",
        "statement_b": "Cheetah duniya ka sabse tez animal hai",
        "statement_c": "Bananas technically berries hain",
        "lie": "b",
        "explanation": "Peregrine falcon duniya ka sabse tez animal hai - 390 km/h dive mein!"
    },
    {
        "statement_a": "Humans ke pass 206 bones hain",
        "statement_b": "Octopus ke blue blood hota hai",
        "statement_c": "Human body mein 37 liters khoon hota hai",
        "lie": "c",
        "explanation": "Human body mein 5-6 liters khoon hota hai, 37 nahi!"
    },
    {
        "statement_a": "Sharks dinosaurs se pehle exist karte the",
        "statement_b": "Koala ke fingerprints humans se identical hote hain",
        "statement_c": "Cats ke 300 bones hote hain",
        "lie": "c",
        "explanation": "Cats ke 230 bones hote hain, 300 nahi!"
    },
    {
        "statement_a": "Lightning 5 times hotter hai Sun surface se",
        "statement_b": "Horses khade hokar so sakte hain",
        "statement_c": "Giraffe ka tongue 60 cm lamba hota hai",
        "lie": "c",
        "explanation": "Giraffe ka tongue 45 cm lamba hota hai, 60 nahi!"
    },
    {
        "statement_a": "India mein 22 official languages hain",
        "statement_b": "Kumbh Mela duniya ka sabse bada gathering hai",
        "statement_c": "Indian Railway roz 50 million passengers carry karta hai",
        "lie": "c",
        "explanation": "Indian Railway roz 23 million passengers carry karta hai, 50 million nahi!"
    },
    {
        "statement_a": "Apple ka pehla logo Isaac Newton ka drawing tha",
        "statement_b": "Google pehle 'BackRub' naam se jaana jaata tha",
        "statement_c": "Facebook ka original name 'TheFacebook' tha",
        "lie": "a",
        "explanation": "Apple ka pehla logo Newton nahi tha - wo Newton ke apple se related hai, par drawing nahi!"
    },
    {
        "statement_a": "WiFi ka full form 'Wireless Fidelity' hai",
        "statement_b": "Pehla SMS 1992 mein 'Merry Christmas' tha",
        "statement_c": "Internet ka pehla message 'LO' tha",
        "lie": "a",
        "explanation": "WiFi ka koi official full form nahi hai! Ye ek myth hai."
    },
    {
        "statement_a": "Butterflies apne pairo se sunte hain",
        "statement_b": "Snakes apni aankhein band nahi kar sakte",
        "statement_c": "Parrots 500+ words seekh sakte hain",
        "lie": "c",
        "explanation": "Parrots 100+ words seekh sakte hain, 500 nahi!"
    },
]

TONGUE_TWISTERS_HINDI = [
    "Kaccha papad pakka papad, kacche papde ke pakke papad",
    "Chhat pe chadh ke chhat pe chadhi chhat",
    "Tota pota mein baitha, tota ne pota ko toda",
    "Pahadi pe pahadi, pahadi ke niche pahadi",
    "Kala kauwa kala kauwa, kitne kale kauwe kale",
    "Lal mirch lali mirch, lali mirch ki lali lal",
    "Nani teri morni ko mor le gaye",
    "Kitne kilo kitne kilo kitne kilo tere kandhe pe",
    "Dhruv ke papa ka naam hai dhruv",
]

TONGUE_TWISTERS_ENGLISH = [
    "She sells seashells by the seashore",
    "Peter Piper picked a peck of pickled peppers",
    "How much wood would a woodchuck chuck",
    "Red lorry, yellow lorry, red lorry, yellow lorry",
    "Unique New York, you know you need unique New York",
    "Toy boat, toy boat, toy boat",
    "Rubber baby buggy bumpers",
    "Six slippery snails slid slowly seaward",
    "Three free throws, three free throws, three free throws",
]


def get_would_you_rather() -> dict:
    return random.choice(WOULD_YOU_RATHER)


def get_two_truths_lie() -> dict:
    return random.choice(TWO_TRUTHS_ONE_LIE)


def get_tongue_twister(language: str = "hindi") -> str:
    if language == "english":
        return random.choice(TONGUE_TWISTERS_ENGLISH)
    return random.choice(TONGUE_TWISTERS_HINDI)
