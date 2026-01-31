#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test pour le Backend IA SarfX
Vérifie tous les endpoints et fonctionnalités
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8087"

def print_header(title):
    """Affiche un header formaté"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_health_check():
    """Test du health check"""
    print_header("Test 1: Health Check")
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ Health check réussi")
            print(f"   Version: {data.get('version')}")
            print(f"   Database: {data.get('database')}")
            print(f"   Cache entries: {data.get('cache', {}).get('entries', 0)}")
            print(f"   ML models: {', '.join(data.get('features', {}).get('ml_models', []))}")
            return True
        else:
            print(f"❌ Erreur HTTP {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Impossible de se connecter au backend")
        print("   Assurez-vous que le backend est démarré: cd 'SarfX Backend' && python main.py")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_smart_rate():
    """Test du smart rate endpoint"""
    print_header("Test 2: Smart Rate (EUR → MAD)")
    try:
        response = requests.get(f"{BASE_URL}/smart-rate/EUR/MAD?amount=1000", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ Smart rate récupéré")
            print(f"   Paire: {data['meta']['pair']}")
            print(f"   Taux SarfX: {data['sarfx_offer']['rate']}")
            print(f"   Montant final: {data['sarfx_offer']['final_amount']:.2f} MAD")
            print(f"   Économies vs banque: {data['market_intelligence']['savings']:.2f} MAD")
            print(f"   Signal IA: {data['ai_advisor']['signal']}")
            return True
        else:
            print(f"❌ Erreur HTTP {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_predictions():
    """Test des prédictions ML"""
    print_header("Test 3: Prédictions ML (ARIMA + Prophet)")
    try:
        response = requests.get(f"{BASE_URL}/predict/EURMAD", timeout=30)
        if response.status_code == 200:
            data = response.json()
            print("✅ Prédictions générées")
            print(f"   Taux actuel: {data['meta']['current_rate']:.4f}")
            print(f"   Jours de prédiction: {data['meta']['prediction_days']}")
            print(f"   Modèles utilisés: {', '.join(data['meta']['models_used'])}")
            print(f"   Confiance: {data['confidence']}")

            # Afficher les 3 premières prédictions
            print("\n   Prédictions (3 premiers jours):")
            for i in range(min(3, len(data['predictions']['dates']))):
                date = data['predictions']['dates'][i]
                arima = data['predictions']['ARIMA'][i]
                prophet = data['predictions']['Prophet'][i]
                ensemble = data['predictions']['Ensemble_Mean'][i]
                print(f"     {date}: ARIMA={arima:.4f}, Prophet={prophet:.4f}, Ensemble={ensemble:.4f}")

            return True
        else:
            print(f"❌ Erreur HTTP {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_cache_stats():
    """Test des stats du cache"""
    print_header("Test 4: Statistiques Cache")
    try:
        response = requests.get(f"{BASE_URL}/cache/stats", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ Statistiques cache récupérées")
            print(f"   Total entrées: {data['total_entries']}")
            print(f"   TTL: {data['ttl_seconds']} secondes")

            if data['entries']:
                print("\n   Détails cache:")
                for entry in data['entries'][:3]:  # Afficher 3 premières entrées
                    print(f"     • {entry['key']}: {entry['rate']:.4f} (expire dans {entry['expires_in']:.0f}s)")
            else:
                print("   Cache vide (aucune requête précédente)")

            return True
        else:
            print(f"❌ Erreur HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_cache_clear():
    """Test du vidage du cache"""
    print_header("Test 5: Vidage Cache")
    try:
        response = requests.post(f"{BASE_URL}/cache/clear", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ Cache vidé avec succès")
            print(f"   Message: {data['message']}")
            return True
        else:
            print(f"❌ Erreur HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def main():
    """Fonction principale"""
    print("\n" + "🚀 "*30)
    print("   Test Suite - Backend IA SarfX v2.0")
    print("🚀 "*30)

    results = []

    # Test 1: Health Check
    results.append(("Health Check", test_health_check()))

    # Test 2: Smart Rate
    results.append(("Smart Rate", test_smart_rate()))

    # Test 3: Prédictions
    results.append(("Prédictions ML", test_predictions()))

    # Test 4: Cache Stats
    results.append(("Stats Cache", test_cache_stats()))

    # Test 5: Clear Cache
    results.append(("Vidage Cache", test_cache_clear()))

    # Résumé
    print_header("Résumé des Tests")
    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")

    print(f"\n{'='*60}")
    print(f"  Score: {passed}/{total} tests réussis ({passed*100//total}%)")
    print(f"{'='*60}\n")

    if passed == total:
        print("🎉 Tous les tests sont passés ! Le backend IA fonctionne parfaitement.\n")
    else:
        print("⚠️  Certains tests ont échoué. Vérifiez les logs ci-dessus.\n")

if __name__ == "__main__":
    main()
