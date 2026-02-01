#!/usr/bin/env python3
"""
Script pour initialiser l'utilisateur admin dans MongoDB
Utilise les variables d'environnement du fichier .env
"""

import os
import sys
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
from werkzeug.security import generate_password_hash

# Charger les variables d'environnement
load_dotenv()

MONGO_URI = os.environ.get("MONGO_URI")
DB_NAME = os.environ.get("DB_NAME", "SarfX_DB")
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "starkxgroup@gmail.com")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin")

def seed_admin():
    """Crée l'utilisateur admin dans MongoDB"""
    
    if not MONGO_URI:
        print("❌ Erreur: MONGO_URI non défini dans .env")
        sys.exit(1)
    
    try:
        print(f"🔌 Connexion à MongoDB: {MONGO_URI[:50]}...")
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        
        # Tester la connexion
        client.admin.command('ping')
        print("✅ Connexion à MongoDB réussie")
        
        db = client[DB_NAME]
        users_collection = db.users
        
        # Vérifier si l'admin existe déjà
        existing_admin = users_collection.find_one({"email": ADMIN_EMAIL})
        if existing_admin:
            print(f"⚠️  Admin {ADMIN_EMAIL} existe déjà")
            response = input("Voulez-vous le réinitialiser ? (y/n): ")
            if response.lower() != 'y':
                print("Annulé.")
                return
            users_collection.delete_one({"email": ADMIN_EMAIL})
            print(f"🗑️  Admin {ADMIN_EMAIL} supprimé")
        
        # Créer l'utilisateur admin
        hashed_password = generate_password_hash(ADMIN_PASSWORD)
        admin_user = {
            "email": ADMIN_EMAIL,
            "password": hashed_password,
            "role": "admin",
            "verified": True,
        }
        
        result = users_collection.insert_one(admin_user)
        print(f"✅ Admin créé avec succès!")
        print(f"   Email: {ADMIN_EMAIL}")
        print(f"   Mot de passe: {ADMIN_PASSWORD}")
        print(f"   ID MongoDB: {result.inserted_id}")
        
        client.close()
        print("\n🎉 Initialisation terminée!")
        
    except ServerSelectionTimeoutError:
        print("❌ Erreur: Impossible de se connecter à MongoDB")
        print(f"Vérifiez la connexion Internet et l'URI: {MONGO_URI[:50]}...")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    seed_admin()
