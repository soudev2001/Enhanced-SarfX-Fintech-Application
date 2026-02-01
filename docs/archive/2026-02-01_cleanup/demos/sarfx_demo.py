#!/usr/bin/env python3
"""
SarfX Demo Robot - Script standalone pour démonstration
========================================================

Exécution:
    python sarfx_demo.py --role admin --visible
    python sarfx_demo.py --role bank --visible
    python sarfx_demo.py --role user --visible
    python sarfx_demo.py --role admin --headless

Prérequis:
    pip install playwright
    playwright install chromium
"""
import argparse
import time
import os
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5000"

# Boutons Quick Login sur la page /auth/login
QUICK_LOGIN_BUTTONS = {
    'admin': 'Admin Demo',
    'bank': 'Bank Respo Demo',
    'user': 'User Demo'
}

# Scénarios de navigation pour chaque rôle
# Format: (route, description, actions[], nav_method)
# actions: liste de tuples (action_type, selector, value, description)
# nav_method: 'sidebar', 'bottombar', 'direct' ou None (default: direct)
SCENARIOS = {
    'admin': [
        ('/app/', 'Dashboard App', [
            ('screenshot', None, None, 'Dashboard principal'),
            ('scroll', None, 400, 'Scroll dashboard'),
            ('screenshot', None, None, 'Dashboard complet'),
        ], None),

        # Navigation vers Admin Dashboard
        ('/admin/', 'Dashboard Admin', [
            ('screenshot', None, None, 'Dashboard admin'),
            ('scroll', None, 500, 'Scroll stats'),
            ('screenshot', None, None, 'Stats admin'),
        ], 'sidebar'),

        # Gestion Utilisateurs
        ('/admin/users', 'Gestion Utilisateurs', [
            ('screenshot', None, None, 'Liste utilisateurs'),
            ('fill', '#search-input', 'demo', 'Recherche demo'),
            ('wait', None, 0.5, None),
            ('screenshot', None, None, 'Recherche demo'),
            ('clear', '#search-input', None, None),
            ('select', '#filter-role', 'admin', 'Filtrer admin'),
            ('wait', None, 0.5, None),
            ('screenshot', None, None, 'Admins filtrés'),
            ('select', '#filter-role', '', 'Reset filtre'),
            ('click', 'button[title="Voir détails"]:first-child', None, 'Voir détails'),
            ('wait', None, 1, None),
            ('screenshot', None, None, 'Modal utilisateur'),
            ('click', '.wise-modal-close, button[onclick*="close"], .modal-close', None, 'Fermer'),
        ], 'sidebar'),

        # Wallets
        ('/app/wallets', 'Gestion Wallets', [
            ('screenshot', None, None, 'Wallets'),
            ('click', '.wise-wallet-card:first-child', None, 'Ouvrir wallet'),
            ('wait', None, 1, None),
            ('screenshot', None, None, 'Modal wallet'),
            ('click', '.wise-modal-tab[data-tab="history"]', None, 'Historique'),
            ('wait', None, 0.5, None),
            ('screenshot', None, None, 'Historique wallet'),
            ('click', '.wise-modal-close', None, 'Fermer'),
            ('wait', None, 0.5, None),
            ('click', 'button:has-text("Add Currency")', None, 'Ajouter devise'),
            ('wait', None, 1, None),
            ('screenshot', None, None, 'Modal devise'),
            ('click', '.wise-modal-close, button[onclick*="close"]', None, 'Fermer'),
        ], 'sidebar'),

        # Convertisseur
        ('/app/converter', 'Convertisseur', [
            ('screenshot', None, None, 'Convertisseur'),
            ('fill', '#smart-amount', '1000', 'Montant 1000'),
            ('wait', None, 0.5, None),
            ('fill', '#smart-amount', '10000', 'Montant 10000'),
            ('wait', None, 0.5, None),
            ('screenshot', None, None, 'Conversion 10K'),
            ('select', '#from-currency', 'EUR', 'EUR'),
            ('wait', None, 0.5, None),
            ('screenshot', None, None, 'EUR vers MAD'),
            ('select', '#from-currency', 'USD', 'USD'),
            ('select', '#to-currency', 'EUR', 'Vers EUR'),
            ('wait', None, 0.5, None),
            ('screenshot', None, None, 'USD vers EUR'),
            ('select', '#to-currency', 'MAD', 'MAD'),
            ('click', '.wise-tab[data-tab="pairs"]', None, 'Paires'),
            ('wait', None, 0.5, None),
            ('screenshot', None, None, 'Paires populaires'),
            ('click', 'button:has-text("Refresh")', None, 'Rafraîchir'),
            ('wait', None, 1, None),
        ], 'bottombar'),

        # ATMs
        ('/app/atms', 'ATMs', [
            ('screenshot', None, None, 'Carte ATMs'),
            ('scroll', None, 500, 'Scroll'),
            ('screenshot', None, None, 'Liste ATMs'),
        ], 'bottombar'),

        # Transactions
        ('/app/transactions', 'Transactions', [
            ('screenshot', None, None, 'Transactions'),
            ('scroll', None, 400, 'Scroll'),
            ('screenshot', None, None, 'Plus transactions'),
        ], 'sidebar'),

        # Banques
        ('/admin/banks', 'Gestion Banques', [
            ('screenshot', None, None, 'Liste banques'),
            ('fill', '#search-input', 'attijari', 'Recherche AWB'),
            ('wait', None, 0.5, None),
            ('screenshot', None, None, 'Résultat AWB'),
            ('clear', '#search-input', None, None),
            ('click', 'a:has-text("Ajouter")', None, 'Ajouter banque'),
            ('wait', None, 1, None),
            ('screenshot', None, None, 'Formulaire banque'),
            ('fill', 'input[name="name"]', 'Test Bank', 'Nom'),
            ('fill', 'input[name="code"]', 'TEST', 'Code'),
            ('screenshot', None, None, 'Formulaire rempli'),
            ('click', 'a:has-text("Retour")', None, 'Retour'),
        ], 'sidebar'),

        # Bénéficiaires
        ('/app/beneficiaries', 'Bénéficiaires', [
            ('screenshot', None, None, 'Bénéficiaires'),
            ('click', 'button:has-text("Ajouter")', None, 'Ajouter'),
            ('wait', None, 1, None),
            ('screenshot', None, None, 'Modal ajout'),
            ('click', '.wise-modal-close, button[onclick*="close"], .modal-close', None, 'Fermer'),
        ], 'sidebar'),

        # IA
        ('/app/ai', 'IA Prédictions', [
            ('screenshot', None, None, 'Prédictions IA'),
            ('scroll', None, 400, 'Scroll'),
            ('screenshot', None, None, 'Analyses IA'),
        ], 'sidebar'),

        # Rate History
        ('/app/rate-history', 'Historique Taux', [
            ('screenshot', None, None, 'Historique'),
            ('scroll', None, 400, 'Scroll'),
            ('screenshot', None, None, 'Graphique'),
        ], 'sidebar'),

        # FAQ
        ('/app/faq', 'FAQ', [
            ('screenshot', None, None, 'FAQ'),
            ('scroll', None, 600, 'Parcourir'),
            ('screenshot', None, None, 'FAQ complète'),
        ], 'sidebar'),

        # Profil
        ('/app/profile', 'Profil', [
            ('screenshot', None, None, 'Profil'),
            ('scroll', None, 300, 'Scroll'),
            ('screenshot', None, None, 'Profil complet'),
        ], 'sidebar'),

        # Paramètres
        ('/app/settings', 'Paramètres', [
            ('screenshot', None, None, 'Paramètres'),
            ('click', 'button:has-text("Mode sombre"), button:has-text("Mode clair")', None, 'Toggle thème'),
            ('wait', None, 0.5, None),
            ('screenshot', None, None, 'Thème changé'),
            ('click', 'button:has-text("Mode sombre"), button:has-text("Mode clair")', None, 'Retour'),
        ], 'sidebar'),
    ],
    'bank': [
        # Dashboard
        ('/app/', 'Dashboard Banque', [
            ('screenshot', None, None, 'Dashboard banque'),
            ('scroll', None, 400, 'Scroll'),
            ('screenshot', None, None, 'Dashboard complet'),
        ], None),

        # Config API Banque
        ('/app/bank-settings', 'Configuration API', [
            ('screenshot', None, None, 'Config API'),
            ('fill', '#api_key', 'sk_live_test_123456789', 'Clé API'),
            ('fill', '#api_secret', 'sk_secret_987654321', 'Secret'),
            ('screenshot', None, None, 'Credentials'),
            ('fill', '#webhook_url', 'https://sarfx.io/webhooks/awb', 'Webhook'),
            ('fill', '#withdrawal_limit', '10000', 'Limite'),
            ('screenshot', None, None, 'Config complète'),
            ('click', 'button:has-text("Tester"), .btn-secondary:has-text("Test")', None, 'Tester'),
            ('wait', None, 1, None),
            ('screenshot', None, None, 'Test connexion'),
        ], 'sidebar'),

        # Wallets
        ('/app/wallets', 'Portefeuilles', [
            ('screenshot', None, None, 'Wallets'),
            ('click', '.wise-wallet-card:first-child', None, 'Ouvrir wallet'),
            ('wait', None, 1, None),
            ('screenshot', None, None, 'Détails wallet'),
            ('click', '.wise-modal-close, button[aria-label="Close"]', None, 'Fermer'),
        ], 'sidebar'),

        # Convertisseur gros montants
        ('/app/converter', 'Convertisseur', [
            ('screenshot', None, None, 'Convertisseur'),
            ('fill', '#smart-amount', '100000', 'Montant 100K'),
            ('wait', None, 0.5, None),
            ('screenshot', None, None, 'Conversion 100K'),
            ('fill', '#smart-amount', '500000', 'Montant 500K'),
            ('wait', None, 0.5, None),
            ('select', '#from-currency', 'EUR', 'EUR'),
            ('wait', None, 0.5, None),
            ('screenshot', None, None, 'EUR 500K'),
            ('select', '#from-currency', 'USD', 'USD'),
            ('click', 'button:has-text("Refresh"), .wise-refresh-btn', None, 'Rafraîchir'),
            ('wait', None, 1, None),
        ], 'bottombar'),

        # ATMs
        ('/app/atms', 'Réseau ATMs', [
            ('screenshot', None, None, 'Carte ATMs'),
            ('fill', '#atmSearch', 'Casablanca', 'Recherche'),
            ('wait', None, 0.5, None),
            ('screenshot', None, None, 'ATMs Casa'),
            ('clear', '#atmSearch', None, None),
            ('scroll', None, 400, 'Scroll'),
            ('screenshot', None, None, 'Liste ATMs'),
        ], 'bottombar'),

        # Transactions
        ('/app/transactions', 'Transactions', [
            ('screenshot', None, None, 'Transactions'),
            ('click', 'button[data-filter="completed"], button:has-text("Complétées")', None, 'Complétées'),
            ('wait', None, 0.5, None),
            ('screenshot', None, None, 'TX complétées'),
            ('click', 'button[data-filter="all"], button:has-text("Toutes")', None, 'Toutes'),
            ('scroll', None, 400, 'Scroll'),
            ('screenshot', None, None, 'Historique'),
        ], 'sidebar'),

        # IA
        ('/app/ai', 'Prévisions IA', [
            ('screenshot', None, None, 'IA'),
            ('fill', '#convert-amount', '100000', '100K'),
            ('wait', None, 0.5, None),
            ('screenshot', None, None, 'Conversion IA'),
            ('scroll', None, 400, 'Scroll'),
            ('screenshot', None, None, 'Analyses'),
        ], 'sidebar'),

        # Historique taux
        ('/app/rate-history', 'Historique Taux', [
            ('screenshot', None, None, 'Historique'),
            ('scroll', None, 400, 'Scroll'),
            ('screenshot', None, None, 'Graphique'),
        ], 'sidebar'),

        # Profil
        ('/app/profile', 'Profil', [
            ('screenshot', None, None, 'Profil'),
            ('scroll', None, 300, 'Scroll'),
            ('screenshot', None, None, 'Profil complet'),
        ], 'sidebar'),

        # Paramètres
        ('/app/settings', 'Paramètres', [
            ('screenshot', None, None, 'Paramètres'),
            ('click', 'button:has-text("Mode sombre"), button:has-text("Mode clair"), .wise-theme-toggle', None, 'Thème'),
            ('wait', None, 0.5, None),
            ('screenshot', None, None, 'Thème changé'),
        ], 'sidebar'),
    ],
    'user': [
        # Dashboard
        ('/app/', 'Mon Dashboard', [
            ('screenshot', None, None, 'Dashboard'),
            ('fill', '#home-amount', '1000', 'Calcul rapide'),
            ('wait', None, 0.5, None),
            ('screenshot', None, None, 'Calcul'),
            ('scroll', None, 400, 'Scroll'),
            ('screenshot', None, None, 'Providers'),
        ], None),

        # Wallets
        ('/app/wallets', 'Mes Wallets', [
            ('screenshot', None, None, 'Wallets'),
            ('click', '.wise-wallet-card:first-child', None, 'Ouvrir'),
            ('wait', None, 1, None),
            ('screenshot', None, None, 'Détails'),
            ('click', '.wise-modal-close, button[aria-label="Close"]', None, 'Fermer'),
        ], 'bottombar'),

        # Convertisseur
        ('/app/converter', 'Convertisseur', [
            ('screenshot', None, None, 'Convertisseur'),
            ('fill', '#smart-amount', '1000', '1000'),
            ('wait', None, 0.5, None),
            ('fill', '#smart-amount', '5000', '5000'),
            ('wait', None, 0.5, None),
            ('screenshot', None, None, 'Conversion'),
            ('select', '#from-currency', 'EUR', 'EUR'),
            ('wait', None, 0.5, None),
            ('screenshot', None, None, 'EUR'),
            ('select', '#from-currency', 'USD', 'USD'),
            ('click', 'button[data-tab="pairs"], .wise-tab[data-tab="pairs"]', None, 'Paires'),
            ('wait', None, 0.5, None),
            ('screenshot', None, None, 'Paires'),
        ], 'bottombar'),

        # ATMs
        ('/app/atms', 'Trouver ATM', [
            ('screenshot', None, None, 'Carte'),
            ('fill', '#atmSearch', 'Casa', 'Recherche'),
            ('wait', None, 0.5, None),
            ('screenshot', None, None, 'ATMs Casa'),
            ('scroll', None, 400, 'Scroll'),
            ('screenshot', None, None, 'Liste'),
        ], 'bottombar'),

        # Bénéficiaires
        ('/app/beneficiaries', 'Bénéficiaires', [
            ('screenshot', None, None, 'Bénéficiaires'),
            ('click', 'button:has-text("Ajouter"), .btn-primary:has-text("Ajouter")', None, 'Ajouter'),
            ('wait', None, 1, None),
            ('screenshot', None, None, 'Modal'),
            ('fill', 'input[name="name"], #beneficiary-name', 'Mohammed Alami', 'Nom'),
            ('fill', 'input[name="account_number"], #account-number', '007780123456789', 'RIB'),
            ('screenshot', None, None, 'Formulaire'),
            ('click', '.wise-modal-close, button:has-text("Annuler"), .modal-close', None, 'Fermer'),
        ], 'sidebar'),

        # Transactions
        ('/app/transactions', 'Historique', [
            ('screenshot', None, None, 'Transactions'),
            ('scroll', None, 400, 'Scroll'),
            ('screenshot', None, None, 'Plus TX'),
        ], 'sidebar'),

        # IA
        ('/app/ai', 'Prédictions IA', [
            ('screenshot', None, None, 'IA'),
            ('scroll', None, 400, 'Scroll'),
            ('screenshot', None, None, 'Analyses'),
        ], 'sidebar'),

        # Historique taux
        ('/app/rate-history', 'Historique Taux', [
            ('screenshot', None, None, 'Historique'),
            ('scroll', None, 400, 'Scroll'),
            ('screenshot', None, None, 'Graphique'),
        ], 'sidebar'),

        # FAQ
        ('/app/faq', 'FAQ', [
            ('screenshot', None, None, 'FAQ'),
            ('fill', '#faqSearch', 'retrait', 'Recherche'),
            ('wait', None, 0.5, None),
            ('screenshot', None, None, 'Résultats'),
            ('clear', '#faqSearch', None, None),
            ('click', '.wise-faq-question:first-child, .faq-item:first-child', None, 'Question'),
            ('wait', None, 0.5, None),
            ('screenshot', None, None, 'Réponse'),
        ], 'sidebar'),

        # Profil
        ('/app/profile', 'Mon Profil', [
            ('screenshot', None, None, 'Profil'),
            ('scroll', None, 300, 'Scroll'),
            ('screenshot', None, None, 'Profil complet'),
        ], 'sidebar'),

        # Paramètres
        ('/app/settings', 'Paramètres', [
            ('screenshot', None, None, 'Paramètres'),
            ('click', 'button:has-text("Mode sombre"), button:has-text("Mode clair"), .wise-theme-toggle', None, 'Thème'),
            ('wait', None, 0.5, None),
            ('screenshot', None, None, 'Thème changé'),
        ], 'sidebar'),
    ]
}


