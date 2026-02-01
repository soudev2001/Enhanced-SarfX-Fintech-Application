"""
Démo Playwright pour le rôle ADMIN
Tour complet de l'interface administrateur (2-3 minutes)
"""
from playwright.sync_api import Page
from .demo_base import DemoBase
from .config import BASE_URL, DELAYS


class AdminDemo(DemoBase):
    """Démonstration complète du rôle Administrateur"""
    
    def __init__(self, headless: bool = False):
        super().__init__('admin', headless)
    
    def execute_demo(self, page: Page, result: dict):
        """
        Scénario Admin:
        1. Connexion via bouton démo
        2. Dashboard Admin
        3. Gestion des utilisateurs
        4. Banques partenaires
        5. Gestion des DAB
        6. Transactions
        7. Configuration API
        8. Déconnexion
        """
        self.log("🎬 Début de la démo Admin")
        
        # 1. Connexion
        self.login_with_demo_button(page, result)
        
        # 2. Vue d'accueil utilisateur
        self.subtitles.add(self.get_subtitle('home_view'))
        self.take_screenshot(page, 'home', result)
        self.wait(delay_type='long')
        
        # 3. Aller au Dashboard Admin
        self.subtitles.add("🛡️ Accès au panneau d'administration...")
        page.goto(f"{BASE_URL}/admin")
        self.wait(delay_type='page_load')
        self.subtitles.add(self.get_subtitle('admin_dashboard'))
        self.take_screenshot(page, 'admin_dashboard', result)
        
        # Scroll pour montrer les stats
        page.evaluate("window.scrollBy(0, 300)")
        self.wait(delay_type='medium')
        self.subtitles.add("📊 Statistiques en temps réel")
        self.take_screenshot(page, 'admin_stats', result)
        
        # 4. Gestion des utilisateurs
        self.subtitles.add("👥 Gestion des utilisateurs...")
        page.goto(f"{BASE_URL}/admin/users")
        self.wait(delay_type='page_load')
        self.subtitles.add(self.get_subtitle('admin_users'))
        self.take_screenshot(page, 'admin_users', result)
        
        # Montrer les filtres
        self.wait(delay_type='medium')
        self.subtitles.add("🔍 Filtrage et recherche d'utilisateurs")
        self.take_screenshot(page, 'admin_users_filters', result)
        
        # 5. Banques partenaires
        self.subtitles.add("🏛️ Banques partenaires...")
        page.goto(f"{BASE_URL}/admin/banks")
        self.wait(delay_type='page_load')
        self.subtitles.add(self.get_subtitle('admin_banks'))
        self.take_screenshot(page, 'admin_banks', result)
        self.wait(delay_type='long')
        
        # 6. Gestion des DAB
        self.subtitles.add("🏧 Gestion des distributeurs...")
        page.goto(f"{BASE_URL}/admin/atms")
        self.wait(delay_type='page_load')
        self.subtitles.add(self.get_subtitle('admin_atms'))
        self.take_screenshot(page, 'admin_atms', result)
        
        # Dashboard ATM
        page.goto(f"{BASE_URL}/admin/atm-dashboard")
        self.wait(delay_type='page_load')
        self.subtitles.add("📈 Dashboard ATM avec graphiques")
        self.take_screenshot(page, 'admin_atm_dashboard', result)
        self.wait(delay_type='long')
        
        # 7. Transactions
        self.subtitles.add("💹 Suivi des transactions...")
        page.goto(f"{BASE_URL}/admin/transactions")
        self.wait(delay_type='page_load')
        self.subtitles.add(self.get_subtitle('transactions_view'))
        self.take_screenshot(page, 'admin_transactions', result)
        
        # 8. Configuration API
        self.subtitles.add("🔧 Configuration des APIs...")
        page.goto(f"{BASE_URL}/admin/api-control")
        self.wait(delay_type='page_load')
        self.subtitles.add("⚙️ Contrôle des sources de données")
        self.take_screenshot(page, 'admin_api', result)
        self.wait(delay_type='medium')
        
        # 9. Wallets (vue admin)
        self.subtitles.add("💰 Aperçu des portefeuilles...")
        page.goto(f"{BASE_URL}/admin/wallets")
        self.wait(delay_type='page_load')
        self.subtitles.add("💳 Tous les portefeuilles utilisateurs")
        self.take_screenshot(page, 'admin_wallets', result)
        
        # 10. Bénéficiaires
        self.subtitles.add("👥 Liste des bénéficiaires...")
        page.goto(f"{BASE_URL}/admin/beneficiaries")
        self.wait(delay_type='page_load')
        self.subtitles.add("📋 Gestion des bénéficiaires")
        self.take_screenshot(page, 'admin_beneficiaries', result)
        
        # 11. Retour accueil et déconnexion
        self.wait(delay_type='medium')
        self.logout(page, result)
        
        self.log("✅ Démo Admin terminée")


def run_admin_demo(headless: bool = False) -> dict:
    """Fonction pour lancer la démo admin"""
    demo = AdminDemo(headless=headless)
    return demo.run()


if __name__ == '__main__':
    import sys
    headless = '--headless' in sys.argv
    result = run_admin_demo(headless=headless)
    print(f"Résultat: {result}")
