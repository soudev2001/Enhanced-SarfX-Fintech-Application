import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Sécurité : Clé secrète obligatoire en prod
    SECRET_KEY = os.environ.get("SECRET_KEY", os.urandom(24))

    # Base de données
    MONGO_URI = os.environ.get("MONGO_URI")
    DB_NAME = "SarfX_Enhanced"

    # Gemini AI API
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

    # SarfX AI Backend (FastAPI)
    AI_BACKEND_URL = os.environ.get("AI_BACKEND_URL", "http://localhost:8087")
    AI_BACKEND_TIMEOUT = int(os.environ.get("AI_BACKEND_TIMEOUT", 5))  # secondes

    # Cache TTL for rates (secondes)
    RATES_CACHE_TTL = int(os.environ.get("RATES_CACHE_TTL", 30))

    # SMTP (Email)
    SMTP_EMAIL = os.environ.get("SMTP_EMAIL")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
    SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))

    # Options
    SESSION_COOKIE_SECURE = True # Requis pour HTTPS (Cloud Run)
    SESSION_COOKIE_HTTPONLY = True
    PERMANENT_SESSION_LIFETIME = 3600 # 1 heure