def run_demo(role: str, headless: bool = False):
    """Exécute la démo pour un rôle donné"""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("❌ Playwright non installé. Exécutez:")
        print("   pip install playwright")
        print("   playwright install chromium")
        return

    button_text = QUICK_LOGIN_BUTTONS.get(role)
    scenario = SCENARIOS.get(role)

    if not button_text or not scenario:
        print(f"❌ Rôle invalide: {role}")
        return

    print(f"🎬 Démarrage de la démo {role.upper()}...")
    print(f"   Mode: {'headless' if headless else 'visible'}")
    print(f"   URL: {BASE_URL}")
    print(f"   Bouton: {button_text}")
    print()

    # Dossier de sortie
    output_dir = os.path.join(os.getcwd(), 'sarfx_demo_output')
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    video_path = os.path.join(output_dir, f'demo_{role}_{timestamp}')

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            slow_mo=150  # Vitesse optimisée
        )

        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            record_video_dir=video_path,
            record_video_size={'width': 1920, 'height': 1080}
        )

        page = context.new_page()

        try:
            # Aller sur la page de login
            print(f"🔐 Navigation vers la page de connexion...")
            page.goto(f"{BASE_URL}/auth/login")
            time.sleep(2)

            # Cliquer sur le bouton Quick Login
            print(f"🖱️ Clic sur le bouton '{button_text}'...")
            page.click(f'button:has-text("{button_text}")')

            # Attendre que le login soit complété et la redirection terminée
            print("⏳ Attente de la connexion...")
            time.sleep(4)

            # Vérifier qu'on est bien connecté (URL contient /app ou /admin)
            try:
                page.wait_for_url("**/app/**", timeout=10000)
            except:
                page.wait_for_url("**/admin/**", timeout=5000)
            print("✅ Connecté!")
            print()

            # Screenshot de la page d'accueil après login
            screenshot_path = os.path.join(output_dir, f'{role}_dashboard.png')
            page.screenshot(path=screenshot_path)
            time.sleep(1)

            # Parcourir le scénario (skip le premier /app/ car déjà dessus)
            for path, description, actions, nav_method in scenario:
                if path == '/app/' or path == '/admin/':
                    # Déjà sur le dashboard après login, juste exécuter les actions
                    print(f"📍 {description} (page actuelle)")
                    for action in actions:
                        action_type, selector, value, action_desc = action
                        try:
                            if action_type == 'screenshot':
                                if action_desc:
                                    print(f"   📸 {action_desc}")
                                action_screenshot = os.path.join(output_dir, f'{role}_dashboard_{action_desc.replace(" ", "_")}.png')
                                page.screenshot(path=action_screenshot)
                            elif action_type == 'scroll':
                                if action_desc:
                                    print(f"   📜 {action_desc}")
                                page.evaluate(f'window.scrollBy(0, {value})')
                            elif action_type == 'wait':
                                time.sleep(value)
                            time.sleep(0.5)
                        except Exception as e:
                            print(f"   ⚠️ Action ignorée: {e}")
                    continue

                print(f"📍 {description}...")

                # Navigation selon la méthode spécifiée
                if nav_method == 'sidebar':
                    # Navigation via sidebar (menu latéral)
                    print(f"   🧭 Navigation via sidebar...")
                    try:
                        sidebar_selector = f'a.wise-nav-item[href="{path}"], .wise-nav-item a[href="{path}"], nav a[href="{path}"], .sidebar a[href="{path}"]'
                        page.click(sidebar_selector, timeout=3000)
                    except:
                        # Fallback: essayer avec le texte du lien
                        try:
                            page.click(f'a[href="{path}"]', timeout=3000)
                        except:
                            # Dernier recours: goto direct
                            print(f"   ⚠️ Sidebar non trouvé, navigation directe...")
                            page.goto(f"{BASE_URL}{path}")

                elif nav_method == 'bottombar':
                    # Navigation via bottom bar (menu du bas)
                    print(f"   🧭 Navigation via bottom bar...")
                    try:
                        bottombar_selector = f'.wise-bottom-item[href="{path}"], .bottom-nav a[href="{path}"], .bottombar a[href="{path}"]'
                        page.click(bottombar_selector, timeout=3000)
                    except:
                        try:
                            page.click(f'a[href="{path}"]', timeout=3000)
                        except:
                            print(f"   ⚠️ Bottom bar non trouvé, navigation directe...")
                            page.goto(f"{BASE_URL}{path}")

                else:
                    # Navigation directe via URL
                    page.goto(f"{BASE_URL}{path}")

                time.sleep(1.5)

                # Scroll en haut de la page pour une vue propre
                page.evaluate('window.scrollTo(0, 0)')
                time.sleep(0.3)

                # Exécuter les actions définies pour cette page
                for action in actions:
                    action_type, selector, value, action_desc = action

                    try:
                        if action_type == 'click':
                            if action_desc:
                                print(f"   🖱️ {action_desc}")
                            page.click(selector, timeout=5000)

                        elif action_type == 'fill':
                            if action_desc:
                                print(f"   ✏️ {action_desc}")
                            page.fill(selector, str(value))

                        elif action_type == 'clear':
                            page.fill(selector, '')

                        elif action_type == 'select':
                            if action_desc:
                                print(f"   📋 {action_desc}")
                            page.select_option(selector, value)

                        elif action_type == 'wait':
                            time.sleep(value)

                        elif action_type == 'scroll':
                            if action_desc:
                                print(f"   📜 {action_desc}")
                            page.evaluate(f'window.scrollBy(0, {value})')

                        elif action_type == 'screenshot':
                            if action_desc:
                                print(f"   📸 {action_desc}")
                            action_screenshot = os.path.join(output_dir, f'{role}_{path.replace("/", "_")}_{action_desc.replace(" ", "_")}.png')
                            page.screenshot(path=action_screenshot)

                        elif action_type == 'hover':
                            page.hover(selector)

                        time.sleep(0.3)  # Pause réduite entre actions

                    except Exception as e:
                        print(f"   ⚠️ Action ignorée: {e}")

            print()
            print("✅ Démo terminée!")

        finally:
            context.close()
            browser.close()

    # Trouver la vidéo générée
    for f in os.listdir(video_path):
        if f.endswith('.webm'):
            final_video = os.path.join(output_dir, f'demo_{role}_{timestamp}.webm')
            os.rename(os.path.join(video_path, f), final_video)
            print(f"🎥 Vidéo: {final_video}")
            break

    print(f"📁 Screenshots: {output_dir}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='SarfX Demo Robot')
    parser.add_argument('--role', choices=['admin', 'bank', 'user'], required=True,
                        help='Rôle à démontrer')
    parser.add_argument('--visible', action='store_true',
                        help='Mode visible (ouvre le navigateur)')
    parser.add_argument('--headless', action='store_true',
                        help='Mode headless (invisible)')

    args = parser.parse_args()

    headless = args.headless or not args.visible
    run_demo(args.role, headless=headless)
