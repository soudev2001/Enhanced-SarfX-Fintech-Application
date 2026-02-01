#!/usr/bin/env python3
"""
Script pour créer les fournisseurs de change avec données réelles
Taux basés sur le marché marocain - Janvier 2025
"""

import os
from dotenv import load_dotenv
from pymongo import MongoClient
from datetime import datetime

# Charger les variables d'environnement
load_dotenv()

MONGO_URI = os.environ.get("MONGO_URI")
DB_NAME = os.environ.get("DB_NAME", "SarfX_Enhanced")

# Fournisseurs réels avec leurs taux et logos
SUPPLIERS_DATA = [
    # === Crypto/P2P Exchanges ===
    {
        "name": "Binance P2P",
        "type": "crypto",
        "category": "p2p",
        "rate": 10.12,
        "fee": 0,
        "fee_type": "percent",
        "logo": "https://cryptologos.cc/logos/binance-coin-bnb-logo.png",
        "description": "Plateforme d'échange P2P crypto - Meilleurs taux",
        "min_amount": 10,
        "max_amount": 100000,
        "processing_time": "instant",
        "is_active": True,
        "rating": 4.8,
        "supported_currencies": ["USD", "EUR", "GBP", "USDT"]
    },
    {
        "name": "Paxful",
        "type": "crypto",
        "category": "p2p",
        "rate": 10.08,
        "fee": 0,
        "fee_type": "percent",
        "logo": "https://cdn.worldvectorlogo.com/logos/paxful.svg",
        "description": "Marketplace P2P mondial avec multiples méthodes de paiement",
        "min_amount": 20,
        "max_amount": 50000,
        "processing_time": "instant",
        "is_active": True,
        "rating": 4.5,
        "supported_currencies": ["USD", "EUR", "GBP"]
    },
    {
        "name": "LocalBitcoins",
        "type": "crypto",
        "category": "p2p",
        "rate": 10.05,
        "fee": 1,
        "fee_type": "percent",
        "logo": "https://cdn.worldvectorlogo.com/logos/localbitcoins.svg",
        "description": "Le pionnier du P2P Bitcoin",
        "min_amount": 50,
        "max_amount": 50000,
        "processing_time": "1-30 min",
        "is_active": True,
        "rating": 4.2,
        "supported_currencies": ["USD", "EUR"]
    },
    {
        "name": "Bybit P2P",
        "type": "crypto",
        "category": "p2p",
        "rate": 10.10,
        "fee": 0,
        "fee_type": "percent",
        "logo": "https://cryptologos.cc/logos/thumbs/bybit.png",
        "description": "P2P rapide avec 0% de frais",
        "min_amount": 10,
        "max_amount": 80000,
        "processing_time": "instant",
        "is_active": True,
        "rating": 4.6,
        "supported_currencies": ["USD", "EUR", "USDT"]
    },
    
    # === Services de Transfert International ===
    {
        "name": "Western Union",
        "type": "transfer",
        "category": "remittance",
        "rate": 9.95,
        "fee": 15,
        "fee_type": "fixed",
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2c/Western_Union_Logo_2019.svg/1200px-Western_Union_Logo_2019.svg.png",
        "description": "Leader mondial du transfert d'argent",
        "min_amount": 50,
        "max_amount": 7500,
        "processing_time": "10 min - 1 jour",
        "is_active": True,
        "rating": 4.0,
        "supported_currencies": ["USD", "EUR", "GBP", "CAD"]
    },
    {
        "name": "MoneyGram",
        "type": "transfer",
        "category": "remittance",
        "rate": 9.92,
        "fee": 12,
        "fee_type": "fixed",
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/ea/MoneyGram_logo.svg/1200px-MoneyGram_logo.svg.png",
        "description": "Transferts rapides dans 200+ pays",
        "min_amount": 30,
        "max_amount": 10000,
        "processing_time": "10 min - 3 jours",
        "is_active": True,
        "rating": 3.9,
        "supported_currencies": ["USD", "EUR", "GBP"]
    },
    {
        "name": "Wise (TransferWise)",
        "type": "transfer",
        "category": "fintech",
        "rate": 10.02,
        "fee": 0.5,
        "fee_type": "percent",
        "logo": "https://wise.com/public-resources/assets/logos/wise/brand_logo.svg",
        "description": "Taux mid-market avec frais transparents",
        "min_amount": 1,
        "max_amount": 1000000,
        "processing_time": "1-2 jours",
        "is_active": True,
        "rating": 4.7,
        "supported_currencies": ["USD", "EUR", "GBP", "CHF", "CAD"]
    },
    {
        "name": "Remitly",
        "type": "transfer",
        "category": "fintech",
        "rate": 9.98,
        "fee": 3.99,
        "fee_type": "fixed",
        "logo": "https://upload.wikimedia.org/wikipedia/commons/5/56/Remitly_Logo.png",
        "description": "Express vers le Maroc avec app mobile",
        "min_amount": 25,
        "max_amount": 2999,
        "processing_time": "minutes - 3 jours",
        "is_active": True,
        "rating": 4.4,
        "supported_currencies": ["USD", "EUR", "GBP", "CAD"]
    },
    {
        "name": "WorldRemit",
        "type": "transfer",
        "category": "fintech",
        "rate": 9.96,
        "fee": 2.99,
        "fee_type": "fixed",
        "logo": "https://upload.wikimedia.org/wikipedia/commons/b/b4/WorldRemit_Logo.png",
        "description": "Transfert mobile et cash pickup",
        "min_amount": 10,
        "max_amount": 5000,
        "processing_time": "minutes - 2 jours",
        "is_active": True,
        "rating": 4.3,
        "supported_currencies": ["USD", "EUR", "GBP"]
    },
    {
        "name": "Xoom (PayPal)",
        "type": "transfer",
        "category": "fintech",
        "rate": 9.90,
        "fee": 4.99,
        "fee_type": "fixed",
        "logo": "https://upload.wikimedia.org/wikipedia/commons/5/50/Xoom_logo.svg",
        "description": "Service PayPal pour le Maroc",
        "min_amount": 10,
        "max_amount": 9999,
        "processing_time": "minutes - 5 jours",
        "is_active": True,
        "rating": 4.1,
        "supported_currencies": ["USD", "EUR"]
    },
    
    # === Banques Marocaines ===
    {
        "name": "Attijariwafa Bank",
        "type": "bank",
        "category": "bank",
        "rate": 9.85,
        "fee": 25,
        "fee_type": "fixed",
        "logo": "/static/images/banks/attijariwafa.png",
        "description": "1ère banque au Maroc et en Afrique",
        "min_amount": 100,
        "max_amount": 500000,
        "processing_time": "1-3 jours",
        "is_active": True,
        "rating": 4.2,
        "supported_currencies": ["USD", "EUR", "GBP", "CHF"]
    },
    {
        "name": "Banque Populaire",
        "type": "bank",
        "category": "bank",
        "rate": 9.82,
        "fee": 20,
        "fee_type": "fixed",
        "logo": "/static/images/banks/chaabi.png",
        "description": "Réseau étendu au Maroc",
        "min_amount": 100,
        "max_amount": 300000,
        "processing_time": "1-3 jours",
        "is_active": True,
        "rating": 4.0,
        "supported_currencies": ["USD", "EUR", "GBP"]
    },
    {
        "name": "BMCE Bank of Africa",
        "type": "bank",
        "category": "bank",
        "rate": 9.84,
        "fee": 22,
        "fee_type": "fixed",
        "logo": "/static/images/banks/boa.png",
        "description": "Présence panafricaine",
        "min_amount": 100,
        "max_amount": 400000,
        "processing_time": "1-3 jours",
        "is_active": True,
        "rating": 4.1,
        "supported_currencies": ["USD", "EUR", "GBP", "CAD"]
    },
    {
        "name": "CIH Bank",
        "type": "bank",
        "category": "bank",
        "rate": 9.80,
        "fee": 18,
        "fee_type": "fixed",
        "logo": "/static/images/banks/cih.png",
        "description": "Banque digitale moderne",
        "min_amount": 50,
        "max_amount": 200000,
        "processing_time": "1-2 jours",
        "is_active": True,
        "rating": 4.3,
        "supported_currencies": ["USD", "EUR"]
    },
    {
        "name": "BMCI (BNP Paribas)",
        "type": "bank",
        "category": "bank",
        "rate": 9.88,
        "fee": 30,
        "fee_type": "fixed",
        "logo": "/static/images/banks/bmci.png",
        "description": "Filiale BNP Paribas au Maroc",
        "min_amount": 200,
        "max_amount": 500000,
        "processing_time": "1-3 jours",
        "is_active": True,
        "rating": 4.0,
        "supported_currencies": ["USD", "EUR", "GBP", "CHF"]
    },
    
    # === Bureaux de change ===
    {
        "name": "Badr Exchange",
        "type": "exchange",
        "category": "bureau",
        "rate": 10.00,
        "fee": 0,
        "fee_type": "included",
        "logo": "https://cdn-icons-png.flaticon.com/512/2830/2830284.png",
        "description": "Bureau de change agréé - Casablanca",
        "min_amount": 50,
        "max_amount": 50000,
        "processing_time": "instant",
        "is_active": True,
        "rating": 4.5,
        "supported_currencies": ["USD", "EUR", "GBP", "CHF", "CAD"]
    },
    {
        "name": "Afriquia Change",
        "type": "exchange",
        "category": "bureau",
        "rate": 9.98,
        "fee": 0,
        "fee_type": "included",
        "logo": "https://cdn-icons-png.flaticon.com/512/2830/2830284.png",
        "description": "Réseau national de bureaux de change",
        "min_amount": 20,
        "max_amount": 30000,
        "processing_time": "instant",
        "is_active": True,
        "rating": 4.3,
        "supported_currencies": ["USD", "EUR", "GBP"]
    },
    {
        "name": "Agdal Change",
        "type": "exchange",
        "category": "bureau",
        "rate": 10.01,
        "fee": 0,
        "fee_type": "included",
        "logo": "https://cdn-icons-png.flaticon.com/512/2830/2830284.png",
        "description": "Meilleurs taux à Rabat",
        "min_amount": 30,
        "max_amount": 40000,
        "processing_time": "instant",
        "is_active": True,
        "rating": 4.6,
        "supported_currencies": ["USD", "EUR", "GBP", "CHF"]
    },
]

