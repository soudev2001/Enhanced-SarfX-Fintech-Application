"""
Démo Playwright pour le rôle USER (utilisateur standard)
Tour complet de l'interface utilisateur (2-3 minutes)
"""
from playwright.sync_api import Page
from .demo_base import DemoBase
from .config import BASE_URL, DELAYS


class UserDemo(DemoBase):
    """Démonstration complète du rôle Utilisateur"""
    
    def __init__(self, headless: bool = False):
        super().__init__('user', headless)
    
    def execute_demo(self, page: Page, result: dict):
        """
        Scénario User:
        1. Connexion via bouton démo
        2. Accueil avec taux en direct
        3. Portefeuilles
        4. Convertisseur interactif
        5. Localisation DAB
        6. Bénéficiaires
        7. Historique transactions
        8. IA Prédictions
        9. FAQ
        10. Profil et paramètres
        11. Déconnexion
        """
        self.log("🎬 Début de la démo Utilisateur")
        
        # 1. Connexion
        self.login_with_demo_button(page, result)
        
        # 2. Vue d'accueil
        self.subtitles.add(self.get_subtitle('home_view'))
        self.take_screenshot(page, 'home', result)
        self.wait(delay_type='long')
        
        # Interagir avec le widget de conversion rapide
        self.subtitles.add("💹 Taux de change en temps réel")
        page.evaluate("window.scrollBy(0, 300)")
        self.wait(delay_type='medium')
        self.take_screenshot(page, 'home_rates', result)
        
        # Continuer le scroll
        page.evaluate("window.scrollBy(0, 400)")
        self.wait(delay_type='medium')
        self.subtitles.add("🔄 Services disponibles")
        self.take_screenshot(page, 'home_services', result)
        
        # 3. Portefeuilles
        self.subtitles.add("💰 Mes portefeuilles...")
        page.goto(f"{BASE_URL}/app/wallets")
        self.wait(delay_type='page_load')
        self.subtitles.add(self.get_subtitle('wallets_view'))
        self.take_screenshot(page, 'wallets', result)
        self.wait(delay_type='long')
        
        # Montrer les différentes devises
        page.evaluate("window.scrollBy(0, 200)")
        self.wait(delay_type='short')
        self.subtitles.add("💵 Multi-devises: MAD, EUR, USD...")
        self.take_screenshot(page, 'wallets_multi', result)
        
        # 4. Convertisseur
        self.subtitles.add("💱 Convertisseur de devises...")
        page.goto(f"{BASE_URL}/app/converter")
        self.wait(delay_type='page_load')
        self.subtitles.add(self.get_subtitle('converter_view'))
        self.take_screenshot(page, 'converter', result)
        
        # Simuler une conversion
        try:
            amount_input = page.locator('input[type="number"], .wise-amount-input').first
            if amount_input.is_visible():
                amount_input.fill('1000')
                self.wait(delay_type='medium')
                self.subtitles.add("💵 Conversion de 1000 MAD en EUR")
                self.take_screenshot(page, 'converter_1000', result)
                
                # Changer le montant
                amount_input.fill('5000')
                self.wait(delay_type='medium')
                self.subtitles.add("💵 Conversion de 5000 MAD")
                self.take_screenshot(page, 'converter_5000', result)
        except:
            pass
        
        # Montrer les fournisseurs
        page.evaluate("window.scrollBy(0, 300)")
        self.wait(delay_type='medium')
        self.subtitles.add("🏦 Comparaison des taux entre fournisseurs")
        self.take_screenshot(page, 'converter_providers', result)
        
        # 5. Localisation DAB
        self.subtitles.add("📍 Trouver un DAB...")
        page.goto(f"{BASE_URL}/app/atms")
        self.wait(delay_type='page_load')
        self.subtitles.add(self.get_subtitle('atms_view'))
        self.take_screenshot(page, 'atms', result)
        self.wait(delay_type='long')
        
        # Attendre le chargement de la carte
        self.wait(delay_type='medium')
        self.subtitles.add("🗺️ Carte interactive des distributeurs")
        self.take_screenshot(page, 'atms_map', result)
        
        # 6. Bénéficiaires
        self.subtitles.add("👥 Mes bénéficiaires...")
        page.goto(f"{BASE_URL}/app/beneficiaries")
        self.wait(delay_type='page_load')
        self.subtitles.add("📋 Gestion des bénéficiaires")
        self.take_screenshot(page, 'beneficiaries', result)
        self.wait(delay_type='medium')
        
        # 7. Historique des transactions
        self.subtitles.add("📊 Mes transactions...")
        page.goto(f"{BASE_URL}/app/transactions")
        self.wait(delay_type='page_load')
        self.subtitles.add(self.get_subtitle('transactions_view'))
        self.take_screenshot(page, 'transactions', result)
        self.wait(delay_type='medium')
        
        # Montrer les filtres
        self.subtitles.add("🔍 Filtrage par type de transaction")
        self.take_screenshot(page, 'transactions_filters', result)
        
        # 8. Historique des taux
        self.subtitles.add("📈 Historique des taux...")
        page.goto(f"{BASE_URL}/app/rate-history")
        self.wait(delay_type='page_load')
        self.subtitles.add("📊 Évolution des taux de change")
        self.take_screenshot(page, 'rate_history', result)
        self.wait(delay_type='long')
        
        # 9. IA Prédictions
        self.subtitles.add("🤖 Prédictions IA...")
        page.goto(f"{BASE_URL}/app/ai")
        self.wait(delay_type='page_load')
        self.subtitles.add("🧠 Analyses et recommandations IA")
        self.take_screenshot(page, 'ai', result)
        self.wait(delay_type='medium')
        
        # 10. FAQ
        self.subtitles.add("❓ Centre d'aide...")
        page.goto(f"{BASE_URL}/app/faq")
        self.wait(delay_type='page_load')
        self.subtitles.add("📚 Questions fréquentes")
        self.take_screenshot(page, 'faq', result)
        self.wait(delay_type='short')
        
        # 11. Profil
        self.subtitles.add("👤 Mon profil...")
        page.goto(f"{BASE_URL}/app/profile")
        self.wait(delay_type='page_load')
        self.subtitles.add(self.get_subtitle('profile_view'))
        self.take_screenshot(page, 'profile', result)
        self.wait(delay_type='medium')
        
        # 12. Paramètres
        self.subtitles.add("⚙️ Paramètres...")
        page.goto(f"{BASE_URL}/app/settings")
        self.wait(delay_type='page_load')
        self.subtitles.add(self.get_subtitle('settings_view'))
        self.take_screenshot(page, 'settings', result)
        self.wait(delay_type='short')
        
        # 13. Déconnexion
        self.wait(delay_type='medium')
        self.logout(page, result)
        
        self.log("✅ Démo Utilisateur terminée")


def run_user_demo(headless: bool = False) -> dict:
    """Fonction pour lancer la démo user"""
    demo = UserDemo(headless=headless)
    return demo.run()


if __name__ == '__main__':
    import sys
    headless = '--headless' in sys.argv
    result = run_user_demo(headless=headless)
    print(f"Résultat: {result}")
