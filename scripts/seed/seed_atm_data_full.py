"""
Script pour initialiser la base de données avec les 4577 ATM des 5 banques partenaires marocaines
Répartition: Attijari (1242), BOA (660), Chaabi (1800), CIH (626), BMCI (249)
Exécuter avec: python seed_atm_data_full.py
"""

import sys
import os
import random
from datetime import datetime
from pymongo import MongoClient
import certifi
from dotenv import load_dotenv

# Charger le fichier .env
load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuration des banques avec leurs quotas d'ATM
BANKS_CONFIG = {
    "attijariwafa": {
        "name": "Attijariwafa Bank",
        "atm_target": 1242,
        "prefix": "ATW"
    },
    "boa": {
        "name": "Bank of Africa",
        "atm_target": 660,
        "prefix": "BOA"
    },
    "banque_populaire": {
        "name": "Banque Populaire (Chaabi)",
        "atm_target": 1800,
        "prefix": "BCP"
    },
    "cih": {
        "name": "CIH Bank",
        "atm_target": 626,
        "prefix": "CIH"
    },
    "bmci": {
        "name": "BMCI",
        "atm_target": 249,
        "prefix": "BMC"
    }
}

# Villes marocaines avec coordonnées GPS et poids de distribution
MOROCCAN_CITIES = [
    # Grandes métropoles (35% des ATM)
    {"city": "Casablanca", "lat": 33.5731, "lon": -7.5898, "weight": 18, "districts": [
        "Maarif", "Anfa", "Gauthier", "Bourgogne", "Centre Ville", "Hay Hassani", "Sidi Belyout", 
        "Ain Chock", "Ain Sebaa", "Ben M'sick", "Bernoussi", "Sidi Moumen", "Sbata", "Roches Noires",
        "Derb Sultan", "Habous", "Mers Sultan", "2 Mars", "Oulfa", "Hay Mohammadi"
    ]},
    {"city": "Rabat", "lat": 34.0209, "lon": -6.8416, "weight": 10, "districts": [
        "Agdal", "Hassan", "Hay Riad", "Souissi", "Yacoub El Mansour", "Akkari", "Océan",
        "Médina", "Takaddoum", "Youssoufia", "Temara", "Salé Centre"
    ]},
    {"city": "Marrakech", "lat": 31.6295, "lon": -7.9811, "weight": 8, "districts": [
        "Guéliz", "Hivernage", "Médina", "Palmeraie", "Targa", "Semlalia", "Daoudiate",
        "M'hamid", "Sidi Youssef Ben Ali", "Massira", "Ménara", "Annakhil"
    ]},
    
    # Grandes villes (25% des ATM)
    {"city": "Fès", "lat": 34.0181, "lon": -5.0078, "weight": 6, "districts": [
        "Ville Nouvelle", "Médina", "Saiss", "Narjiss", "Mont Fleuri", "Adarissa",
        "Zouagha", "Dhar El Mahraz", "Oued Fès"
    ]},
    {"city": "Tanger", "lat": 35.7595, "lon": -5.8340, "weight": 5, "districts": [
        "Centre Ville", "Malabata", "Médina", "Moujahidine", "Marshan", "Beni Makada",
        "Val Fleuri", "Tanger City Center", "Iberia", "Souani"
    ]},
    {"city": "Agadir", "lat": 30.4278, "lon": -9.5981, "weight": 4, "districts": [
        "Centre Ville", "Talborjt", "Hay Mohammadi", "Founty", "Tikouine", 
        "Charaf", "Dakhla", "Tilila", "Agadir Oufella"
    ]},
    {"city": "Meknès", "lat": 33.8935, "lon": -5.5473, "weight": 3, "districts": [
        "Ville Nouvelle", "Médina", "Hamria", "Marjane", "Zitoune", "Rouamzine"
    ]},
    {"city": "Oujda", "lat": 34.6805, "lon": -1.9076, "weight": 3, "districts": [
        "Centre Ville", "Médina", "Lazaret", "Hay Al Andalous", "Si Kaddour"
    ]},
    
    # Villes moyennes (20% des ATM)
    {"city": "Kenitra", "lat": 34.2541, "lon": -6.5890, "weight": 2.5, "districts": [
        "Centre Ville", "Bir Rami", "Oulad Oujih", "Maamora", "Mehdia"
    ]},
    {"city": "Tétouan", "lat": 35.5785, "lon": -5.3684, "weight": 2, "districts": [
        "Centre Ville", "Médina", "Martil", "M'diq", "Touabel"
    ]},
    {"city": "El Jadida", "lat": 33.2316, "lon": -8.5007, "weight": 2, "districts": [
        "Centre Ville", "Cité Portugaise", "Hay Essalam", "Sidi Bouzid"
    ]},
    {"city": "Safi", "lat": 32.2833, "lon": -9.2333, "weight": 1.5, "districts": [
        "Centre Ville", "Médina", "Jrifate", "Sidi Bouzid"
    ]},
    {"city": "Mohammedia", "lat": 33.6861, "lon": -7.3828, "weight": 2, "districts": [
        "Centre Ville", "Alia", "Hassania", "Palmier"
    ]},
    {"city": "Béni Mellal", "lat": 32.3373, "lon": -6.3498, "weight": 1.5, "districts": [
        "Centre Ville", "Hay Al Qods", "Ouled M'Barek"
    ]},
    {"city": "Nador", "lat": 35.1681, "lon": -2.9287, "weight": 1.5, "districts": [
        "Centre Ville", "Selouane", "Al Aaroui"
    ]},
    {"city": "Khouribga", "lat": 32.8811, "lon": -6.9063, "weight": 1, "districts": [
        "Centre Ville", "Hay Al Qods", "Hay Riad"
    ]},
    
    # Petites villes (20% des ATM)
    {"city": "Settat", "lat": 33.0019, "lon": -7.6166, "weight": 1, "districts": ["Centre Ville", "Hay Salam"]},
    {"city": "Taza", "lat": 34.2100, "lon": -4.0100, "weight": 0.8, "districts": ["Centre Ville", "Médina"]},
    {"city": "Errachidia", "lat": 31.9314, "lon": -4.4267, "weight": 0.7, "districts": ["Centre Ville", "Hay Riad"]},
    {"city": "Essaouira", "lat": 31.5085, "lon": -9.7595, "weight": 0.8, "districts": ["Centre Ville", "Médina"]},
    {"city": "Khémisset", "lat": 33.8242, "lon": -6.0661, "weight": 0.7, "districts": ["Centre Ville"]},
    {"city": "Larache", "lat": 35.1932, "lon": -6.1561, "weight": 0.7, "districts": ["Centre Ville", "Médina"]},
    {"city": "Ksar El Kébir", "lat": 35.0000, "lon": -5.9000, "weight": 0.6, "districts": ["Centre Ville"]},
    {"city": "Guelmim", "lat": 28.9870, "lon": -10.0574, "weight": 0.5, "districts": ["Centre Ville"]},
    {"city": "Ouarzazate", "lat": 30.9189, "lon": -6.8973, "weight": 0.6, "districts": ["Centre Ville", "Tabounte"]},
    {"city": "Al Hoceima", "lat": 35.2517, "lon": -3.9372, "weight": 0.7, "districts": ["Centre Ville", "Calabonita"]},
    {"city": "Berkane", "lat": 34.9167, "lon": -2.3167, "weight": 0.5, "districts": ["Centre Ville"]},
    {"city": "Taourirt", "lat": 34.4167, "lon": -2.8833, "weight": 0.4, "districts": ["Centre Ville"]},
    {"city": "Dakhla", "lat": 23.6848, "lon": -15.9579, "weight": 0.4, "districts": ["Centre Ville", "Port"]},
    {"city": "Laayoune", "lat": 27.1536, "lon": -13.2033, "weight": 0.5, "districts": ["Centre Ville", "Hay Al Wahda"]},
    {"city": "Tan-Tan", "lat": 28.4378, "lon": -11.1033, "weight": 0.3, "districts": ["Centre Ville"]},
    {"city": "Tiznit", "lat": 29.7000, "lon": -9.7333, "weight": 0.4, "districts": ["Centre Ville", "Médina"]},
    {"city": "Taroudant", "lat": 30.4706, "lon": -8.8769, "weight": 0.4, "districts": ["Centre Ville", "Médina"]},
    {"city": "Chefchaouen", "lat": 35.1688, "lon": -5.2636, "weight": 0.4, "districts": ["Centre Ville", "Médina"]},
    {"city": "Ifrane", "lat": 33.5333, "lon": -5.1000, "weight": 0.3, "districts": ["Centre Ville"]},
    {"city": "Azrou", "lat": 33.4333, "lon": -5.2167, "weight": 0.3, "districts": ["Centre Ville"]},
]