def seed_suppliers():
    """Insère les fournisseurs dans MongoDB"""
    
    if not MONGO_URI:
        print("❌ Erreur: MONGO_URI non défini dans .env")
        return
    
    try:
        print(f"🔌 Connexion à MongoDB...")
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        print("✅ Connexion réussie")
        
        db = client[DB_NAME]
        
        # Supprimer les anciens fournisseurs
        existing_count = db.suppliers.count_documents({})
        if existing_count > 0:
            response = input(f"⚠️  {existing_count} fournisseurs existants. Supprimer et remplacer? (y/n): ")
            if response.lower() != 'y':
                print("Annulé.")
                return
            db.suppliers.delete_many({})
            print(f"🗑️  {existing_count} fournisseurs supprimés")
        
        # Ajouter timestamp
        for supplier in SUPPLIERS_DATA:
            supplier['created_at'] = datetime.utcnow()
            supplier['updated_at'] = datetime.utcnow()
        
        # Insérer les fournisseurs
        result = db.suppliers.insert_many(SUPPLIERS_DATA)
        print(f"✅ {len(result.inserted_ids)} fournisseurs ajoutés avec succès!")
        
        # Afficher un résumé par type
        print("\n📊 Résumé par type:")
        types = {}
        for s in SUPPLIERS_DATA:
            t = s['type']
            types[t] = types.get(t, 0) + 1
        for t, count in types.items():
            print(f"  - {t}: {count}")
        
        client.close()
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    seed_suppliers()
