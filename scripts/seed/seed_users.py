#!/usr/bin/env python3
"""
Script pour créer les utilisateurs de démo : Admin et Bank Responsible
"""

import os
from dotenv import load_dotenv
from pymongo import MongoClient
from werkzeug.security import generate_password_hash
from datetime import datetime, timezone
import uuid

# Charger les variables d'environnement
load_dotenv()

MONGO_URI = os.environ.get("MONGO_URI")
DB_NAME = os.environ.get("DB_NAME", "SarfX_Enhanced")

# Utilisateurs de démo
DEMO_USERS = [
    {
        "email": "admin@sarfx.io",
        "password": "admin123",
        "role": "admin",
        "first_name": "Super",
        "last_name": "Admin",
        "full_name": "Super Admin",
        "phone": "+212 600-000001",
        "verified": True,
        "is_active": True,
        "permissions": ["all"],
        "description": "Administrateur principal du système"
    },
    {
        "email": "starkxgroup@gmail.com",
        "password": "admin",
        "role": "admin",
        "first_name": "Soufiane",
        "last_name": "Stark",
        "full_name": "Soufiane Stark",
        "phone": "+212 600-000002",
        "verified": True,
        "is_active": True,
        "permissions": ["all"],
        "description": "Super Admin"
    },
    {
        "email": "bank@attijariwafa.ma",
        "password": "bank123",
        "role": "bank_respo",
        "first_name": "Mohammed",
        "last_name": "Alaoui",
        "full_name": "Mohammed Alaoui",
        "phone": "+212 600-100001",
        "verified": True,
        "is_active": True,
        "bank_code": "attijariwafa",
        "bank_name": "Attijariwafa Bank",
        "permissions": ["view_atms", "manage_atms", "view_transactions"],
        "description": "Responsable bancaire Attijariwafa"
    },
    {
        "email": "bank@chaabi.ma",
        "password": "bank123",
        "role": "bank_respo",
        "first_name": "Fatima",
        "last_name": "Bennani",
        "full_name": "Fatima Bennani",
        "phone": "+212 600-100002",
        "verified": True,
        "is_active": True,
        "bank_code": "banque_populaire",
        "bank_name": "Banque Populaire",
        "permissions": ["view_atms", "manage_atms", "view_transactions"],
        "description": "Responsable bancaire Banque Populaire"
    },
    {
        "email": "user@demo.com",
        "password": "demo123",
        "role": "user",
        "first_name": "Demo",
        "last_name": "User",
        "full_name": "Demo User",
        "phone": "+212 600-200001",
        "verified": True,
        "is_active": True,
        "permissions": ["basic"],
        "description": "Utilisateur de démonstration"
    }
]

def seed_users():
    """Crée les utilisateurs de démo dans MongoDB"""
    
    if not MONGO_URI:
        print("❌ Erreur: MONGO_URI non défini dans .env")
        return
    
    try:
        print(f"🔌 Connexion à MongoDB...")
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        print("✅ Connexion réussie")
        
        db = client[DB_NAME]
        
        created_count = 0
        updated_count = 0
        
        for user_data in DEMO_USERS:
            email = user_data['email']
            
            # Vérifier si l'utilisateur existe
            existing = db.users.find_one({"email": email})
            
            # Préparer le document utilisateur
            user_doc = {
                "email": email,
                "password": generate_password_hash(user_data['password']),
                "role": user_data['role'],
                "first_name": user_data.get('first_name', ''),
                "last_name": user_data.get('last_name', ''),
                "full_name": user_data.get('full_name', ''),
                "phone": user_data.get('phone', ''),
                "verified": user_data.get('verified', True),
                "is_active": user_data.get('is_active', True),
                "permissions": user_data.get('permissions', []),
                "description": user_data.get('description', ''),
                "updated_at": datetime.now(timezone.utc)
            }
            
            # Ajouter les infos banque si c'est un bank_respo
            if user_data['role'] == 'bank_respo':
                user_doc['bank_code'] = user_data.get('bank_code', '')
                user_doc['bank_name'] = user_data.get('bank_name', '')
            
            if existing:
                # Mettre à jour l'utilisateur existant
                db.users.update_one(
                    {"email": email},
                    {"$set": user_doc}
                )
                print(f"🔄 Mis à jour: {email} ({user_data['role']})")
                updated_count += 1
            else:
                # Créer le nouvel utilisateur
                user_doc['created_at'] = datetime.now(timezone.utc)
                user_doc['token'] = str(uuid.uuid4())
                result = db.users.insert_one(user_doc)
                
                # Créer un wallet pour le nouvel utilisateur
                wallet_doc = {
                    "wallet_id": f"WLT-{str(uuid.uuid4())[:8].upper()}",
                    "user_id": str(result.inserted_id),
                    "email": email,
                    "balances": {
                        "USD": 1000.00 if user_data['role'] == 'user' else 5000.00,
                        "EUR": 850.00,
                        "MAD": 10000.00,
                        "GBP": 750.00
                    },
                    "is_active": True,
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc)
                }
                db.wallets.insert_one(wallet_doc)
                
                print(f"✅ Créé: {email} ({user_data['role']}) + wallet")
                created_count += 1
        
        print(f"\n📊 Résumé:")
        print(f"   - Créés: {created_count}")
        print(f"   - Mis à jour: {updated_count}")
        
        print("\n🔑 Comptes de démo:")
        print("   ┌─────────────────────────────┬────────────┬───────────┐")
        print("   │ Email                       │ Password   │ Role      │")
        print("   ├─────────────────────────────┼────────────┼───────────┤")
        for u in DEMO_USERS:
            print(f"   │ {u['email']:<27} │ {u['password']:<10} │ {u['role']:<9} │")
        print("   └─────────────────────────────┴────────────┴───────────┘")
        
        client.close()
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    seed_users()
