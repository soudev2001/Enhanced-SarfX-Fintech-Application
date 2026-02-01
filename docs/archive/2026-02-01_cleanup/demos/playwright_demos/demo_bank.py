"""
Démo Playwright pour le rôle BANK RESPONSABLE
Tour complet de l'interface banque (2-3 minutes)
"""
from playwright.sync_api import Page
from .demo_base import DemoBase
from .config import BASE_URL, DELAYS


class BankDemo(DemoBase):
    """Démonstration complète du rôle Responsable Banque"""
    
    def __init__(self, headless: bool = False):
        super().__init__('bank', headless)
    
    def execute_demo(self, page: Page, result: dict):
        """
        Scénario Bank Responsable:
        1. Connexion via bouton démo
        2. Accueil utilisateur
        3. Configuration Banque
        4. Gestion des ATMs de la banque
        5. Convertisseur de devises
        6. Wallets
        7. Transactions
        8. Déconnexion
        """
        self.log("🎬 Début de la démo Bank Responsable")
        
        # 1. Connexion
        self.login_with_demo_button(page, result)
        
        # 2. Vue d'accueil
        self.subtitles.add(self.get_subtitle('home_view'))
        self.take_screenshot(page, 'home', result)
        self.wait(delay_type='long')
        
        # Scroll pour voir les widgets
        page.evaluate("window.scrollBy(0, 400)")
        self.wait(delay_type='medium')
        self.subtitles.add("📊 Aperçu des taux et services")
        self.take_screenshot(page, 'home_scrolled', result)
        
        # 3. Configuration Banque
        self.subtitles.add("🏦 Configuration de la banque...")
        page.goto(f"{BASE_URL}/app/bank-settings")
        self.wait(delay_type='page_load')
        self.subtitles.add(self.get_subtitle('bank_config'))
        self.take_screenshot(page, 'bank_settings', result)
        self.wait(delay_type='long')
        
        # Montrer les paramètres API
        page.evaluate("window.scrollBy(0, 300)")
        self.wait(delay_type='medium')
        self.subtitles.add("🔑 Configuration des APIs bancaires")
        self.take_screenshot(page, 'bank_api_config', result)
        
        # 4. Gestion ATMs (via admin si accès)
        self.subtitles.add("🏧 Accès aux ATMs de la banque...")
        page.goto(f"{BASE_URL}/admin/atms")
        self.wait(delay_type='page_load')
        self.subtitles.add("📍 Gestion des distributeurs de la banque")
        self.take_screenshot(page, 'bank_atms', result)
        self.wait(delay_type='medium')
        
        # 5. Convertisseur de devises
        self.subtitles.add("💱 Accès au convertisseur...")
        page.goto(f"{BASE_URL}/app/converter")
        self.wait(delay_type='page_load')
        self.subtitles.add(self.get_subtitle('converter_view'))
        self.take_screenshot(page, 'converter', result)
        
        # Interagir avec le convertisseur
        try:
            amount_input = page.locator('input[type="number"], .wise-amount-input').first
            if amount_input.is_visible():
                amount_input.fill('5000')
                self.wait(delay_type='medium')
                self.subtitles.add("💵 Conversion de 5000 MAD")
                self.take_screenshot(page, 'converter_filled', result)
        except:
            pass
        
        # 6. Wallets
        self.subtitles.add("💰 Gestion des portefeuilles...")
        page.goto(f"{BASE_URL}/app/wallets")
        self.wait(delay_type='page_load')
        self.subtitles.add(self.get_subtitle('wallets_view'))
        self.take_screenshot(page, 'wallets', result)
        self.wait(delay_type='long')
        
        # 7. Historique des transactions
        self.subtitles.add("📊 Historique des opérations...")
        page.goto(f"{BASE_URL}/app/transactions")
        self.wait(delay_type='page_load')
        self.subtitles.add(self.get_subtitle('transactions_view'))
        self.take_screenshot(page, 'transactions', result)
        self.wait(delay_type='medium')
        
        # 8. Localisation ATMs
        self.subtitles.add("📍 Carte des distributeurs...")
        page.goto(f"{BASE_URL}/app/atms")
        self.wait(delay_type='page_load')
        self.subtitles.add(self.get_subtitle('atms_view'))
        self.take_screenshot(page, 'atms_map', result)
        self.wait(delay_type='long')
        
        # 9. IA Prédictions
        self.subtitles.add("🤖 Prédictions IA...")
        page.goto(f"{BASE_URL}/app/ai")
        self.wait(delay_type='page_load')
        self.subtitles.add("🧠 Analyses et prédictions par IA")
        self.take_screenshot(page, 'ai_predictions', result)
        self.wait(delay_type='medium')
        
        # 10. Profil
        self.subtitles.add("👤 Profil utilisateur...")
        page.goto(f"{BASE_URL}/app/profile")
        self.wait(delay_type='page_load')
        self.subtitles.add(self.get_subtitle('profile_view'))
        self.take_screenshot(page, 'profile', result)
        
        # 11. Déconnexion
        self.wait(delay_type='medium')
        self.logout(page, result)
        
        self.log("✅ Démo Bank Responsable terminée")


def run_bank_demo(headless: bool = False) -> dict:
    """Fonction pour lancer la démo bank"""
    demo = BankDemo(headless=headless)
    return demo.run()


if __name__ == '__main__':
    import sys
    headless = '--headless' in sys.argv
    result = run_bank_demo(headless=headless)
    print(f"Résultat: {result}")
