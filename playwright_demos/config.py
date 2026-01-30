"""
Configuration pour les démos Playwright SarfX
"""
import os

# URLs
BASE_URL = os.environ.get('SARFX_URL', 'https://sarfx.io')
LOGIN_URL = f"{BASE_URL}/auth/login"

# Comptes de démonstration
DEMO_ACCOUNTS = {
    'admin': {
        'email': 'admin@sarfx.io',
        'password': 'admin123',
        'name': 'Admin Demo',
        'role': 'admin',
        'emoji': '👑'
    },
    'bank': {
        'email': 'bank@sarfx.io',
        'password': 'bank123',
        'name': 'Bank Respo Demo',
        'role': 'bank_admin',
        'emoji': '🏦'
    },
    'user': {
        'email': 'user@sarfx.io',
        'password': 'user123',
        'name': 'User Demo',
        'role': 'user',
        'emoji': '👤'
    }
}

# Chemins de sortie
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'robot_results', 'playwright')
VIDEOS_DIR = os.path.join(OUTPUT_DIR, 'videos')
SCREENSHOTS_DIR = os.path.join(OUTPUT_DIR, 'screenshots')

# Paramètres vidéo
VIDEO_CONFIG = {
    'width': 1280,
    'height': 720,
    'fps': 30
}

# Délais (en ms)
DELAYS = {
    'short': 500,
    'medium': 1000,
    'long': 2000,
    'page_load': 3000,
    'action': 800
}

# Sous-titres pour chaque action
SUBTITLES = {
    'fr': {
        'login_start': "🔐 Connexion à SarfX...",
        'login_demo_click': "📱 Clic sur Connexion Démo Rapide",
        'login_success': "✅ Connexion réussie !",
        'home_view': "🏠 Bienvenue sur le Dashboard",
        'wallets_view': "💰 Gestion des Portefeuilles",
        'converter_view': "💱 Convertisseur de devises",
        'atms_view': "📍 Localisation des DAB",
        'transactions_view': "📊 Historique des transactions",
        'profile_view': "👤 Profil utilisateur",
        'settings_view': "⚙️ Paramètres",
        'admin_dashboard': "🛡️ Dashboard Administrateur",
        'admin_users': "👥 Gestion des utilisateurs",
        'admin_banks': "🏛️ Banques partenaires",
        'admin_atms': "🏧 Gestion des DAB",
        'bank_config': "🏦 Configuration Banque",
        'logout': "👋 Déconnexion",
        'demo_complete': "🎬 Démonstration terminée !"
    }
}
