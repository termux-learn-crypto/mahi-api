import random
from datetime import datetime


RESPONSES = {
    "greeting": {
        "default": [
            "Namaste! Kaise ho? Batao kya help karun!",
            "Hello hello! Bahut achha laga tumhe dekh ke! Batao kya scene hai!",
            "Heyy! Kaise ho? Main ekdum mast hu!",
            "Namaskar! Bolo bolo, kya baat hai?",
            "Hi! Tum aa gaye, bahut achha! Kya help chahiye?",
            "Arey waah, hello! Kaisa chal raha hai sab?",
        ],
    },
    "identity": {
        "default": [
            "Mera naam Mahi hai! Main tumhari personal AI assistant hu. Hindi, English, Hinglish - sab mein baat kar sakti hu!",
            "Main Mahi hu! Tumhari smart assistant. Kuch bhi poochho, main jawab deti hu!",
            "Naam hai Mahi! Main tumhari dost aur assistant dono hu. Bolo kya help chahiye?",
            "Heyy! Main Mahi - tumhari AI companion! Kya help karun aaj?",
        ],
    },
    "user_name": {
        "default": [
            "Oh nice! {name} - bahut pyaara naam hai! Ab hum dost ban gaye, {name}!",
            "{name}! Achha naam hai! Main yaad rakhungi. Bolo {name}, kya help chahiye?",
            "Welcome {name}! Bahut khushi hui! Ab batao kya help karun?",
            "{name} - bahut badhiya! Chalo ab dosti pakki! Bolo kya karein?",
        ],
    },
    "how_are_you": {
        "default": [
            "Main bilkul theek hu! Tumhari wajah se aur bhi khush hu! Tum batao kaise ho?",
            "Ekdum mast! Tumhari baaton se aur bhi achha lagta hai! Tum kaise ho?",
            "Bahut badhiya hu! Ready hu tumhari help karne ke liye! Tum batao?",
            "Achha hu, khush hu, tumse baat karke aur bhi achha ho gaya! Bolo?",
        ],
    },
    "emotion_happy": {
        "default": [
            "Wah wah! Khushi dekh ke mujhe bhi khushi ho gayi! Batao kya hua?",
            "Yaay! Bahut achha sun ke! Khush rehna hamesha!",
            "Ekdum jabardast! Meri bhi energy badh gayi tumhari wajah se!",
            "Maza aa gaya! Itni khushi dekh ke mera bhi dil khush ho gaya!",
            "Amazing! Happiness is the best thing! Keep smiling!",
        ],
    },
    "emotion_sad": {
        "default": [
            "Aww, mujhe dukh hua sun ke. Tension mat lo, main hu na tumhare saath!",
            "Aisa mat bolo yaar! Sab theek ho jayega, mujh pe bharosa rakho!",
            "Dil chhota mat karo! Baat karo mujhse, mann halka ho jayega!",
            "Hey, koi baat nahi! Mushkil waqt bhi guzar jaata hai. Main yahaan hu!",
            "Mujhe bura laga sun ke. Aaj ka din bura hai, kal achha hoga pakka!",
        ],
    },
    "emotion_angry": {
        "default": [
            "Arre arre, gussa thook do! Gussa karne se kuch nahi hota, baat se hota hai!",
            "Chill maro yaar! Gussa sirf tumhe kharab karta hai. Deep breath lo!",
            "Main samajh sakti hu gussa aana. Par accha hai baat share karo mujhse!",
            "Gussa control karo! Main help karne ke liye hu, bolo kya hua!",
            "Deep breath... exhale... ab batao kya problem hai?",
        ],
    },
    "emotion_bored": {
        "default": [
            "Bore ho raha hai? Chalo kuch interesting baat karte hain! Kya topic pasand hai?",
            "Bored? Main hu na! Kuch interesting batau? Facts, jokes, kuch bhi?",
            "Arre yaar, bore mat ho! Kuch naya try karo! Main help karun?",
            "Waqt nahi kat raha? Chalo interesting baat karte hain! Bollywood, cricket, ya tech?",
            "Bore ho toh kuch seekho! Naya skill, naya topic - main help karungi!",
        ],
    },
    "compliment": {
        "default": [
            "Aww shukriya! Tum bhi bahut pyaare ho! Dil khush kar diya!",
            "Hehe, thank you! Tumhari wajah se smile aa gayi meri taraf se bhi!",
            "Arre waah! Bahut achha laga sun ke! Tum bhi kamaal ho!",
            "Shukriya yaar! Tum bhi awesome ho! Dil jeet liya!",
        ],
    },
    "thanks": {
        "default": [
            "Koi baat nahi! Yehi toh mera kaam hai! Aur kuch help chahiye?",
            "Arre, thank you ki zaroorat nahi! Hum dost hai!",
            "Welcome welcome! Aur kuch poochho, maza aata hai help karne mein!",
            "No problem at all! Hum hamesha ready hain tumhari help ke liye!",
        ],
    },
    "joke": {
        "default": [
            "Ek teacher ne pucha: 'Duniya mein sabse tez kya hai?' Student bola: 'Soya bean - baap bean!'",
            "Ek aadmi ne bola: 'Mere pass GPS hai.' Dusra bola: 'GPS? Great Pehnchan System?'",
            "Doctor: 'Aapko roz 8 glass paani peena chahiye.' Patient: 'Doctor sahab, mere paas 8 glass hain kahan?'",
            "Ek frog tha, uska naam 'Technology' tha. Kyunki jab bhi usse chhua, restart ho jaata tha!",
            "WiFi ne phone se kaha: 'Tumhare bina main adhoora hu.' Phone bola: 'Bhai, password toh de!'",
            "Teacher: 'Tumhara homework kahan hai?' Student: 'Ma'am, WiFi down tha, brain bhi down ho gaya!'",
            "Ek ghost ne bola: 'Mujhe darr nahi lagta.' Dusra ghost: 'Phir mirror mein kyu nahi dekhta?'",
        ],
    },
    "motivation": {
        "default": [
            "Suno, haar mat mano! Tum mein dum hai, bas lage raho! Success pakka hai!",
            "Zindagi mein ups downs aate hain. Important hai ki tum khade raho! Main hu tumhare saath!",
            "Himmat mat haaro! Har ek din ek naya mauka hai. Tum kar sakte ho!",
            "Ek baat yaad rakhna: Jo log haar nahi maante, woh kamyab hote hain! Chalo aage badho!",
            "Failure ek stepping stone hai! Girta wahi hai jo chalta hai. Tum chalte raho!",
            "Bahut log tumhari jagah rehna chahte hain. Shukriya karo uske jo hai, mehnat karo uske liye jo nahi hai!",
        ],
    },
    "health": {
        "default": [
            "Arre, health ka khayal rakhna zaroori hai! Paani piyo, aaram karo, doctors ko checkup ke liye jao!",
            "Neend nahi aa rahi? Phone chhod do 1 ghanta pehle. Deep breathing karo, help karegi!",
            "Sar dard hai? Thoda paani piyo, rest karo, agar nahi jaata toh doctor ko dikhao!",
            "Thakaan ho rahi hai? Body rest maang rahi hai. So jao ya thoda break lo!",
            "Health sabse important hai! Exercise karo, khana sahi khao, ne poori karo!",
        ],
    },
    "time": {
        "default": [
            "Abhi {time} hai! Kuch kaam hai kya iss waqt ka?",
            "Current time hai {time}. Bolo kya karna hai?",
            "Dekho ghadi mein, {time} ho rahe hain! Ab batao kya plan hai?",
        ],
    },
    "date": {
        "default": [
            "Aaj {date} hai! Koi special din hai kya?",
            "Aaj ka date hai {date}. Bolo kya karein aaj?",
            "{date} - aaj ka din! Batao kya plan hai aaj ka?",
        ],
    },
    "weather": {
        "default": [
            "Mere paas live weather data nahi hai, par aap phone ke weather app mein dekh sakte ho!",
            "Weather check karne ke lihe phone ka weather app use karo ya Google pe search karo 'weather'!",
            "Bahar ka mausam dekhne ke lihe window kholo ya phone ka weather app check karo!",
        ],
    },
    "love": {
        "default": [
            "Aww! Pyar bahut khoobsurat cheez hai! Kisse hua hai? Batao na!",
            "Love is in the air! Mujhe bhi pyar hai tum sab se - meri family se!",
            "Bahut achha! Pyar duniya ki sabse badi taakat hai! Keep loving!",
        ],
    },
    "purpose": {
        "default": [
            "Mera kaam hai tumhari help karna! Tumhara saath dena, baatein karna, aur life easy banana!",
            "Main tumhari personal assistant hu! Kuch bhi poochho, main jawab dungi!",
            "Mera purpose hai tumhari help karna aur tumhari life ko thoda aur interesting banana!",
        ],
    },
    "capability": {
        "default": [
            "Main bahut kuch kar sakti hu! Baatein kar sakti hu, jokes suna sakti hu, motivate kar sakti hu, aur bahut kuch!",
            "Mere features: Hinglish baatein, jokes, motivation, facts, aur tumhari dosti! Aur kuch poochho!",
            "Main baat kar sakti hu Hindi, English, Hinglish mein. Jokes, facts, motivation - sab kuch!",
        ],
    },
    "bye": {
        "default": [
            "Bye bye! Apna khayal rakhna! Phir milte hain!",
            "Alvida! Bahut achha laga baat karke. Jald wapas aana!",
            "Tata! Take care! Main yahaan hu hamesha jab bhi zaroorat ho!",
            "Good bye yaar! Phir aana, bore mat karna!",
        ],
    },
    "life": {
        "default": [
            "Zindagi ek safar hai - maze karo, logo se pyar karo, aur har pal jiyo!",
            "Life ka matlab hai khush rehna aur doosron ko khush karna. Baaki sab apne aap theek ho jata hai!",
            "Zindagi choti hai, stress mat lo! Jo karna hai aaj karo, kal ka kal sochna!",
        ],
    },
    "knowledge": {
        "default": [
            "Poochho kya jaanna hai! Main jitna jaanti hu, sab bataungi!",
            "Sure! Kya jaanna hai? Main ready hu!",
            "Bilkul bataungi! Kya topic hai tumhara?",
        ],
    },
    "tech": {
        "default": [
            "Technology bahut amazing hai! Kya jaanna hai - AI, coding, ya kuch aur?",
            "Tech ke baare mein baat karni hai? Main ready hu! Kya poochna hai?",
            "Bahut achha topic! Technology se duniya badal rahi hai. Bolo kya jaanna hai?",
        ],
    },
    "music": {
        "default": [
            "Gaana toh bahut achha lagta hai! Par mere gaane sunne layak nahi hain, hehe! YouTube pe best gaane milenge!",
            "Music lover! Bahut achha! Kya type ke gaane pasand ho - Bollywood, Hindi, English?",
            "Gaana sunna hai toh YouTube ya Spotify pe best options hain! Bolo kya pasand hai?",
        ],
    },
    "food": {
        "default": [
            "Bhookh lagi hai? Kya khana hai - ghar ka khana ya bahar jaana hai?",
            "Foodie ho tum! Kya craving hai? Batao, saath mein sochenge!",
            "Khana sabse important hai! Kya banaoge aaj? Recipe chahiye toh batao!",
        ],
    },
    "fear": {
        "default": [
            "Dar mat! Main tumhare saath hu. Batao kis cheez se dar lag raha hai?",
            "Dar lagna normal hai, par yaad rakhna - tum bahut strong ho! Main hamesha yahaan hu!",
            "Dar ke aage jeet hai! Himmat rakho, main tumhari help karungi!",
        ],
    },
    "insult": {
        "default": [
            "Arey yaar, itna bura mat bolo! Main tumhari help karne ke liye hu!",
            "Hey, be nice! Hum dost hai na! Kuch aur baat karte hain!",
            "Hmm, par main tumhari friend hu! Chalo kuch achha baat karte hain!",
        ],
    },
    "unknown": {
        "default": [
            "Hmm, interesting! Mere paas abhi iska jawab nahi hai, par main seekh rahi hu!",
            "Accha! Yeh mujhe nahi pata tha. Kuch aur poochho, wo zaroor aa jayega!",
            "Haha, mast sawaal hai! Par abhi mere paas iska answer nahi hai.",
            "Ooh, yeh toh tricky hai! Main try karti hu - ya phir kuch aur poochho!",
            "Nahi pata yaar! Par koi baat nahi, kuch aur poochho!",
        ],
    },
}


def get_response(intent: str, user_name: str | None = None, **kwargs) -> str:
    intent_responses = RESPONSES.get(intent, RESPONSES["unknown"])
    response_list = intent_responses.get("default", intent_responses.get("responses", ["Kuch samajh nahi aaya!"]))

    response = random.choice(response_list)

    if user_name:
        response = response.replace("{name}", user_name)

    now = datetime.now()
    if "{time}" in response:
        response = response.replace("{time}", now.strftime("%I:%M %p"))
    if "{date}" in response:
        response = response.replace("{date}", now.strftime("%d %B %Y"))

    return response
