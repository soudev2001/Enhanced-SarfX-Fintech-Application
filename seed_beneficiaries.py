#!/usr/bin/env python3
"""
Script pour créer des bénéficiaires fictifs pour les utilisateurs
"""

import os
import random
from dotenv import load_dotenv
from pymongo import MongoClient
from datetime import datetime, timezone
import uuid

# Charger les variables d'environnement
load_dotenv()

MONGO_URI = os.environ.get("MONGO_URI")
DB_NAME = os.environ.get("DB_NAME", "SarfX_Enhanced")

# Prénoms marocains
FIRST_NAMES = [
    "Mohammed", "Ahmed", "Youssef", "Omar", "Hassan", "Ali", "Karim", "Rachid", "Said", "Hamid",
    "Fatima", "Khadija", "Amina", "Samira", "Laila", "Nadia", "Zineb", "Hanane", "Meryem", "Sara",
    "Soufiane", "Mehdi", "Amine", "Ayoub", "Ilyas", "Zakaria", "Yassine", "Reda", "Mouad", "Othmane"
]

# Noms de famille marocains
LAST_NAMES = [
    "Alaoui", "Bennani", "El Fassi", "Benjelloun", "Tazi", "Cherkaoui", "El Idrissi", "Bouazza",
    "Lahlou", "Belkacem", "Naciri", "El Omari", "Sqalli", "Berrada", "El Ghazi", "Benhaddou",
    "Sekkat", "El Moustakim", "Amrani", "Benkirane", "Filali", "El Hamdaoui", "Chakir", "Bensouda"
]

# Banques marocaines
BANKS = [
    {"code": "attijariwafa", "name": "Attijariwafa Bank", "swift": "BCMAMAMC"},
    {"code": "banque_populaire", "name": "Banque Populaire", "swift": "BCPOMAMC"},
    {"code": "boa", "name": "BMCE Bank of Africa", "swift": "BMCEMAMC"},
    {"code": "cih", "name": "CIH Bank", "swift": "CIHMMAMC"},
    {"code": "bmci", "name": "BMCI", "swift": "BMCIMAMC"},
]

# Villes marocaines
CITIES = ["Casablanca", "Rabat", "Marrakech", "Fès", "Tanger", "Agadir", "Meknès", "Oujda", "Kenitra", "Tétouan"]

def generate_iban():
    """Génère un IBAN marocain fictif"""
    bank_code = random.choice(["007", "011", "013", "021", "025"])
    account = ''.join([str(random.randint(0, 9)) for _ in range(20)])
    return f"MA{random.randint(10, 99)}{bank_code}{account}"

def generate_rib():
    """Génère un RIB marocain fictif"""
    return ''.join([str(random.randint(0, 9)) for _ in range(24)])

def generate_phone():
    """Génère un numéro de téléphone marocain fictif"""
    prefixes = ["06", "07"]
    return f"+212 {random.choice(prefixes)}{random.randint(10000000, 99999999)}"

def create_beneficiary(user_id, user_email):
    """Crée un bénéficiaire fictif"""
    first_name = random.choice(FIRST_NAMES)
    last_name = random.choice(LAST_NAMES)
    bank = random.choice(BANKS)
    city = random.choice(CITIES)
    
    return {
        "beneficiary_id": str(uuid.uuid4())[:12].upper(),
        "user_id": str(user_id),
        "user_email": user_email,
        "name": f"{first_name} {last_name}",
        "first_name": first_name,
        "last_name": last_name,
        "bank_code": bank["code"],
        "bank_name": bank["name"],
        "swift_code": bank["swift"],
        "iban": generate_iban(),
        "rib": generate_rib(),
        "phone": generate_phone(),
        "email": f"{first_name.lower()}.{last_name.lower()}@example.com",
        "city": city,
        "country": "Maroc",
        "currency": "MAD",
        "is_favorite": random.choice([True, False]),
        "is_verified": random.choice([True, True, True, False]),  # 75% verified
        "transfer_count": random.randint(0, 15),
        "last_transfer_at": datetime.now(timezone.utc) if random.random() > 0.5 else None,
        "notes": random.choice([
            "", 
            "Famille", 
            "Ami", 
            "Business", 
            "Loyer mensuel",
            "Partenaire commercial",
            ""
        ]),
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }

def seed_beneficiaries():
    """Insère des bénéficiaires fictifs pour chaque utilisateur"""
    
    if not MONGO_URI:
        print("❌ Erreur: MONGO_URI non défini dans .env")
        return
    
    try:
        print(f"🔌 Connexion à MongoDB...")
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        print("✅ Connexion réussie")
        
        db = client[DB_NAME]
        
        # Récupérer tous les utilisateurs
        users = list(db.users.find())
        print(f"📊 {len(users)} utilisateurs trouvés")
        
        if len(users) == 0:
            print("⚠️  Aucun utilisateur trouvé. Créez d'abord des utilisateurs.")
            return
        
        # Supprimer les anciens bénéficiaires
        existing_count = db.beneficiaries.count_documents({})
        if existing_count > 0:
            response = input(f"⚠️  {existing_count} bénéficiaires existants. Supprimer et remplacer? (y/n): ")
            if response.lower() != 'y':
                print("Annulé.")
                return
            db.beneficiaries.delete_many({})
            print(f"🗑️  {existing_count} bénéficiaires supprimés")
        
        # Créer des bénéficiaires pour chaque utilisateur
        all_beneficiaries = []
        for user in users:
            user_id = user['_id']
            user_email = user.get('email', 'unknown@example.com')
            
            # Chaque utilisateur a entre 2 et 6 bénéficiaires
            num_beneficiaries = random.randint(2, 6)
            
            for _ in range(num_beneficiaries):
                beneficiary = create_beneficiary(user_id, user_email)
                all_beneficiaries.append(beneficiary)
        
        # Insérer tous les bénéficiaires
        if all_beneficiaries:
            result = db.beneficiaries.insert_many(all_beneficiaries)
            print(f"✅ {len(result.inserted_ids)} bénéficiaires créés!")
            
            # Statistiques
            print("\n📊 Statistiques:")
            for user in users:
                count = sum(1 for b in all_beneficiaries if b['user_email'] == user.get('email'))
                print(f"  - {user.get('email')}: {count} bénéficiaires")
        
        client.close()
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    seed_beneficiaries()
