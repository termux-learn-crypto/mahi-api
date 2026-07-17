import jwt
import hashlib
import secrets
import time
from functools import wraps
from flask import request, jsonify, g
from .config import config


def generate_token(user_id: str, role: str = "user") -> str:
    payload = {
        "user_id": user_id,
        "role": role,
        "iat": time.time(),
        "exp": time.time() + (config.JWT_EXPIRY_HOURS * 3600),
    }
    return jwt.encode(payload, config.SECRET_KEY, algorithm="HS256")


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, config.SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def generate_api_key() -> str:
    return f"mahi_{secrets.token_hex(32)}"


def hash_api_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode()).hexdigest()


API_KEYS = {}


def register_api_key(name: str) -> str:
    api_key = generate_api_key()
    API_KEYS[hash_api_key(api_key)] = {"name": name, "created_at": time.time()}
    return api_key


def validate_api_key(api_key: str) -> bool:
    key_hash = hash_api_key(api_key)
    return key_hash in API_KEYS


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if not token:
            return jsonify({"error": "Token required"}), 401

        data = decode_token(token)
        if not data:
            return jsonify({"error": "Invalid or expired token"}), 401

        g.current_user = data["user_id"]
        g.user_role = data.get("role", "user")
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if not token:
            return jsonify({"error": "Token required"}), 401

        data = decode_token(token)
        if not data:
            return jsonify({"error": "Invalid or expired token"}), 401

        if data.get("role") != "admin":
            return jsonify({"error": "Admin access required"}), 403

        g.current_user = data["user_id"]
        g.user_role = "admin"
        return f(*args, **kwargs)
    return decorated


def api_key_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            return jsonify({"error": "API key required"}), 401

        if not validate_api_key(api_key):
            return jsonify({"error": "Invalid API key"}), 401

        return f(*args, **kwargs)
    return decorated


def optional_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if token:
            data = decode_token(token)
            if data:
                g.current_user = data["user_id"]
                g.user_role = data.get("role", "user")
            else:
                g.current_user = None
                g.user_role = None
        else:
            g.current_user = request.get_json(silent=True, force=True).get("user_id") if request.is_json else None
            g.user_role = None
        return f(*args, **kwargs)
    return decorated
