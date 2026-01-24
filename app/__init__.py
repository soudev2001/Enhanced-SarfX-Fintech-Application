from flask import Flask, render_template
from .config import Config
import logging

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Configuration des Logs pour Cloud Run
    logging.basicConfig(level=logging.INFO)

    # Services
    from .services.db_service import get_db, close_db
    app.teardown_appcontext(close_db)

    # Blueprints (Routes)
    from .routes.auth_routes import auth_bp
    from .routes.admin_routes import admin_bp
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

    # Gestionnaires d'erreurs
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('500.html', error=e), 500

    return app