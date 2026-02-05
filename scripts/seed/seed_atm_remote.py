#!/usr/bin/env python3
"""Script pour seeder 4577 ATMs sur le serveur de production"""
import os
import random
from datetime import datetime
from pymongo import MongoClient

BANKS_CONFIG = {
    "attijariwafa": {"name": "Attijariwafa Bank", "atm_target": 1242, "prefix": "ATW"},
    "boa": {"name": "Bank of Africa", "atm_target": 660, "prefix": "BOA"},
    "banque_populaire": {"name": "Banque Populaire", "atm_target": 1800, "prefix": "BCP"},
    "cih": {"name": "CIH Bank", "atm_target": 626, "prefix": "CIH"},
    "bmci": {"name": "BMCI", "atm_target": 249, "prefix": "BMC"}
}

MOROCCAN_CITIES = [
    {"city": "Casablanca", "lat": 33.5731, "lon": -7.5898, "weight": 18, "districts": ["Maarif", "Anfa", "Centre Ville", "Hay Hassani", "Ain Sebaa", "Sidi Belyout", "Bernoussi"]},
    {"city": "Rabat", "lat": 34.0209, "lon": -6.8416, "weight": 10, "districts": ["Agdal", "Hassan", "Hay Riad", "Souissi", "Ocean"]},
    {"city": "Marrakech", "lat": 31.6295, "lon": -7.9811, "weight": 8, "districts": ["Gueliz", "Hivernage", "Medina", "Palmeraie"]},
    {"city": "Fes", "lat": 34.0181, "lon": -5.0078, "weight": 6, "districts": ["Ville Nouvelle", "Medina", "Saiss"]},
    {"city": "Tanger", "lat": 35.7595, "lon": -5.8340, "weight": 5, "districts": ["Centre Ville", "Malabata", "Medina"]},
    {"city": "Agadir", "lat": 30.4278, "lon": -9.5981, "weight": 4, "districts": ["Centre Ville", "Talborjt", "Founty"]},
    {"city": "Meknes", "lat": 33.8935, "lon": -5.5473, "weight": 3, "districts": ["Ville Nouvelle", "Medina"]},
    {"city": "Oujda", "lat": 34.6805, "lon": -1.9076, "weight": 3, "districts": ["Centre Ville", "Medina"]},
    {"city": "Kenitra", "lat": 34.2541, "lon": -6.5890, "weight": 2.5, "districts": ["Centre Ville", "Bir Rami"]},
    {"city": "Tetouan", "lat": 35.5785, "lon": -5.3684, "weight": 2, "districts": ["Centre Ville", "Medina"]},
    {"city": "El Jadida", "lat": 33.2316, "lon": -8.5007, "weight": 2, "districts": ["Centre Ville"]},
    {"city": "Mohammedia", "lat": 33.6861, "lon": -7.3828, "weight": 2, "districts": ["Centre Ville"]},
    {"city": "Safi", "lat": 32.2833, "lon": -9.2333, "weight": 1.5, "districts": ["Centre Ville"]},
    {"city": "Beni Mellal", "lat": 32.3373, "lon": -6.3498, "weight": 1.5, "districts": ["Centre Ville"]},
    {"city": "Nador", "lat": 35.1681, "lon": -2.9287, "weight": 1.5, "districts": ["Centre Ville"]},
    {"city": "Khouribga", "lat": 32.8811, "lon": -6.9063, "weight": 1, "districts": ["Centre Ville"]},
    {"city": "Settat", "lat": 33.0019, "lon": -7.6166, "weight": 1, "districts": ["Centre Ville"]},
    {"city": "Essaouira", "lat": 31.5085, "lon": -9.7595, "weight": 0.8, "districts": ["Centre Ville", "Medina"]},
    {"city": "Errachidia", "lat": 31.9314, "lon": -4.4267, "weight": 0.7, "districts": ["Centre Ville"]},
    {"city": "Ouarzazate", "lat": 30.9189, "lon": -6.8973, "weight": 0.6, "districts": ["Centre Ville"]},
]

LOCATION_TYPES = [
    {"type": "branch", "weight": 45},
    {"type": "mall", "weight": 15},
    {"type": "supermarket", "weight": 10},
    {"type": "station", "weight": 8},
    {"type": "standalone", "weight": 22},
]

def generate_coordinates(base_lat, base_lon, radius_km=5):
    lat_offset = random.uniform(-radius_km/111, radius_km/111)
    lon_offset = random.uniform(-radius_km/111, radius_km/111)
    return round(base_lat + lat_offset, 6), round(base_lon + lon_offset, 6)

def select_weighted(options):
    total = sum(o["weight"] for o in options)
    r = random.uniform(0, total)
    cumulative = 0
    for option in options:
        cumulative += option["weight"]
        if r <= cumulative:
            return option
    return options[-1]

def generate_atm(bank_code, city_info, index, source_id):
    city = city_info["city"]
    district = random.choice(city_info["districts"])
    location_type = select_weighted(LOCATION_TYPES)
    lat, lon = generate_coordinates(city_info["lat"], city_info["lon"])
    bank_name = BANKS_CONFIG[bank_code]["name"].split()[0]
    prefix = BANKS_CONFIG[bank_code]["prefix"]
    
    services = random.choice([
        ["withdrawal", "balance"],
        ["withdrawal", "deposit", "balance"],
        ["withdrawal", "balance", "transfer"],
    ])
    
    return {
        "atm_id": f"{prefix}_{city[:3].upper()}_{index:05d}",
        "bank_code": bank_code,
        "name": f"ATM {bank_name} {district}",
        "address": f"Rue Mohammed V, {district}, {city}",
        "city": city,
        "district": district,
        "location": {"type": "Point", "coordinates": [lon, lat]},
        "location_type": location_type["type"],
        "services": services,
        "available_24h": random.random() < 0.7,
        "has_wheelchair_access": random.random() < 0.6,
        "has_nfc": random.random() < 0.4,
        "status": "active",
        "source_id": source_id,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }

def main():
    mongo_uri = os.environ.get("MONGO_URI")
    client = MongoClient(mongo_uri)
    db = client.SarfX_Enhanced
    
    print("Initialisation des 4577 ATM...")
    
    db.atm_locations.delete_many({})
    print("Anciennes donnees supprimees")
    
    db.atm_locations.create_index([("location", "2dsphere")])
    db.atm_locations.create_index([("bank_code", 1)])
    db.atm_locations.create_index([("city", 1)])
    db.atm_locations.create_index([("atm_id", 1)], unique=True)
    
    source_id = "SRC_SEED_2026"
    all_atms = []
    global_index = 0
    total_weight = sum(c["weight"] for c in MOROCCAN_CITIES)
    
    for bank_code, config in BANKS_CONFIG.items():
        target = config["atm_target"]
        bank_atms = []
        
        for city_info in MOROCCAN_CITIES:
            city_count = int(target * city_info["weight"] / total_weight)
            for i in range(city_count):
                global_index += 1
                atm = generate_atm(bank_code, city_info, global_index, source_id)
                bank_atms.append(atm)
        
        all_atms.extend(bank_atms)
        print(f"  {config['name']}: {len(bank_atms)} ATM")
    
    batch_size = 500
    for i in range(0, len(all_atms), batch_size):
        db.atm_locations.insert_many(all_atms[i:i+batch_size])
    
    print(f"\nTotal insere: {db.atm_locations.count_documents({})}")
    
    for bank_code, config in BANKS_CONFIG.items():
        count = db.atm_locations.count_documents({"bank_code": bank_code})
        print(f"  {config['name']}: {count}")
    
    print("\nDone!")

if __name__ == "__main__":
    main()