# Types de lieux pour les ATM
LOCATION_TYPES = [
    {"type": "branch", "name": "Agence", "weight": 45},
    {"type": "mall", "name": "Centre Commercial", "weight": 15},
    {"type": "supermarket", "name": "Supermarché", "weight": 10},
    {"type": "station", "name": "Station Service", "weight": 8},
    {"type": "hospital", "name": "Hôpital/Clinique", "weight": 5},
    {"type": "university", "name": "Université", "weight": 5},
    {"type": "airport", "name": "Aéroport", "weight": 2},
    {"type": "train_station", "name": "Gare", "weight": 3},
    {"type": "hotel", "name": "Hôtel", "weight": 4},
    {"type": "standalone", "name": "Kiosque", "weight": 3},
]

# Services disponibles
SERVICES_OPTIONS = [
    ["withdrawal", "balance"],
    ["withdrawal", "deposit", "balance"],
    ["withdrawal", "balance", "transfer"],
    ["withdrawal", "deposit", "balance", "transfer"],
    ["withdrawal", "deposit", "balance", "transfer", "bill_payment"],
]


def get_db_direct():
    """Connexion directe à MongoDB"""
    try:
        mongo_uri = os.getenv('MONGO_URI')
        if not mongo_uri:
            print("❌ MONGO_URI non défini dans .env")
            return None
        
        # Extraire le nom de la DB depuis l'URI ou utiliser une valeur par défaut
        db_name = 'SarfX_Enhanced'
        if '/' in mongo_uri:
            potential_db = mongo_uri.split('/')[-1].split('?')[0]
            if potential_db:
                db_name = potential_db
        
        print(f"🔗 Connexion à MongoDB Atlas...")
        client = MongoClient(
            mongo_uri,
            tlsCAFile=certifi.where(),
            serverSelectionTimeoutMS=10000
        )
        client.server_info()
        print(f"✅ Connexion MongoDB réussie: {db_name}")
        return client[db_name]
    except Exception as e:
        print(f"❌ Erreur de connexion MongoDB: {e}")
        return None


