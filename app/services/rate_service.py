"""
Service de gestion des taux de change
"""
from app.services.db_service import get_db
from datetime import datetime
import random


def get_all_suppliers(active_only=True):
    """Récupère tous les fournisseurs"""
    db = get_db()
    if db is None:
        return []
    
    query = {"is_active": True} if active_only else {}
    suppliers = list(db.suppliers.find(query))
    
    # Convert ObjectId to string
    for s in suppliers:
        s['_id'] = str(s['_id'])
    
    return suppliers


def get_supplier_by_id(supplier_id):
    """Récupère un fournisseur par son ID"""
    db = get_db()
    if db is None:
        return None
    
    from bson import ObjectId
    try:
        supplier = db.suppliers.find_one({"_id": ObjectId(supplier_id)})
        if supplier:
            supplier['_id'] = str(supplier['_id'])
        return supplier
    except:
        return None


def calculate_best_rate(amount, from_currency='USD', to_currency='MAD'):
    """
    Calcule le meilleur taux parmi tous les fournisseurs
    
    Returns:
        dict avec le meilleur fournisseur et les détails
    """
    suppliers = get_all_suppliers(active_only=True)
    if not suppliers:
        return None
    
    results = []
    for supplier in suppliers:
        # Simuler une petite variation du taux (réaliste)
        base_rate = supplier.get('rate', 10.0)
        variation = random.uniform(-0.02, 0.02)
        current_rate = base_rate * (1 + variation)
        
        fee = supplier.get('fee', 0)
        
        # Calcul du montant final
        net_amount = amount - fee
        final_amount = net_amount * current_rate
        
        results.append({
            'supplier': supplier,
            'rate': current_rate,
            'fee': fee,
            'final_amount': final_amount
        })
    
    # Trier par montant final décroissant (meilleur deal)
    results.sort(key=lambda x: x['final_amount'], reverse=True)
    
    return {
        'best': results[0],
        'all': results
    }


def create_supplier(name, supplier_type, rate, fee=0, logo='', is_active=True):
    """Crée un nouveau fournisseur"""
    db = get_db()
    if db is None:
        return None
    
    supplier = {
        "name": name,
        "type": supplier_type,
        "rate": float(rate),
        "fee": float(fee),
        "logo": logo,
        "is_active": is_active,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = db.suppliers.insert_one(supplier)
    supplier['_id'] = str(result.inserted_id)
    
    return supplier


def update_supplier(supplier_id, **kwargs):
    """Met à jour un fournisseur"""
    db = get_db()
    if db is None:
        return False
    
    from bson import ObjectId
    
    update_data = {k: v for k, v in kwargs.items() if v is not None}
    update_data['updated_at'] = datetime.utcnow()
    
    try:
        result = db.suppliers.update_one(
            {"_id": ObjectId(supplier_id)},
            {"$set": update_data}
        )
        return result.modified_count > 0
    except:
        return False


def delete_supplier(supplier_id):
    """Supprime un fournisseur"""
    db = get_db()
    if db is None:
        return False
    
    from bson import ObjectId
    
    try:
        result = db.suppliers.delete_one({"_id": ObjectId(supplier_id)})
        return result.deleted_count > 0
    except:
        return False


def update_rate(supplier_id, new_rate):
    """
    Met à jour le taux d'un fournisseur et enregistre l'historique
    """
    db = get_db()
    if db is None:
        return False
    
    from bson import ObjectId
    
    try:
        supplier = db.suppliers.find_one({"_id": ObjectId(supplier_id)})
        if not supplier:
            return False
        
        old_rate = supplier.get('rate', 0)
        
        # Enregistrer l'historique
        rate_history = {
            "supplier_id": supplier_id,
            "old_rate": old_rate,
            "new_rate": float(new_rate),
            "change_pct": ((float(new_rate) - old_rate) / old_rate * 100) if old_rate else 0,
            "created_at": datetime.utcnow()
        }
        db.rate_history.insert_one(rate_history)
        
        # Mettre à jour le taux
        db.suppliers.update_one(
            {"_id": ObjectId(supplier_id)},
            {
                "$set": {
                    "rate": float(new_rate),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return True
    except:
        return False


def get_rate_history(supplier_id=None, limit=50):
    """Récupère l'historique des taux"""
    db = get_db()
    if db is None:
        return []
    
    query = {"supplier_id": supplier_id} if supplier_id else {}
    return list(db.rate_history.find(query).sort("created_at", -1).limit(limit))


def seed_default_suppliers():
    """Initialise les fournisseurs par défaut"""
    db = get_db()
    if db is None:
        return False
    
    # Vérifier si des fournisseurs existent déjà
    if db.suppliers.count_documents({}) > 0:
        return False
    
    default_suppliers = [
        {
            "name": "Binance P2P",
            "type": "crypto",
            "rate": 10.12,
            "fee": 0,
            "logo": "https://cryptologos.cc/logos/binance-coin-bnb-logo.png?v=026",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "name": "Banque Populaire",
            "type": "bank",
            "rate": 9.85,
            "fee": 20,
            "logo": "https://upload.wikimedia.org/wikipedia/fr/2/22/Logo_Banque_Populaire.png",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "name": "Western Union",
            "type": "transfer",
            "rate": 9.95,
            "fee": 15,
            "logo": "https://www.westernunion.com/content/dam/wu/jm/logos/wu_logo.svg",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "name": "MoneyGram",
            "type": "transfer",
            "rate": 9.90,
            "fee": 12,
            "logo": "https://www.moneygram.com/mgo/images/logo.svg",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "name": "Marché Parallèle",
            "type": "cash",
            "rate": 10.05,
            "fee": 0,
            "logo": "https://cdn-icons-png.flaticon.com/512/2489/2489756.png",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    ]
    
    db.suppliers.insert_many(default_suppliers)
    return True
