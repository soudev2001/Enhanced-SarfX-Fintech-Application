from flask import Flask, render_template
from .config import Config
import logging
import os

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Configuration des Logs pour Cloud Run
    logging.basicConfig(level=logging.INFO)

    # ============================================
    # SECURITY EXTENSIONS
    # ============================================

    # CSRF Protection
    from flask_wtf.csrf import CSRFProtect
    csrf = CSRFProtect(app)

    # Gzip Compression
    from flask_compress import Compress
    Compress(app)

    # Security Headers (Talisman) - Only in production
    if os.environ.get("FLASK_ENV") == "production":
        from flask_talisman import Talisman
        Talisman(app,
            content_security_policy=app.config.get('CSP_POLICY'),
            force_https=True,
            strict_transport_security=True,
            strict_transport_security_max_age=31536000,
            session_cookie_secure=True,
            session_cookie_http_only=True
        )

    # Rate Limiting
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address

    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"],
        storage_uri=app.config.get('RATELIMIT_STORAGE_URL', 'memory://')
    )
    # Store limiter in app for use in routes
    app.limiter = limiter

    # Redis Cache
    from flask_caching import Cache

    try:
        cache = Cache(app, config={
            'CACHE_TYPE': app.config.get('CACHE_TYPE', 'simple'),
            'CACHE_REDIS_URL': app.config.get('CACHE_REDIS_URL'),
            'CACHE_DEFAULT_TIMEOUT': app.config.get('CACHE_DEFAULT_TIMEOUT', 300)
        })
    except Exception as e:
        logging.warning(f"Redis cache failed, falling back to simple cache: {e}")
        cache = Cache(app, config={'CACHE_TYPE': 'simple'})

    app.cache = cache

    # ============================================
    # GOOGLE OAUTH SETUP
    # ============================================
    from authlib.integrations.flask_client import OAuth

    oauth = OAuth(app)

    if app.config.get('GOOGLE_CLIENT_ID') and app.config.get('GOOGLE_CLIENT_SECRET'):
        oauth.register(
            name='google',
            client_id=app.config['GOOGLE_CLIENT_ID'],
            client_secret=app.config['GOOGLE_CLIENT_SECRET'],
            server_metadata_url=app.config['GOOGLE_DISCOVERY_URL'],
            client_kwargs={
                'scope': 'openid email profile'
            }
        )
        logging.info("✅ Google OAuth configured successfully")
    else:
        logging.warning("⚠️ Google OAuth not configured - missing GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET")

    app.oauth = oauth

    # Services
    from .services.db_service import get_db, close_db
    app.teardown_appcontext(close_db)

    # Blueprints (Routes)
    from .routes.auth_routes import auth_bp
    from .routes.admin import admin_bp
    from .routes.supplier_routes import supplier_bp
    from .routes.app_routes import app_bp
    from .routes.api_routes import api_bp
    from .routes.admin_bank_routes import admin_banks_bp
    from .routes.landing_routes import landing_bp

    app.register_blueprint(landing_bp)  # Landing page (/)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(supplier_bp) # Préfixe géré dans le blueprint
    app.register_blueprint(app_bp, url_prefix='/app')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(admin_banks_bp) # /admin/banks

    # Exempt CSRF for API routes
    csrf.exempt(api_bp)

    # Gestionnaires d'erreurs
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html', error=e), 500

    @app.errorhandler(429)
    def ratelimit_handler(e):
        return render_template('errors/429.html', error="Trop de requêtes. Veuillez réessayer plus tard."), 429

    # Custom Jinja2 filters
    @app.template_filter('get_flag')
    def get_flag(currency):
        flags = {
            'USD': '🇺🇸', 'EUR': '🇪🇺', 'GBP': '🇬🇧', 'MAD': '🇲🇦',
            'CHF': '🇨🇭', 'CAD': '🇨🇦', 'AED': '🇦🇪', 'SAR': '🇸🇦'
        }
        return flags.get(currency, '💵')

    @app.template_filter('get_transaction_icon')
    def get_transaction_icon(transaction_type):
        icons = {
            'deposit': 'arrow-down-left',
            'withdrawal': 'arrow-up-right',
            'transfer': 'arrow-right-left'
        }
        return icons.get(transaction_type, 'activity')

    @app.template_filter('number_format')
    def number_format(value):
        if isinstance(value, (int, float)):
            try:
                return f"{int(value):,}"
            except (ValueError, TypeError):
                return value
        return value

    return app