def generate_coordinates(base_lat, base_lon, radius_km=5):
    """Génère des coordonnées aléatoires autour d'un point"""
    # 1 degré ≈ 111 km
    lat_offset = random.uniform(-radius_km/111, radius_km/111)
    lon_offset = random.uniform(-radius_km/111, radius_km/111)
    return round(base_lat + lat_offset, 6), round(base_lon + lon_offset, 6)


def select_weighted(options, weight_key="weight"):
    """Sélection pondérée"""
    total = sum(o[weight_key] for o in options)
    r = random.uniform(0, total)
    cumulative = 0
    for option in options:
        cumulative += option[weight_key]
        if r <= cumulative:
            return option
    return options[-1]


def generate_atm_name(bank_code, location_type, city, district, index):
    """Génère un nom d'ATM réaliste"""
    bank_name = BANKS_CONFIG[bank_code]["name"].split()[0]
    prefix = BANKS_CONFIG[bank_code]["prefix"]
    
    if location_type["type"] == "branch":
        return f"ATM {bank_name} {district}"
    elif location_type["type"] == "mall":
        malls = ["Morocco Mall", "Marjane", "Carrefour", "Aswak Assalam", "Acima"]
        return f"ATM {bank_name} {random.choice(malls)} {city}"
    elif location_type["type"] == "station":
        stations = ["Shell", "Afriquia", "Total", "Winxo", "Ziz"]
        return f"ATM {bank_name} Station {random.choice(stations)}"
    elif location_type["type"] == "airport":
        return f"ATM {bank_name} Aéroport {city}"
    elif location_type["type"] == "train_station":
        return f"ATM {bank_name} Gare {city}"
    else:
        return f"ATM {bank_name} {district} {index}"


