import re
import json


def detect_mobile_command(message: str) -> dict | None:
    msg = message.lower().strip()

    if any(w in msg for w in ["youtube", "youtube pe", "video dikhao", "video chalao"]):
        search = re.sub(r'(youtube|pe|dikhao|chalao|search|karo|open|kholo)', '', msg).strip()
        if search:
            return {
                "command": "youtube_search",
                "action": "open",
                "package": "com.google.android.youtube",
                "data": {"query": search},
                "response": f"YouTube pe \"{search}\" dhundh raha hoon! 📺"
            }
        return {
            "command": "youtube_open",
            "action": "open",
            "package": "com.google.android.youtube",
            "response": "YouTube khol raha hoon! 📺"
        }

    if any(w in msg for w in ["whatsapp", "message bhejo", "message karo", "whatsapp pe"]):
        contact = None
        text = None
        contact_match = re.search(r'(?:whatsapp pe\s+)?(\w+)\s+(?:ko|se|to)\s+(?:message|bhejo|bol|sms)', msg)
        if contact_match:
            contact = contact_match.group(1).strip()
            text_match = re.search(r'(?:message|bol|bhejo|sms)\s+(?:bhejo\s+)?(?:ki\s+)?(?:message\s+)?(.+)', msg)
            if text_match:
                text = text_match.group(1).strip()

        if contact and text:
            return {
                "command": "whatsapp_message",
                "action": "send",
                "package": "com.whatsapp",
                "data": {"contact": contact, "message": text},
                "response": f"{contact} ko WhatsApp pe bhej raha hoon: \"{text}\" 💬"
            }
        elif contact:
            return {
                "command": "whatsapp_open_chat",
                "action": "open",
                "package": "com.whatsapp",
                "data": {"contact": contact},
                "response": f"{contact} ka WhatsApp khol raha hoon! 💬"
            }
        return {
            "command": "whatsapp_open",
            "action": "open",
            "package": "com.whatsapp",
            "response": "WhatsApp khol raha hoon! 💬"
        }

    if any(w in msg for w in ["call", "phone", "phone karo", "call karo"]):
        contact = None
        contact_match = re.search(r'(.+?)\s+(?:ko|se|to)\s+(?:call|phone)', msg)
        if contact_match:
            contact = contact_match.group(1).strip()

        if contact:
            return {
                "command": "phone_call",
                "action": "call",
                "package": "com.android.dialer",
                "data": {"contact": contact},
                "response": f"{contact} ko call laga raha hoon! 📞"
            }
        return {
            "command": "phone_open",
            "action": "open",
            "package": "com.android.dialer",
            "response": "Phone dialer khol raha hoon! 📞"
        }

    if any(w in msg for w in ["sms", "sms bhejo", "text karo"]):
        contact = None
        text = None
        contact_match = re.search(r'(\w+)\s+(?:ko|se|to)\s+(?:sms|message|bhejo)', msg)
        if contact_match:
            contact = contact_match.group(1).strip()
            text_match = re.search(r'(?:sms|message|bhejo)\s+bhejo\s+(.+)', msg)
            if not text_match:
                text_match = re.search(r'(?:sms|message|bhejo)\s+(.+)', msg)
            if text_match:
                text = text_match.group(1).strip()
                text = re.sub(r'^(bhejo|message|sms)\s+', '', text).strip()

        if contact and text:
            return {
                "command": "sms_send",
                "action": "send",
                "package": "com.android.mms",
                "data": {"contact": contact, "message": text},
                "response": f"{contact} ko SMS bhej raha hoon: \"{text}\" 📩"
            }
        return {
            "command": "sms_open",
            "action": "open",
            "package": "com.android.mms",
            "response": "SMS app khol raha hoon! 📩"
        }

    if any(w in msg for w in ["alarm", "alarm lagao", "reminder", "yaad dila"]):
        time_match = re.search(r'(\d{1,2}[:\s]?\d{0,2})\s*(baje|am|pm|bajey|o.clock)?', msg)
        time_str = time_match.group(1) if time_match else None

        if time_str:
            return {
                "command": "alarm_set",
                "action": "set",
                "package": "com.google.android.deskclock",
                "data": {"time": time_str},
                "response": f"{time_str} baje ka alarm laga raha hoon! ⏰"
            }
        return {
            "command": "alarm_open",
            "action": "open",
            "package": "com.google.android.deskclock",
            "response": "Alarm app khol raha hoon! ⏰"
        }

    if any(w in msg for w in ["open", "kholo", "khol", "chalaao", "chalao"]):
        apps = {
            "chrome": "com.android.chrome",
            "camera": "com.android.camera",
            "gallery": "com.google.android.apps.photos",
            "photos": "com.google.android.apps.photos",
            "maps": "com.google.android.apps.maps",
            "play store": "com.android.vending",
            "playstore": "com.android.vending",
            "settings": "com.android.settings",
            "calculator": "com.google.android.calculator",
            "calendar": "com.google.android.calendar",
            "clock": "com.google.android.deskclock",
            "contacts": "com.google.android.contacts",
            "files": "com.google.android.apps.nbu.files",
            "file manager": "com.google.android.apps.nbu.files",
            "music": "com.google.android.apps.music",
            "spotify": "com.spotify.music",
            "gaana": "com.gaana",
            "wynk": "com.wynk.music",
            "jiosaavn": "com.jio.media.jiogaana",
            "instagram": "com.instagram.android",
            "facebook": "com.facebook.katana",
            "twitter": "com.twitter.android",
            "telegram": "org.telegram.messenger",
            "snapchat": "com.snapchat.android",
            "linkedin": "com.linkedin.android",
            "netflix": "com.netflix.mediaclient",
            "prime video": "com.amazon.avod",
            "hotstar": "in.hotstar",
            "zomato": "com.zomato",
            "swiggy": "com.swiggy.android",
            "paytm": "net.one97.paytm",
            "gpay": "com.google.android.apps.nbu.paisa.user",
            "phonepe": "com.phonepe.app",
        }

        for app_name, package in apps.items():
            if app_name in msg:
                return {
                    "command": "app_open",
                    "action": "open",
                    "package": package,
                    "response": f"{app_name.title()} khol raha hoon! 📱"
                }

        return {
            "command": "app_list",
            "action": "list",
            "response": "Konsa app kholna hai? Batao naam! 📱"
        }

    if any(w in msg for w in ["brightness", "brightness badhao", "brightness kam karo", "screen"]):
        if "badhao" in msg or "zyada" in msg or "up" in msg:
            return {
                "command": "brightness_up",
                "action": "set",
                "data": {"level": "high"},
                "response": "Brightness badha raha hoon! 🔆"
            }
        elif "kam" in msg or "down" in msg:
            return {
                "command": "brightness_down",
                "action": "set",
                "data": {"level": "low"},
                "response": "Brightness kam kar raha hoon! 🔅"
            }
        return {
            "command": "brightness_settings",
            "action": "open",
            "package": "com.android.settings",
            "response": "Brightness settings khol raha hoon! 🔆"
        }

    if any(w in msg for w in ["wifi", "wifi on", "wifi off", "internet"]):
        if "on" in msg or "chalu" in msg or "kholo" in msg:
            return {
                "command": "wifi_on",
                "action": "set",
                "data": {"state": "on"},
                "response": "WiFi ON kar raha hoon! 📶"
            }
        elif "off" in msg or "band" in msg:
            return {
                "command": "wifi_off",
                "action": "set",
                "data": {"state": "off"},
                "response": "WiFi OFF kar raha hoon! 📶"
            }
        return {
            "command": "wifi_settings",
            "action": "open",
            "package": "com.android.settings",
            "response": "WiFi settings khol raha hoon! 📶"
        }

    if any(w in msg for w in ["bluetooth", "bluetooth on", "bluetooth off"]):
        if "on" in msg or "chalu" in msg:
            return {
                "command": "bluetooth_on",
                "action": "set",
                "data": {"state": "on"},
                "response": "Bluetooth ON kar raha hoon! 🔵"
            }
        elif "off" in msg or "band" in msg:
            return {
                "command": "bluetooth_off",
                "action": "set",
                "data": {"state": "off"},
                "response": "Bluetooth OFF kar raha hoon! 🔵"
            }
        return {
            "command": "bluetooth_settings",
            "action": "open",
            "package": "com.android.settings",
            "response": "Bluetooth settings khol raha hoon! 🔵"
        }

    if any(w in msg for w in ["volume", "volume badhao", "volume kam karo", "aawaz"]):
        if "badhao" in msg or "zyada" in msg:
            return {
                "command": "volume_up",
                "action": "set",
                "data": {"level": "up"},
                "response": "Volume badha raha hoon! 🔊"
            }
        elif "kam" in msg:
            return {
                "command": "volume_down",
                "action": "set",
                "data": {"level": "down"},
                "response": "Volume kam kar raha hoon! 🔉"
            }
        elif "mute" in msg or "silence" in msg or "chup" in msg:
            return {
                "command": "volume_mute",
                "action": "set",
                "data": {"level": "mute"},
                "response": "Volume mute kar diya! 🔇"
            }
        return {
            "command": "volume_settings",
            "action": "open",
            "package": "com.android.settings",
            "response": "Volume settings khol raha hoon! 🔊"
        }

    if any(w in msg for w in ["share", "share karo", "ye bhejo"]):
        return {
            "command": "share",
            "action": "share",
            "response": "Kya share karna hai? Batao! 📤"
        }

    return None
