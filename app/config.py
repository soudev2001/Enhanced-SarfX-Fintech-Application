import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Sécurité : Clé secrète obligatoire en prod
    SECRET_KEY = os.environ.get("SECRET_KEY")
    if not SECRET_KEY:
        if os.environ.get("FLASK_ENV") == "production":
            raise ValueError("SECRET_KEY must be set in production!")
        SECRET_KEY = "dev-secret-key-change-in-production"

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

    # Session Security
    SESSION_COOKIE_SECURE = True  # Requis pour HTTPS (Cloud Run)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 3600  # 1 heure

    # ============================================
    # GOOGLE OAUTH 2.0 CONFIGURATION
    # ============================================
    GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
    GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

    # OAuth Redirect URI (production)
    OAUTH_REDIRECT_URI = os.environ.get("OAUTH_REDIRECT_URI", "https://sarfx.io/auth/login/google/callback")

    # ============================================
    # REDIS CACHE CONFIGURATION
    # ============================================
    # Auto-detect: use Redis in production, simple/memory in dev
    _redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

    # Check if we should use Redis or fallback to simple cache
    if os.environ.get("CACHE_TYPE"):
        CACHE_TYPE = os.environ.get("CACHE_TYPE")
    elif os.environ.get("FLASK_ENV") == "production":
        CACHE_TYPE = "redis"
    else:
        CACHE_TYPE = "simple"  # Use simple cache for Windows/dev

    CACHE_REDIS_URL = _redis_url
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes

    # ============================================
    # RATE LIMITING
    # ============================================
    # Use memory storage for dev, Redis for production
    if os.environ.get("FLASK_ENV") == "production":
        RATELIMIT_STORAGE_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/1")
    else:
        RATELIMIT_STORAGE_URL = "memory://"  # In-memory for dev/Windows

    RATELIMIT_STRATEGY = "fixed-window"
    RATELIMIT_DEFAULT = "200 per day, 50 per hour"

    # ============================================
    # SECURITY HEADERS (CSP)
    # ============================================
    CSP_POLICY = {
        'default-src': "'self'",
        'script-src': [
            "'self'",
            "'unsafe-inline'",
            "'unsafe-eval'",  # Needed for some JS libraries
            "https://unpkg.com",
            "https://cdn.tailwindcss.com",
            "https://cdn.jsdelivr.net",
            "https://accounts.google.com",
            "https://apis.google.com",
        ],
        'style-src': [
            "'self'",
            "'unsafe-inline'",
            "https://fonts.googleapis.com",
            "https://cdn.tailwindcss.com",
        ],
        'font-src': ["'self'", "https://fonts.gstatic.com", "data:"],
        'img-src': ["'self'", "data:", "https:", "blob:"],
        'connect-src': [
            "'self'",
            "https://accounts.google.com",
            "https://www.googleapis.com",
            "https://unpkg.com",
            "https://cdn.jsdelivr.net",
        ],
        'frame-src': ["'self'", "https://accounts.google.com"],
    }

    # Disable Talisman (CSP) in development - causes issues with hot reload
    TALISMAN_ENABLED = os.environ.get("FLASK_ENV") == "production"