def generate_address(location_type, city, district):
    """Génère une adresse réaliste"""
    street_types = ["Avenue", "Boulevard", "Rue", "Place"]
    street_names = [
        "Mohammed V", "Hassan II", "Mohammed VI", "Moulay Youssef", "FAR",
        "Allal Ben Abdallah", "Zerktouni", "Abdelmoumen", "Massira", "Al Qods",
        "Palestine", "Nations Unies", "France", "Fès", "Marrakech"
    ]
    
    if location_type["type"] == "branch":
        return f"{random.choice(street_types)} {random.choice(street_names)}, {district}"
    elif location_type["type"] == "mall":
        return f"Centre Commercial, {district}, {city}"
    else:
        return f"{random.choice(street_types)} {random.choice(street_names)}, {district}, {city}"


def generate_atm(bank_code, city_info, index, source_id):
    """Génère un ATM complet"""
    city = city_info["city"]
    district = random.choice(city_info["districts"])
    location_type = select_weighted(LOCATION_TYPES)
    
    lat, lon = generate_coordinates(city_info["lat"], city_info["lon"])
    
    atm = {
        "atm_id": f"{BANKS_CONFIG[bank_code]['prefix']}_{city[:3].upper()}_{index:05d}",
        "bank_code": bank_code,
        "name": generate_atm_name(bank_code, location_type, city, district, index),
        "address": generate_address(location_type, city, district),
        "city": city,
        "district": district,
        "location": {
            "type": "Point",
            "coordinates": [lon, lat]  # [longitude, latitude] pour MongoDB
        },
        "location_type": location_type["type"],
        "services": random.choice(SERVICES_OPTIONS),
        "available_24h": random.random() < 0.7,  # 70% sont 24h
        "has_wheelchair_access": random.random() < 0.6,  # 60% accessibles
        "has_nfc": random.random() < 0.4,  # 40% ont NFC
        "has_deposit": "deposit" in random.choice(SERVICES_OPTIONS),
        "status": "active",
        "source_id": source_id,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    
    if not atm["available_24h"]:
        atm["hours"] = random.choice([
            "08:00 - 18:00", "08:00 - 20:00", "09:00 - 19:00", "08:30 - 16:30"
        ])
    
    return atm


def seed_sources(db):
    """Crée les sources de données"""
    sources = [
        {
            "source_id": "SRC_INITIAL_2026",
            "type": "initial_seed",
            "name": "Import initial banques partenaires",
            "description": "Données initiales des 4577 ATM des 5 banques partenaires marocaines",
            "banks": list(BANKS_CONFIG.keys()),
            "total_atms": 4577,
            "imported_at": datetime.now(),
            "imported_by": "system",
            "status": "completed"
        }
    ]
    
    db.sources.delete_many({})
    db.sources.insert_many(sources)
    print("✅ Sources créées")
    return "SRC_INITIAL_2026"


def seed_banks(db):
    """Met à jour les informations des banques avec les quotas"""
    banks_data = [
        {
            "code": "attijariwafa",
            "name": "Attijariwafa Bank",
            "name_ar": "التجاري وفا بنك",
            "logo": "/static/images/banks/attijariwafa.svg",
            "color": "#E30613",
            "website": "https://www.attijariwafabank.com",
            "atm_quota": 1242,
            "is_partner": True,
            "is_active": True,
            "updated_at": datetime.now()
        },
        {
            "code": "boa",
            "name": "Bank of Africa",
            "name_ar": "بنك أفريقيا",
            "logo": "/static/images/banks/boa.svg",
            "color": "#00843D",
            "website": "https://www.bankofafrica.ma",
            "atm_quota": 660,
            "is_partner": True,
            "is_active": True,
            "updated_at": datetime.now()
        },
        {
            "code": "banque_populaire",
            "name": "Banque Populaire",
            "name_ar": "البنك الشعبي",
            "logo": "/static/images/banks/banque-populaire.svg",
            "color": "#005BAA",
            "website": "https://www.gbp.ma",
            "atm_quota": 1800,
            "is_partner": True,
            "is_active": True,
            "updated_at": datetime.now()
        },
        {
            "code": "cih",
            "name": "CIH Bank",
            "name_ar": "بنك القرض العقاري والسياحي",
            "logo": "/static/images/banks/cih.svg",
            "color": "#C41E3A",
            "website": "https://www.cih.co.ma",
            "atm_quota": 626,
            "is_partner": True,
            "is_active": True,
            "updated_at": datetime.now()
        },
        {
            "code": "bmci",
            "name": "BMCI",
            "name_ar": "البنك المغربي للتجارة والصناعة",
            "logo": "/static/images/banks/bmci.svg",
            "color": "#DC0032",
            "website": "https://www.bmci.ma",
            "atm_quota": 249,
            "is_partner": True,
            "is_active": True,
            "updated_at": datetime.now()
        },
        {
            "code": "albarid",
            "name": "Al Barid Bank",
            "name_ar": "بنك البريد",
            "logo": "/static/images/banks/albarid.svg",
            "color": "#FFD700",
            "website": "https://www.albaridbank.ma",
            "atm_quota": 0,
            "is_partner": False,
            "is_active": True,
            "updated_at": datetime.now()
        }
    ]
    
    for bank in banks_data:
        db.banks.update_one(
            {"code": bank["code"]},
            {"$set": bank},
            upsert=True
        )
    
    print("✅ Banques mises à jour")


def distribute_atms_by_city(total_atms):
    """Distribue les ATM selon le poids des villes"""
    total_weight = sum(city["weight"] for city in MOROCCAN_CITIES)
    distribution = []
    
    remaining = total_atms
    for i, city in enumerate(MOROCCAN_CITIES):
        if i == len(MOROCCAN_CITIES) - 1:
            count = remaining
        else:
            count = int(total_atms * city["weight"] / total_weight)
            remaining -= count
        distribution.append({"city": city, "count": count})
    
    return distribution


def seed_atm_data():
    """Initialise la base de données avec les 4577 ATM"""
    print("🏦 Initialisation des 4577 ATM des 5 banques partenaires...")
    
    db = get_db_direct()
    if db is None:
        return False
    
    # Créer les sources
    source_id = seed_sources(db)
    
    # Mettre à jour les banques
    seed_banks(db)
    
    # Supprimer les anciennes données ATM
    print("🗑️  Suppression des anciennes données ATM...")
    db.atm_locations.delete_many({})
    
    # Créer les index
    print("📊 Création des index géospatiaux...")
    db.atm_locations.create_index([("location", "2dsphere")])
    db.atm_locations.create_index([("bank_code", 1)])
    db.atm_locations.create_index([("city", 1)])
    db.atm_locations.create_index([("status", 1)])
    db.atm_locations.create_index([("atm_id", 1)], unique=True)
    
    all_atms = []
    global_index = 0
    
    for bank_code, config in BANKS_CONFIG.items():
        print(f"\n🏧 Génération de {config['atm_target']} ATM pour {config['name']}...")
        
        city_distribution = distribute_atms_by_city(config['atm_target'])
        bank_atms = []
        
        for dist in city_distribution:
            city_info = dist["city"]
            count = dist["count"]
            
            for i in range(count):
                global_index += 1
                atm = generate_atm(bank_code, city_info, global_index, source_id)
                bank_atms.append(atm)
        
        all_atms.extend(bank_atms)
        print(f"   ✓ {len(bank_atms)} ATM générés pour {config['name']}")
    
    # Insertion en batch
    print(f"\n💾 Insertion de {len(all_atms)} ATM dans MongoDB...")
    
    batch_size = 500
    for i in range(0, len(all_atms), batch_size):
        batch = all_atms[i:i+batch_size]
        db.atm_locations.insert_many(batch)
        print(f"   ✓ Batch {i//batch_size + 1}/{(len(all_atms) + batch_size - 1)//batch_size} inséré")
    
    # Statistiques finales
    print("\n" + "="*60)
    print("📊 STATISTIQUES FINALES")
    print("="*60)
    
    total = db.atm_locations.count_documents({})
    print(f"\n🏧 Total ATM insérés: {total}")
    
    print("\n📍 Répartition par banque:")
    for bank_code, config in BANKS_CONFIG.items():
        count = db.atm_locations.count_documents({"bank_code": bank_code})
        target = config['atm_target']
        status = "✅" if count == target else "⚠️"
        print(f"   {status} {config['name']}: {count}/{target} ATM")
    
    print("\n🏙️ Top 10 villes:")
    city_pipeline = [
        {"$group": {"_id": "$city", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    for city in db.atm_locations.aggregate(city_pipeline):
        print(f"   • {city['_id']}: {city['count']} ATM")
    
    print("\n✅ Initialisation terminée avec succès!")
    return True


if __name__ == "__main__":
    seed_atm_data()
