import re
import secrets
import string
from . import Plugin


class PasswordGenPlugin(Plugin):
    def __init__(self):
        super().__init__(
            name="password_gen",
            description="Generate secure passwords with customizable length and character types",
            version="1.0.0",
        )
        self.commands = ["password", "generate password", "password banao"]
        self.keywords = [
            "password", "passwd", "generate", "secure", "random",
            "password banao", "password generator",
        ]

    def can_handle(self, intent: str, message: str) -> bool:
        if intent == "password":
            return True
        msg = message.lower()
        return any(kw in msg for kw in self.keywords)

    def execute(self, user_id: str, message: str, context: dict) -> dict:
        msg = message.lower()

        length = 16
        length_match = re.search(r'(\d+)\s*(?:char|length|lamba|size)', msg)
        if length_match:
            length = max(6, min(128, int(length_match.group(1))))
        else:
            num_match = re.search(r'(\d+)', msg)
            if num_match:
                candidate = int(num_match.group(1))
                if 6 <= candidate <= 128:
                    length = candidate

        use_upper = not bool(re.search(r'\b(no caps?|no uppercase|bina bade|small only|lower only)\b', msg))
        use_lower = not bool(re.search(r'\b(no small|no lowercase|bina chhote|capital only|upper only)\b', msg))
        use_digits = not bool(re.search(r'\b(no digits?|no numbers?|bina number|bina digit)\b', msg))
        use_special = bool(re.search(r'\b(special|symbol|extra|complex|mushkil|strong|safe)\b', msg)) or \
            not bool(re.search(r'\b(easy|simple|basic|aasan|no special|no symbol)\b', msg))

        if not any([use_upper, use_lower, use_digits]):
            use_lower = True
            use_upper = True

        password = self._generate(length, use_upper, use_lower, use_digits, use_special)
        strength = self._strength_score(password, length)
        strength_emoji = {"Strong": "💪", "Medium": "👍", "Weak": "⚠\uFE0F"}

        charset_info = []
        if use_upper:
            charset_info.append("A-Z")
        if use_lower:
            charset_info.append("a-z")
        if use_digits:
            charset_info.append("0-9")
        if use_special:
            charset_info.append("!@#$%...")

        response = (
            f"🔐 Tumhara password ready hai:\n\n"
            f"`{password}`\n\n"
            f"📏 Length: {length}\n"
            f"🎯 Characters: {' + '.join(charset_info)}\n"
            f"💪 Strength: {strength_emoji.get(strength, '')} {strength}\n\n"
            f"⚠\uFE0F Password copy kar lo aur safe rakho!"
        )
        return {
            "response": response,
            "data": {
                "password": password, "length": length,
                "strength": strength, "uppercase": use_upper,
                "lowercase": use_lower, "digits": use_digits,
                "special": use_special,
            },
        }

    @staticmethod
    def _generate(length: int, upper: bool, lower: bool, digits: bool, special: bool) -> str:
        chars = []
        required = []
        if upper:
            chars.extend(string.ascii_uppercase)
            required.append(secrets.choice(string.ascii_uppercase))
        if lower:
            chars.extend(string.ascii_lowercase)
            required.append(secrets.choice(string.ascii_lowercase))
        if digits:
            chars.extend(string.digits)
            required.append(secrets.choice(string.digits))
        if special:
            special_chars = "!@#$%^&*()-_=+[]{}|;:,.<>?"
            chars.extend(special_chars)
            required.append(secrets.choice(special_chars))

        if not chars:
            chars = string.ascii_letters + string.digits
            required = [secrets.choice(string.ascii_letters)]

        remaining = [secrets.choice(chars) for _ in range(length - len(required))]
        password_list = required + remaining

        indices = list(range(len(password_list)))
        for i in range(len(indices) - 1, 0, -1):
            j = secrets.randbelow(i + 1)
            indices[i], indices[j] = indices[j], indices[i]

        return ''.join(password_list[i] for i in indices)

    @staticmethod
    def _strength_score(password: str, length: int) -> str:
        score = 0
        if length >= 12:
            score += 1
        if length >= 16:
            score += 1
        if any(c in string.ascii_uppercase for c in password):
            score += 1
        if any(c in string.ascii_lowercase for c in password):
            score += 1
        if any(c in string.digits for c in password):
            score += 1
        if any(c in "!@#$%^&*()-_=+[]{}|;:,.<>?" for c in password):
            score += 1
        if score >= 5:
            return "Strong"
        if score >= 3:
            return "Medium"
        return "Weak"
