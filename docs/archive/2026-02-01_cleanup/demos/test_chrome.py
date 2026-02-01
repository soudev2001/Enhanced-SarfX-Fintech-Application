#!/usr/bin/env python3
"""Script de diagnostic Chrome/Selenium pour Windows"""

import sys
import subprocess
from pathlib import Path

def check_chrome():
    """Vérifie l'installation de Chrome"""
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]

    print("🔍 Recherche de Chrome...")
    for path in chrome_paths:
        if Path(path).exists():
            print(f"✅ Chrome trouvé: {path}")
            try:
                result = subprocess.run([path, "--version"], capture_output=True, text=True)
                print(f"   Version: {result.stdout.strip()}")
            except Exception as e:
                print(f"   ⚠️  Erreur lors de la vérification: {e}")
            return path

    print("❌ Chrome non trouvé dans les emplacements standards")
    return None

def check_selenium():
    """Vérifie Selenium et SeleniumLibrary"""
    print("\n🔍 Vérification de Selenium...")
    try:
        import selenium
        print(f"✅ Selenium installé: version {selenium.__version__}")

        from selenium import webdriver
        print("✅ selenium.webdriver importé")

        # Test du Selenium Manager
        try:
            from selenium.webdriver.common.selenium_manager import SeleniumManager
            print("✅ Selenium Manager disponible (gestion auto de ChromeDriver)")
        except ImportError:
            print("⚠️  Selenium Manager non disponible (version ancienne)")

    except ImportError as e:
        print(f"❌ Selenium non installé: {e}")
        return False

    return True

def check_robot_framework():
    """Vérifie Robot Framework"""
    print("\n🔍 Vérification de Robot Framework...")
    try:
        import robot
        print(f"✅ Robot Framework installé: version {robot.__version__}")

        from SeleniumLibrary import SeleniumLibrary
        print(f"✅ SeleniumLibrary installé")

    except ImportError as e:
        print(f"❌ Robot Framework ou SeleniumLibrary manquant: {e}")
        return False

    return True

def test_chrome_driver():
    """Test de création d'un WebDriver Chrome"""
    print("\n🧪 Test de création du WebDriver Chrome...")
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options

        options = Options()
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')

        print("   Création du driver (Selenium Manager téléchargera ChromeDriver si nécessaire)...")
        driver = webdriver.Chrome(options=options)

        print("✅ WebDriver créé avec succès!")
        print(f"   Session ID: {driver.session_id}")

        driver.quit()
        print("✅ Driver fermé proprement")
        return True

    except Exception as e:
        print(f"❌ Erreur lors de la création du WebDriver:")
        print(f"   {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Exécute tous les diagnostics"""
    print("=" * 60)
    print("🔧 DIAGNOSTIC CHROME/SELENIUM POUR SARFX")
    print("=" * 60)

    chrome_ok = check_chrome() is not None
    selenium_ok = check_selenium()
    robot_ok = check_robot_framework()

    if chrome_ok and selenium_ok:
        driver_ok = test_chrome_driver()
    else:
        driver_ok = False

    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ")
    print("=" * 60)
    print(f"Chrome:           {'✅ OK' if chrome_ok else '❌ MANQUANT'}")
    print(f"Selenium:         {'✅ OK' if selenium_ok else '❌ MANQUANT'}")
    print(f"Robot Framework:  {'✅ OK' if robot_ok else '❌ MANQUANT'}")
    print(f"WebDriver Test:   {'✅ OK' if driver_ok else '❌ ÉCHEC'}")

    if chrome_ok and selenium_ok and robot_ok and driver_ok:
        print("\n✅ Tous les tests sont passés! Vous pouvez lancer les tests Robot Framework.")
        return 0
    else:
        print("\n⚠️  Des problèmes ont été détectés. Voir les détails ci-dessus.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
