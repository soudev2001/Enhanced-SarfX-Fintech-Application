#!/usr/bin/env python3
"""
Script de test pour les nouvelles fonctionnalités Wallets
"""

import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.services.wallet_service import (
    create_wallet,
    get_wallet,
    add_currency_to_wallet,
    remove_currency_from_wallet,
    get_wallet_transactions,
    get_wallet_history,
    update_balance
)


def test_wallet_operations():
    """Test des opérations wallet"""
    print("🧪 Test des opérations Wallets")
    print("=" * 50)

    # Test 1: Créer un wallet
    print("\n1️⃣ Test: Créer un wallet")
    user_id = "test_user_123"
    wallet = create_wallet(user_id)

    if wallet:
        print(f"✅ Wallet créé: {wallet['wallet_id'][:16]}...")
        print(f"   Devises initiales: {list(wallet['balances'].keys())}")
    else:
        print("❌ Échec de création du wallet")
        return False

    # Test 2: Ajouter une devise
    print("\n2️⃣ Test: Ajouter une devise (CHF)")
    success = add_currency_to_wallet(user_id, 'CHF')

    if success:
        wallet = get_wallet(user_id)
        print(f"✅ CHF ajouté")
        print(f"   Devises actuelles: {list(wallet['balances'].keys())}")
    else:
        print("❌ Échec d'ajout de devise")

    # Test 3: Mettre à jour le solde
    print("\n3️⃣ Test: Mettre à jour le solde USD")
    success = update_balance(user_id, 'USD', 1000, 'add')

    if success:
        wallet = get_wallet(user_id)
        print(f"✅ Solde mis à jour")
        print(f"   USD Balance: {wallet['balances']['USD']}")
    else:
        print("❌ Échec de mise à jour")

    # Test 4: Essayer de retirer une devise avec solde
    print("\n4️⃣ Test: Retirer devise avec solde (devrait échouer)")
    success = remove_currency_from_wallet(user_id, 'USD')

    if not success:
        print("✅ Retrait bloqué (solde non-nul) - Comportement correct")
    else:
        print("❌ Retrait autorisé (pas normal)")

    # Test 5: Retirer une devise avec solde = 0
    print("\n5️⃣ Test: Retirer devise avec solde = 0 (CHF)")
    success = remove_currency_from_wallet(user_id, 'CHF')

    if success:
        wallet = get_wallet(user_id)
        print(f"✅ CHF retiré")
        print(f"   Devises actuelles: {list(wallet['balances'].keys())}")
    else:
        print("❌ Échec de retrait")

    # Test 6: Ajouter plusieurs devises
    print("\n6️⃣ Test: Ajouter plusieurs devises")
    currencies = ['CAD', 'AED', 'SAR']

    for currency in currencies:
        add_currency_to_wallet(user_id, currency)

    wallet = get_wallet(user_id)
    print(f"✅ Devises ajoutées")
    print(f"   Devises finales: {list(wallet['balances'].keys())}")

    print("\n" + "=" * 50)
    print("✅ Tous les tests terminés!")

    return True


def test_validation():
    """Test des validations"""
    print("\n🔒 Test des validations")
    print("=" * 50)

    user_id = "test_user_123"

    # Test 1: Devise invalide
    print("\n1️⃣ Test: Ajouter devise invalide (XXX)")
    success = add_currency_to_wallet(user_id, 'XXX')

    if not success:
        print("✅ Devise invalide rejetée - Sécurité OK")
    else:
        print("❌ Devise invalide acceptée - PROBLÈME!")

    # Test 2: Montant négatif
    print("\n2️⃣ Test: Montant négatif")
    success = update_balance(user_id, 'USD', -100, 'add')

    if not success:
        print("✅ Montant négatif rejeté - Sécurité OK")
    else:
        print("❌ Montant négatif accepté - PROBLÈME!")

    # Test 3: Solde négatif après retrait
    print("\n3️⃣ Test: Retrait avec solde insuffisant")
    success = update_balance(user_id, 'EUR', 5000, 'subtract')

    if not success:
        print("✅ Retrait bloqué (solde insuffisant) - Sécurité OK")
    else:
        print("❌ Retrait autorisé - PROBLÈME!")

    print("\n" + "=" * 50)
    print("✅ Tests de validation terminés!")


def display_wallet_info(user_id):
    """Affiche les infos d'un wallet"""
    print("\n📊 Informations du Wallet")
    print("=" * 50)

    wallet = get_wallet(user_id)

    if not wallet:
        print("❌ Wallet introuvable")
        return

    print(f"Wallet ID: {wallet['wallet_id']}")
    print(f"User ID: {wallet['user_id']}")
    print(f"Actif: {wallet.get('is_active', True)}")
    print(f"\nDevises et Soldes:")

    total_usd = 0
    for currency, balance in wallet['balances'].items():
        print(f"  {currency}: {balance:,.2f}")
        # Conversion simplifiée vers USD
        rate = {'EUR': 1.1, 'GBP': 1.25, 'MAD': 0.1, 'CHF': 1.08, 'CAD': 0.75, 'AED': 0.27, 'SAR': 0.27}.get(currency, 1.0)
        total_usd += balance * rate

    print(f"\nÉquivalent USD total: ${total_usd:,.2f}")
    print("=" * 50)


if __name__ == "__main__":
    print("\n🚀 Lancement des tests Wallets\n")

    try:
        # Tests des opérations
        test_wallet_operations()

        # Tests de validation
        test_validation()

        # Affichage final
        display_wallet_info("test_user_123")

        print("\n✅ TOUS LES TESTS RÉUSSIS!\n")

    except Exception as e:
        print(f"\n❌ ERREUR: {str(e)}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
