import hashlib
import base64
import secrets
import hmac
import os


class EncryptionEngine:
    def __init__(self):
        self.key = self._get_or_generate_key()

    def _get_or_generate_key(self) -> bytes:
        key_file = os.path.join(os.path.dirname(__file__), "..", "data", "encryption.key")

        if os.path.exists(key_file):
            with open(key_file, "rb") as f:
                return f.read().strip()

        key = secrets.token_bytes(32)
        os.makedirs(os.path.dirname(key_file), exist_ok=True)
        with open(key_file, "wb") as f:
            f.write(key)
        return key

    def encrypt(self, data: str) -> str:
        key = self.key
        data_bytes = data.encode("utf-8")

        nonce = secrets.token_bytes(16)

        encrypted = bytearray()
        for i, byte in enumerate(data_bytes):
            key_byte = key[i % len(key)]
            encrypted.append(byte ^ key_byte ^ nonce[i % len(nonce)])

        payload = nonce + bytes(encrypted)
        return base64.b64encode(payload).decode()

    def decrypt(self, encrypted_data: str) -> str:
        key = self.key
        payload = base64.b64decode(encrypted_data)

        nonce = payload[:16]
        encrypted = payload[16:]

        decrypted = bytearray()
        for i, byte in enumerate(encrypted):
            key_byte = key[i % len(key)]
            decrypted.append(byte ^ key_byte ^ nonce[i % len(nonce)])

        return bytes(decrypted).decode("utf-8")

    def hash_data(self, data: str) -> str:
        return hashlib.sha256(data.encode()).hexdigest()

    def generate_secure_token(self, length: int = 32) -> str:
        return secrets.token_hex(length)

    def encrypt_message(self, message: str, user_key: str = None) -> dict:
        if user_key:
            key = hashlib.sha256(user_key.encode()).digest()
            encrypted_bytes = self._xor_encrypt(message.encode(), key)
        else:
            encrypted_bytes = self._xor_encrypt(message.encode(), self.key)

        return {
            "encrypted": base64.b64encode(encrypted_bytes).decode(),
            "algorithm": "XOR-256",
            "has_custom_key": user_key is not None,
        }

    def decrypt_message(self, encrypted_message: str, user_key: str = None) -> dict:
        try:
            decoded = base64.b64decode(encrypted_message)

            if user_key:
                key = hashlib.sha256(user_key.encode()).digest()
                decrypted = self._xor_encrypt(decoded, key).decode("utf-8")
            else:
                decrypted = self._xor_encrypt(decoded, self.key).decode("utf-8")

            return {"decrypted": decrypted, "success": True}
        except Exception as e:
            return {"error": str(e), "success": False}

    def _xor_encrypt(self, data: bytes, key: bytes) -> bytes:
        return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))


encryption = EncryptionEngine()
