#!/usr/bin/env python3
"""
Script pour initialiser les banques partenaires dans MongoDB
"""

from pymongo import MongoClient
import certifi
from datetime import datetime

def get_db_direct():
    """Connexion directe à MongoDB"""
    uri = 'mongodb+srv://soufiane:gogo@cluster0.05omqhe.mongodb.net/SarfX_Enhanced'
    client = MongoClient(uri, tlsCAFile=certifi.where())
    return client['SarfX_Enhanced']

def seed_banks_data():
    """Initialise les banques partenaires"""
    db = get_db_direct()
    
    print("🏦 Initialisation des banques partenaires...\n")
    
    # Supprimer les anciennes données
    db.banks.delete_many({})
    print("🗑️  Suppression des anciennes données...")
    
    # Données des 6 banques marocaines avec nombres réels d'ATMs
    banks = [
        {
            "name": "Attijariwafa Bank",
            "code": "attijariwafa",
            "website": "https://www.attijariwafabank.com",
            "description": "Leader du secteur bancaire marocain et africain",
            "logo": "/static/images/banks/attijariwafa.svg",
            "atm_count": 1242,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "name": "Bank of Africa",
            "code": "boa",
            "website": "https://www.bankofafrica.ma",
            "description": "BMCE Bank of Africa, banque panafricaine",
            "logo": "/static/images/banks/boa.svg",
            "atm_count": 660,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "name": "Banque Populaire",
            "code": "banque-populaire",
            "website": "https://www.gbp.ma",
            "description": "Groupe Banque Populaire, première banque coopérative au Maroc",
            "logo": "/static/images/banks/banque-populaire.svg",
            "atm_count": 1800,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "name": "CIH Bank",
            "code": "cih",
            "website": "https://www.cih.co.ma",
            "description": "Crédit Immobilier et Hôtelier",
            "logo": "/static/images/banks/cih.svg",
            "atm_count": 626,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "name": "Al Barid Bank",
            "code": "albarid",
            "website": "https://www.albaridbank.ma",
            "description": "Banque postale du Maroc",
            "logo": "/static/images/banks/albarid.svg",
            "atm_count": 510,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "name": "BMCI",
            "code": "bmci",
            "website": "https://www.bmcinet.co.ma",
            "description": "Banque Marocaine pour le Commerce et l'Industrie",
            "logo": "/static/images/banks/bmci.svg",
            "atm_count": 249,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    ]
    
    # Insertion
    inserted_count = 0
    for bank in banks:
        result = db.banks.insert_one(bank)
        print(f"✅ Banque ajoutée: {bank['name']}")
        inserted_count += 1
    
    print(f"\n📊 Résumé:")
    print(f"   Total banques insérées: {inserted_count}/{len(banks)}")
    
    # Créer index sur code
    db.banks.create_index([("code", 1)], unique=True)
    print(f"✅ Index créé sur 'code'")
    
    print("\n🎉 Initialisation des banques terminée!")

if __name__ == "__main__":
    seed_banks_data()
