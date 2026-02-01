"""
Script pour initialiser la base de données avec des données d'ATM des banques partenaires
Exécuter avec: python seed_atm_data.py
"""

import sys
import os
from datetime import datetime
from pymongo import MongoClient
import certifi

# Ajouter le chemin de l'application au PATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.atm_service import ATMService


def get_db_direct():
    """Connexion directe à MongoDB sans contexte Flask"""
    try:
        # Utiliser les valeurs par défaut ou variables d'environnement
        mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
        db_name = os.getenv('DB_NAME', 'sarfx_db')
        
        client = MongoClient(
            mongo_uri,
            tlsCAFile=certifi.where(),
            serverSelectionTimeoutMS=5000
        )
        
        # Tester la connexion
        client.server_info()
        print(f"✅ Connexion MongoDB réussie: {db_name}")
        
        return client[db_name]
    except Exception as e:
        print(f"❌ Erreur de connexion MongoDB: {e}")
        print(f"   URI: {mongo_uri}")
        return None


def seed_atm_data():
    """
    Initialise la base de données avec des données d'ATM réalistes
    pour les principales villes du Maroc
    """
    print("🏦 Initialisation des données ATM...")
    
    # Se connecter à la base de données
    db = get_db_direct()
    if db is None:
        print("❌ Impossible de se connecter à la base de données")
        return False
    
    atm_service = ATMService(db)
    
    # Supprimer les données existantes (optionnel)
    print("🗑️  Suppression des anciennes données...")
    db.atm_locations.delete_many({})
    
    # Données des ATM par ville et banque
    atm_data = [
        # CASABLANCA - Attijariwafa Bank
        {
            "bank_code": "attijariwafa",
            "name": "ATM Attijariwafa Twin Center",
            "address": "Boulevard Zerktouni, Twin Center",
            "city": "Casablanca",
            "district": "Maarif",
            "location": {
                "type": "Point",
                "coordinates": [-7.626690, 33.591370]  # [longitude, latitude]
            },
            "services": ["withdrawal", "deposit", "balance", "transfer"],
            "available_24h": True,
            "has_wheelchair_access": True,
            "status": "active"
        },
        {
            "bank_code": "attijariwafa",
            "name": "ATM Attijariwafa Morocco Mall",
            "address": "Morocco Mall, Boulevard de l'Océan Atlantique",
            "city": "Casablanca",
            "district": "Anfa",
            "location": {
                "type": "Point",
                "coordinates": [-7.687430, 33.546910]
            },
            "services": ["withdrawal", "balance"],
            "available_24h": False,
            "hours": "10:00 - 22:00",
            "has_wheelchair_access": True,
            "status": "active"
        },
        {
            "bank_code": "attijariwafa",
            "name": "ATM Attijariwafa Place des Nations Unies",
            "address": "Place des Nations Unies",
            "city": "Casablanca",
            "district": "Centre Ville",
            "location": {
                "type": "Point",
                "coordinates": [-7.617900, 33.594150]
            },
            "services": ["withdrawal", "deposit", "balance"],
            "available_24h": True,
            "has_wheelchair_access": True,
            "status": "active"
        },
        
        # CASABLANCA - Bank of Africa
        {
            "bank_code": "boa",
            "name": "ATM BOA Ain Diab",
            "address": "Boulevard de la Corniche, Ain Diab",
            "city": "Casablanca",
            "district": "Ain Diab",
            "location": {
                "type": "Point",
                "coordinates": [-7.678900, 33.584320]
            },
            "services": ["withdrawal", "balance", "transfer"],
            "available_24h": True,
            "has_wheelchair_access": True,
            "status": "active"
        },
        {
            "bank_code": "boa",
            "name": "ATM BOA Maarif",
            "address": "Rue Abdelmoumen, Maarif",
            "city": "Casablanca",
            "district": "Maarif",
            "location": {
                "type": "Point",
                "coordinates": [-7.637800, 33.585900]
            },
            "services": ["withdrawal", "deposit", "balance"],
            "available_24h": True,
            "has_wheelchair_access": False,
            "status": "active"
        },
        
        # CASABLANCA - Banque Populaire
        {
            "bank_code": "banque_populaire",
            "name": "ATM BP Casa Port",
            "address": "Boulevard des Almohades, Casa Port",
            "city": "Casablanca",
            "district": "Casa Port",
            "location": {
                "type": "Point",
                "coordinates": [-7.612340, 33.601890]
            },
            "services": ["withdrawal", "balance", "transfer"],
            "available_24h": True,
            "has_wheelchair_access": True,
            "status": "active"
        },
        {
            "bank_code": "banque_populaire",
            "name": "ATM BP Anfa Place",
            "address": "Boulevard Moulay Youssef, Anfa",
            "city": "Casablanca",
            "district": "Anfa",
            "location": {
                "type": "Point",
                "coordinates": [-7.648900, 33.576540]
            },
            "services": ["withdrawal", "deposit", "balance"],
            "available_24h": False,
            "hours": "08:00 - 20:00",
            "has_wheelchair_access": True,
            "status": "active"
        },
        
        # CASABLANCA - CIH Bank
        {
            "bank_code": "cih",
            "name": "ATM CIH Gauthier",
            "address": "Boulevard Moulay Youssef, Gauthier",
            "city": "Casablanca",
            "district": "Gauthier",
            "location": {
                "type": "Point",
                "coordinates": [-7.629870, 33.592450]
            },
            "services": ["withdrawal", "balance"],
            "available_24h": True,
            "has_wheelchair_access": True,
            "status": "active"
        },
        {
            "bank_code": "cih",
            "name": "ATM CIH Bourgogne",
            "address": "Rue de Bourgogne",
            "city": "Casablanca",
            "district": "Bourgogne",
            "location": {
                "type": "Point",
                "coordinates": [-7.632100, 33.588900]
            },
            "services": ["withdrawal", "deposit", "balance", "transfer"],
            "available_24h": True,
            "has_wheelchair_access": False,
            "status": "active"
        },
        
        # CASABLANCA - Al Barid Bank
        {
            "bank_code": "albarid",
            "name": "ATM Al Barid Bank Derb Sultan",
            "address": "Boulevard Mohamed V, Derb Sultan",
            "city": "Casablanca",
            "district": "Derb Sultan",
            "location": {
                "type": "Point",
                "coordinates": [-7.604560, 33.589320]
            },
            "services": ["withdrawal", "balance"],
            "available_24h": False,
            "hours": "08:00 - 18:00",
            "has_wheelchair_access": True,
            "status": "active"
        },
        
        # CASABLANCA - BMCI
        {
            "bank_code": "bmci",
            "name": "ATM BMCI Boulevard Anfa",
            "address": "Boulevard d'Anfa",
            "city": "Casablanca",
            "district": "Anfa",
            "location": {
                "type": "Point",
                "coordinates": [-7.641200, 33.588700]
            },
            "services": ["withdrawal", "deposit", "balance", "transfer"],
            "available_24h": True,
            "has_wheelchair_access": True,
            "status": "active"
        },
        
        # RABAT - Attijariwafa Bank
        {
            "bank_code": "attijariwafa",
            "name": "ATM Attijariwafa Agdal",
            "address": "Avenue de France, Agdal",
            "city": "Rabat",
            "district": "Agdal",
            "location": {
                "type": "Point",
                "coordinates": [-6.847890, 33.984560]
            },
            "services": ["withdrawal", "deposit", "balance", "transfer"],
            "available_24h": True,
            "has_wheelchair_access": True,
            "status": "active"
        },
        {
            "bank_code": "attijariwafa",
            "name": "ATM Attijariwafa Hassan",
            "address": "Avenue Hassan II",
            "city": "Rabat",
            "district": "Hassan",
            "location": {
                "type": "Point",
                "coordinates": [-6.830120, 34.020450]
            },
            "services": ["withdrawal", "balance"],
            "available_24h": True,
            "has_wheelchair_access": True,
            "status": "active"
        },
        
        # RABAT - Bank of Africa
        {
            "bank_code": "boa",
            "name": "ATM BOA Hay Riad",
            "address": "Avenue Annakhil, Hay Riad",
            "city": "Rabat",
            "district": "Hay Riad",
            "location": {
                "type": "Point",
                "coordinates": [-6.857340, 33.960120]
            },
            "services": ["withdrawal", "balance", "transfer"],
            "available_24h": True,
            "has_wheelchair_access": True,
            "status": "active"
        },
        
        # RABAT - Banque Populaire
        {
            "bank_code": "banque_populaire",
            "name": "ATM BP Avenue Mohammed V",
            "address": "Avenue Mohammed V",
            "city": "Rabat",
            "district": "Centre Ville",
            "location": {
                "type": "Point",
                "coordinates": [-6.832450, 34.021340]
            },
            "services": ["withdrawal", "deposit", "balance"],
            "available_24h": True,
            "has_wheelchair_access": False,
            "status": "active"
        },
        
        # MARRAKECH - Attijariwafa Bank
        {
            "bank_code": "attijariwafa",
            "name": "ATM Attijariwafa Guéliz",
            "address": "Avenue Mohammed V, Guéliz",
            "city": "Marrakech",
            "district": "Guéliz",
            "location": {
                "type": "Point",
                "coordinates": [-8.007890, 31.634560]
            },
            "services": ["withdrawal", "deposit", "balance", "transfer"],
            "available_24h": True,
            "has_wheelchair_access": True,
            "status": "active"
        },
        {
            "bank_code": "attijariwafa",
            "name": "ATM Attijariwafa Place Jemaa El Fna",
            "address": "Place Jemaa El Fna, Médina",
            "city": "Marrakech",
            "district": "Médina",
            "location": {
                "type": "Point",
                "coordinates": [-7.989120, 31.625900]
            },
            "services": ["withdrawal", "balance"],
            "available_24h": True,
            "has_wheelchair_access": False,
            "status": "active"
        },
        
        # MARRAKECH - Bank of Africa
        {
            "bank_code": "boa",
            "name": "ATM BOA Hivernage",
            "address": "Avenue Echouhada, Hivernage",
            "city": "Marrakech",
            "district": "Hivernage",
            "location": {
                "type": "Point",
                "coordinates": [-8.015670, 31.624780]
            },
            "services": ["withdrawal", "balance", "transfer"],
            "available_24h": True,
            "has_wheelchair_access": True,
            "status": "active"
        },
        
        # MARRAKECH - CIH Bank
        {
            "bank_code": "cih",
            "name": "ATM CIH Ménara Mall",
            "address": "Boulevard Mohamed Zerktouni, Ménara Mall",
            "city": "Marrakech",
            "district": "Guéliz",
            "location": {
                "type": "Point",
                "coordinates": [-8.019450, 31.641230]
            },
            "services": ["withdrawal", "deposit", "balance"],
            "available_24h": False,
            "hours": "10:00 - 22:00",
            "has_wheelchair_access": True,
            "status": "active"
        },
        
        # TANGER - Attijariwafa Bank
        {
            "bank_code": "attijariwafa",
            "name": "ATM Attijariwafa Boulevard Pasteur",
            "address": "Boulevard Pasteur",
            "city": "Tanger",
            "district": "Centre Ville",
            "location": {
                "type": "Point",
                "coordinates": [-5.811230, 35.773450]
            },
            "services": ["withdrawal", "deposit", "balance", "transfer"],
            "available_24h": True,
            "has_wheelchair_access": True,
            "status": "active"
        },
        
        # TANGER - Banque Populaire
        {
            "bank_code": "banque_populaire",
            "name": "ATM BP Tanger City Center",
            "address": "Tanger City Center, Route de Rabat",
            "city": "Tanger",
            "district": "Tanger City Center",
            "location": {
                "type": "Point",
                "coordinates": [-5.837890, 35.757120]
            },
            "services": ["withdrawal", "balance"],
            "available_24h": False,
            "hours": "10:00 - 22:00",
            "has_wheelchair_access": True,
            "status": "active"
        },
        
        # FES - Attijariwafa Bank
        {
            "bank_code": "attijariwafa",
            "name": "ATM Attijariwafa Avenue Hassan II",
            "address": "Avenue Hassan II",
            "city": "Fès",
            "district": "Ville Nouvelle",
            "location": {
                "type": "Point",
                "coordinates": [-4.998900, 34.036780]
            },
            "services": ["withdrawal", "deposit", "balance"],
            "available_24h": True,
            "has_wheelchair_access": True,
            "status": "active"
        },
        
        # FES - Bank of Africa
        {
            "bank_code": "boa",
            "name": "ATM BOA Borj Fès Mall",
            "address": "Borj Fès Mall, Route d'Imouzzer",
            "city": "Fès",
            "district": "Route d'Imouzzer",
            "location": {
                "type": "Point",
                "coordinates": [-5.005600, 34.059800]
            },
            "services": ["withdrawal", "balance", "transfer"],
            "available_24h": False,
            "hours": "10:00 - 22:00",
            "has_wheelchair_access": True,
            "status": "active"
        },
        
        # AGADIR - Attijariwafa Bank
        {
            "bank_code": "attijariwafa",
            "name": "ATM Attijariwafa Boulevard Hassan II",
            "address": "Boulevard Hassan II",
            "city": "Agadir",
            "district": "Centre Ville",
            "location": {
                "type": "Point",
                "coordinates": [-9.598700, 30.428900]
            },
            "services": ["withdrawal", "deposit", "balance", "transfer"],
            "available_24h": True,
            "has_wheelchair_access": True,
            "status": "active"
        },
        
        # AGADIR - CIH Bank
        {
            "bank_code": "cih",
            "name": "ATM CIH Marina d'Agadir",
            "address": "Marina d'Agadir",
            "city": "Agadir",
            "district": "Marina",
            "location": {
                "type": "Point",
                "coordinates": [-9.637890, 30.415600]
            },
            "services": ["withdrawal", "balance"],
            "available_24h": False,
            "hours": "09:00 - 21:00",
            "has_wheelchair_access": True,
            "status": "active"
        }
    ]
    
    # Insérer les données
    inserted_count = 0
    for atm in atm_data:
        try:
            result = atm_service.add_atm(atm)
            if result:
                inserted_count += 1
                print(f"✅ ATM ajouté: {atm['name']} - {atm['city']}")
        except Exception as e:
            print(f"❌ Erreur pour {atm['name']}: {e}")
    
    # Afficher le résumé
    print(f"\n📊 Résumé de l'initialisation:")
    print(f"   Total ATM insérés: {inserted_count}/{len(atm_data)}")
    
    # Afficher les statistiques par banque
    banks = atm_service.get_all_banks()
    print(f"\n🏦 ATM par banque:")
    for bank in banks:
        print(f"   {bank['name']}: {bank['atm_count']} ATM")
    
    # Afficher les statistiques par ville
    cities = atm_service.get_cities_with_atms()
    print(f"\n🏙️  ATM par ville:")
    for city in cities:
        print(f"   {city['city']}: {city['atm_count']} ATM")
    
    print(f"\n✨ Initialisation terminée avec succès!")


if __name__ == "__main__":
    try:
        seed_atm_data()
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation: {e}")
        sys.exit(1)
