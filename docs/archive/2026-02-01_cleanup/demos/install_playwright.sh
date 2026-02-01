#!/bin/bash
# Script d'installation de Playwright pour les démos SarfX

echo "🎭 Installation de Playwright pour SarfX..."

# Installer playwright via pip
pip install playwright

# Installer les navigateurs
echo "📦 Installation des navigateurs Chromium..."
playwright install chromium

# Installer les dépendances système (si nécessaire)
echo "🔧 Installation des dépendances système..."
playwright install-deps chromium 2>/dev/null || true

# Créer les dossiers de sortie
mkdir -p robot_results/playwright/videos
mkdir -p robot_results/playwright/screenshots
mkdir -p robot_results/playwright/logs

echo "✅ Installation terminée!"
echo ""
echo "Pour tester l'installation:"
echo "  python -c 'from playwright.sync_api import sync_playwright; p = sync_playwright().start(); b = p.chromium.launch(); b.close(); p.stop(); print(\"OK!\")'"
echo ""
echo "Pour lancer une démo manuellement:"
echo "  python -m playwright_demos.demo_admin --headless"
echo "  python -m playwright_demos.demo_bank --headless"
echo "  python -m playwright_demos.demo_user --headless"
