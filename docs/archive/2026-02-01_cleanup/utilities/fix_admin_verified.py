#!/usr/bin/env python3
"""
Script pour fixer le statut de vérification de l'admin
"""

import os
from dotenv import load_dotenv
from pymongo import MongoClient
from datetime import datetime, timezone

# Charger les variables d'environnement
load_dotenv()

MONGO_URI = os.environ.get("MONGO_URI")
DB_NAME = os.environ.get("DB_NAME", "SarfX_Enhanced")

def fix_admin_verified():
    """Met à jour le statut verified de l'admin"""
    
    if not MONGO_URI:
        print("❌ Erreur: MONGO_URI non défini dans .env")
        return
    
    try:
        print(f"🔌 Connexion à MongoDB...")
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        print("✅ Connexion réussie")
        
        db = client[DB_NAME]
        
        # Trouver l'utilisateur admin
        admin_email = "starkxgroup@gmail.com"
        admin = db.users.find_one({"email": admin_email})
        
        if not admin:
            print(f"❌ Utilisateur {admin_email} non trouvé")
            return
        
        print(f"📊 Utilisateur trouvé: {admin_email}")
        print(f"   - Role: {admin.get('role', 'N/A')}")
        print(f"   - Verified: {admin.get('verified', False)}")
        print(f"   - Is Active: {admin.get('is_active', True)}")
        
        # Mettre à jour le statut verified
        result = db.users.update_one(
            {"email": admin_email},
            {
                "$set": {
                    "verified": True,
                    "is_active": True,
                    "role": "admin",
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )
        
        if result.modified_count > 0:
            print(f"✅ Utilisateur {admin_email} mis à jour:")
            print(f"   - verified: True")
            print(f"   - is_active: True")
            print(f"   - role: admin")
        else:
            print(f"⚠️  Aucune modification nécessaire (déjà à jour)")
        
        # Vérifier après mise à jour
        admin_updated = db.users.find_one({"email": admin_email})
        print(f"\n📋 État actuel:")
        print(f"   - verified: {admin_updated.get('verified', False)}")
        print(f"   - is_active: {admin_updated.get('is_active', True)}")
        print(f"   - role: {admin_updated.get('role', 'N/A')}")
        
        client.close()
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_admin_verified()
