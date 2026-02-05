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
    # OPENTELEMETRY TRACING
    # ============================================
    try:
        from .tracing import setup_tracing
        setup_tracing(app)
        logging.info("🔍 OpenTelemetry tracing enabled")
    except ImportError as e:
        logging.warning(f"⚠️ Tracing not available (install opentelemetry packages): {e}")
    except Exception as e:
        logging.warning(f"⚠️ Failed to initialize tracing: {e}")

    # ============================================
    # SECURITY EXTENSIONS
    # ============================================

    # CSRF Protection
    from flask_wtf.csrf import CSRFProtect
    csrf = CSRFProtect(app)

    # Gzip Compression
    from flask_compress import Compress
    Compress(app)

    # Security Headers (Talisman) - Only in production with SSL
    # Set FORCE_HTTPS=true in .env when SSL is configured
    if os.environ.get("FLASK_ENV") == "production" and os.environ.get("FORCE_HTTPS", "").lower() == "true":
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

    # ============================================
    # HEALTH CHECK ENDPOINT
    # ============================================
    @app.route('/health')
    def health_check():
        """Health check endpoint for Docker/Kubernetes"""
        from flask import jsonify
        from .services.db_service import get_db
        
        status = {"status": "healthy", "service": "sarfx-flask"}
        
        # Check MongoDB connection
        try:
            db = get_db()
            if db is not None:
                db.command('ping')
                status["mongodb"] = "connected"
            else:
                status["mongodb"] = "not configured"
        except Exception as e:
            status["mongodb"] = f"error: {str(e)}"
            status["status"] = "degraded"
        
        return jsonify(status), 200 if status["status"] == "healthy" else 503

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
        """Emoji flag filter (legacy)"""
        flags = {
            'USD': '🇺🇸', 'EUR': '🇪🇺', 'GBP': '🇬🇧', 'MAD': '🇲🇦',
            'CHF': '🇨🇭', 'CAD': '🇨🇦', 'AED': '🇦🇪', 'SAR': '🇸🇦'
        }
        return flags.get(currency, '💵')

    @app.template_filter('currency_flag')
    def currency_flag_filter(currency, size=24):
        """CDN flag image filter with emoji fallback"""
        from app.utils.flags import get_flag_url, get_flag_emoji
        url = get_flag_url(currency, size)
        emoji = get_flag_emoji(currency)
        return f'<img src="{url}" alt="{emoji}" class="currency-flag" style="width:{size}px;height:auto;border-radius:2px;vertical-align:middle;" onerror="this.outerHTML=\'{emoji}\'">'

    @app.template_filter('flag_url')
    def flag_url_filter(currency, size=40):
        """Get flag URL only"""
        from app.utils.flags import get_flag_url
        return get_flag_url(currency, size)

    @app.template_filter('flag_emoji')
    def flag_emoji_filter(currency):
        """Get emoji flag"""
        from app.utils.flags import get_flag_emoji
        return get_flag_emoji(currency)

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

    # Context processor to inject current_user in all templates
    @app.context_processor
    def inject_user():
        from flask import session
        from app.decorators import get_current_user
        user = get_current_user()
        # Add user preferences for templates
        user_theme = session.get('theme', 'light')
        user_accent_color = session.get('accent_color', 'orange')
        return dict(
            current_user=user,
            user_theme=user_theme,
            user_accent_color=user_accent_color
        )

    # Context processor for i18n
    @app.context_processor
    def inject_i18n():
        from app.services.i18n_service import I18nService
        i18n = I18nService()
        lang = i18n.get_current_language()
        return dict(
            t=i18n.t,
            tn=i18n.tn,
            current_lang=lang,
            is_rtl=i18n.is_rtl(lang),
            available_languages=i18n.get_available_languages()
        )

    return app