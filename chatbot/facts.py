import random


SCIENCE_FACTS = [
    "Light 8 minute 20 second mein Sun se Earth tak aati hai!",
    "Octopus ke 3 hearts hote hain aur blue blood hota hai!",
    "Bananas technically radioactive hote hain!",
    "Honey kabhi kharab nahi hota - 3000 saal purana bhi kha sakte ho!",
    "Human body mein enough carbon hai ki 9000 pencils ban saken!",
    "Ocean mein abhi tak sirf 5% explore hua hai!",
    "Sharks dinosaurs se pehle exist karte the!",
    "Ek average insaan apni life ka 6 saal sapne dekhne mein bitata hai!",
    "DNA mein agar sab instructions ko lamba karo toh Pluto tak pahunch jayega!",
    "Cows ke best friends hote hain aur unse door hone par stressed ho jaati hain!",
    "Water bhi hota hai aur thanda bhi - par extreme temperature pe!",
    "Moon pe apka weight Earth se 6 times kam hoga!",
    "Ek thunderstorm mein 100 million volts electricity hoti hai!",
    "Dolphins apne naam ka response dete hain jab bulao!",
    "Plastic bottle 450 saal tak decompose hoti hai!",
    "Human brain 20 watts ki power se kaam karta hai - bulb se bhi kam!",
    "Banana actually berry hai, strawberry nahi!",
    "Gold fish 3 seconds tak yaad nahi rakh sakte - myth hai, woh actually 5 months tak yaad rakh sakte hain!",
    "Lightning 5 times hotter hai Sun surface se!",
    "Human body mein 37.2 trillion cells hain!",
]

INDIA_FACTS = [
    "India mein 22 official languages hain!",
    "Kumbh Mela duniya ka sabse bada gathering hai - 75 million log aate hain!",
    "India mein duniya ka sabse purana restaurant hai - Mumbai's Leopold Cafe (1871)!",
    "Indian railway duniya ki 4th largest railway hai!",
    "Mumbai ka dabba walas system duniya ka sabse organized food delivery hai!",
    "India mein 1.3 billion log rehte hain - China ke baad sabse zyada!",
    "Hindi duniya ki 3rd sabse zyada bolne wali language hai!",
    "Indian space program ISRO duniya ki sabse sasti space launches karta hai!",
    "India mein 300,000+ mosques hain - duniya mein sabse zyada!",
    "Chai India mein sabse zyada peene wali beverage hai!",
    "Bollywood duniya ki sabse zyada films banane wali industry hai!",
    "Indian postal system duniya ka sabse bada hai - 155,000 post offices!",
    "India mein 90,000+ post offices hain!",
    "Indian Railways roz 23 million passengers carry karta hai!",
    "Varanasi duniya ka sabse purana continuously inhabited city hai!",
    "India mein 200+ airlines operate karte hain!",
    "Taj Mahal 22 saal mein bana tha aur 20,000 workers lage the!",
    "India mein duniya ka sabse lamba railway platform hai - Gorakhpur (1.3 km)!",
    "Himalayas har saal 1 cm upar badh rahe hain!",
    "India mein 1.5 lakh se zyada langars (community kitchens) roz chalte hain!",
]

HISTORY_FACTS = [
    "Great Wall of China 21,000 km lamba hai - visible from space nahi, par bahut lamba hai!",
    "Egyptians ne 4000 years pehle calendar banaya tha!",
    "Cleopatra Roman Empire se zyada ancient thi - Great Pyramids se bhi!",
    "Duniya ka pehla computer 2.5 tons ka tha aur poora room mein fit tha!",
    "Roman Empire mein flush toilets 2000 years pehle the!",
    "Internet ka pehla message 1969 mein 'LO' tha - login half mein crash ho gaya!",
    "Duniya mein pehla email 1971 mein bheja gaya tha!",
    "Napoleon short nahi tha - average height tha us time ke hisaab se!",
    "Eiffel Tower banane ke liye 2 million rivets lage the!",
    "World War 2 mein 70 million log mare gaye the!",
    "Pehli bar 1969 mein insaan moon pe gaya tha!",
    "Duniya mein pehla ATM 1967 mein London mein laga tha!",
    "Coca-Cola pehle green color ka tha!",
    "Google pehle 'BackRub' naam se jaana jaata tha!",
    "Apple ka pehla logo Isaac Newton ka drawing tha!",
]

TECH_FACTS = [
    "Pehla SMS 1992 mein bheja gaya tha - 'Merry Christmas'!",
    "WiFi ka full form 'Wireless Fidelity' nahi hai - koi official full form nahi hai!",
    "Average insaan apne phone ko 2,617 baar roz dekhta hai!",
    "Duniya mein 4.9 billion internet users hain!",
    "Amazon pehle sirf books bechta tha!",
    "Facebook ka original name 'TheFacebook' tha!",
    "USB ka inventor ajeeb hai - pehle galat side lagta hai, phir sahi!",
    "Smartphone mein 1960 ke supercomputer se zyada power hai!",
    "YouTube pe roz 500 hours ka video upload hota hai!",
    "Google pe roz 8.5 billion searches hote hain!",
    "First computer mouse wooden ka tha!",
    "iPhone ka pehla model 2007 mein aaya tha!",
    "Duniya ka pehla website info.cern.ch tha aur abhi bhi live hai!",
    "Bluetooth ka naam Viking king Harald Bluetooth se aaya hai!",
    "AI duniya ka sabse fast growing technology hai!",
]

ANIMAL_FACTS = [
    "Cows ke best friends hote hain aur unse door hone par stressed ho jaati hain!",
    "Penguins sirf Southern Hemisphere mein milte hain!",
    "Elephants duniya ka sabse bada land animal hai!",
    "Kangaroos peeche nahi chal sakte!",
    "Octopus ke 3 hearts hote hain!",
    "Dolphins apne naam ka response dete hain!",
    "Cheetah duniya ka sabse tez animal hai - 112 km/h!",
    "Penguins life mein sirf ek baar partner choose karte hain!",
    "Giraffe ka tongue 45 cm lamba hota hai!",
    "Koala ke fingerprints humans se almost identical hote hain!",
    "Butterflies apne pairo se sunte hain!",
    "Elephants 22 months tak pregnant rehti hain!",
    "Octopus duniya ka sabse intelligent invertebrate hai!",
    "Crows humans ke faces yaad rakh sakte hain!",
    "Snakes apni aankhein band nahi kar sakte!",
    "Dolphins humans ki tarah sapne dekhte hain!",
    "Elephants humans ki tarah rou sakte hain!",
    "Cats ke 230 bones hote hain - humans se 24 zyada!",
    "Parrots 100+ words seekh sakte hain!",
    "Horses apne so sakte hain khade khade!",
]


ALL_FACTS = {
    "science": SCIENCE_FACTS,
    "india": INDIA_FACTS,
    "history": HISTORY_FACTS,
    "tech": TECH_FACTS,
    "animals": ANIMAL_FACTS,
}


def get_random_fact(category: str | None = None) -> str:
    if category and category in ALL_FACTS:
        facts = ALL_FACTS[category]
    else:
        facts = []
        for cat_facts in ALL_FACTS.values():
            facts.extend(cat_facts)

    return random.choice(facts)


def get_fact_categories() -> list[str]:
    return list(ALL_FACTS.keys())
