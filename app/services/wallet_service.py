"""
Service de gestion des portefeuilles
"""
from app.services.db_service import get_db
from datetime import datetime
import uuid


def create_wallet(user_id):
    """Crée un nouveau portefeuille pour un utilisateur"""
    db = get_db()
    if db is None:
        return None
    
    # Vérifier si le wallet existe déjà
    existing = db.wallets.find_one({"user_id": str(user_id)})
    if existing:
        return existing
    
    wallet = {
        "wallet_id": str(uuid.uuid4()),
        "user_id": str(user_id),
        "balances": {
            "USD": 0.0,
            "EUR": 0.0,
            "MAD": 0.0,
            "GBP": 0.0
        },
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    db.wallets.insert_one(wallet)
    return wallet


def get_wallet(user_id):
    """Récupère le portefeuille d'un utilisateur"""
    db = get_db()
    if db is None:
        return None
    return db.wallets.find_one({"user_id": str(user_id)})


def get_wallet_by_id(wallet_id):
    """Récupère un portefeuille par son ID"""
    db = get_db()
    if db is None:
        return None
    return db.wallets.find_one({"wallet_id": wallet_id})


def update_balance(user_id, currency, amount, operation='add'):
    """
    Met à jour le solde d'un portefeuille
    
    Args:
        user_id: ID de l'utilisateur
        currency: Devise (USD, EUR, MAD, etc.)
        amount: Montant à ajouter/retirer
        operation: 'add' ou 'subtract'
    """
    db = get_db()
    if db is None:
        return False
    
    wallet = db.wallets.find_one({"user_id": str(user_id)})
    if not wallet:
        return False
    
    current_balance = wallet.get('balances', {}).get(currency, 0.0)
    
    if operation == 'add':
        new_balance = current_balance + amount
    elif operation == 'subtract':
        new_balance = current_balance - amount
        if new_balance < 0:
            return False  # Solde insuffisant
    else:
        new_balance = amount  # Set direct
    
    db.wallets.update_one(
        {"user_id": str(user_id)},
        {
            "$set": {
                f"balances.{currency}": new_balance,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    return True


def get_all_wallets(limit=100, skip=0):
    """Récupère tous les portefeuilles (admin)"""
    db = get_db()
    if db is None:
        return []
    return list(db.wallets.find().skip(skip).limit(limit))


def adjust_wallet(wallet_id, currency, new_balance, admin_id, reason=""):
    """
    Ajuste manuellement le solde d'un portefeuille (admin)
    
    Args:
        wallet_id: ID du portefeuille
        currency: Devise
        new_balance: Nouveau solde
        admin_id: ID de l'admin effectuant l'ajustement
        reason: Raison de l'ajustement
    """
    db = get_db()
    if db is None:
        return False
    
    wallet = db.wallets.find_one({"wallet_id": wallet_id})
    if not wallet:
        return False
    
    old_balance = wallet.get('balances', {}).get(currency, 0.0)
    
    # Enregistrer l'ajustement
    adjustment = {
        "adjustment_id": str(uuid.uuid4()),
        "wallet_id": wallet_id,
        "user_id": wallet['user_id'],
        "currency": currency,
        "old_balance": old_balance,
        "new_balance": new_balance,
        "difference": new_balance - old_balance,
        "admin_id": admin_id,
        "reason": reason,
        "created_at": datetime.utcnow()
    }
    db.wallet_adjustments.insert_one(adjustment)
    
    # Mettre à jour le solde
    db.wallets.update_one(
        {"wallet_id": wallet_id},
        {
            "$set": {
                f"balances.{currency}": new_balance,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    return True


def get_wallet_history(wallet_id, limit=50):
    """Récupère l'historique des ajustements d'un portefeuille"""
    db = get_db()
    if db is None:
        return []
    return list(db.wallet_adjustments.find({"wallet_id": wallet_id}).sort("created_at", -1).limit(limit))
