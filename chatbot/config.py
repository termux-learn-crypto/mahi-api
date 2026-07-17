import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOADS_DIR = BASE_DIR / "uploads"
LOGS_DIR = BASE_DIR / "logs"

DATA_DIR.mkdir(exist_ok=True)
UPLOADS_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "mahi-secret-key-change-in-production-2024")
    JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", "24"))
    DATABASE_PATH = str(DATA_DIR / "mahi.db")

    STT_API_KEY = os.getenv("STT_API_KEY", "")
    STT_PROVIDER = os.getenv("STT_PROVIDER", "google")

    TTS_API_KEY = os.getenv("TTS_API_KEY", "")
    TTS_PROVIDER = os.getenv("TTS_PROVIDER", "google")

    WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "")
    NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
    SEARCH_API_KEY = os.getenv("SEARCH_API_KEY", "")

    EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
    EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
    EMAIL_USER = os.getenv("EMAIL_USER", "")
    EMAIL_PASS = os.getenv("EMAIL_PASS", "")

    RATE_LIMIT_MAX = int(os.getenv("RATE_LIMIT_MAX", "30"))
    RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))

    MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", "10485760"))
    ALLOWED_EXTENSIONS = {"pdf", "docx", "txt", "md", "csv", "json"}

    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"

    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")

    MAX_SESSIONS = int(os.getenv("MAX_SESSIONS", "1000"))
    SESSION_TTL = int(os.getenv("SESSION_TTL", "7200"))

    PORT = int(os.getenv("PORT", "5000"))


config = Config()
