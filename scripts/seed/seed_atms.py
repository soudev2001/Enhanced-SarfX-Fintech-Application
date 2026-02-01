"""
Script pour initialiser les 4577 ATM des 5 banques partenaires marocaines
Sans modifier les données des banques existantes

Répartition: Attijari (1242), BOA (660), Chaabi (1800), CIH (626), BMCI (249)
Exécuter avec: python seed_atms.py
"""

import os
import random
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from pymongo import MongoClient
import certifi
from dotenv import load_dotenv

load_dotenv()


# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class BankConfig:
    """Configuration d'une banque partenaire"""
    code: str
    name: str
    atm_target: int
    prefix: str


@dataclass
class CityConfig:
    """Configuration d'une ville"""
    name: str
    lat: float
    lon: float
    weight: float
    districts: List[str] = field(default_factory=list)


@dataclass
class LocationType:
    """Type de lieu pour ATM"""
    type: str
    label: str
    weight: int


# Configuration des banques
BANKS = [
    BankConfig("attijariwafa", "Attijariwafa Bank", 1242, "ATW"),
    BankConfig("boa", "Bank of Africa", 660, "BOA"),
    BankConfig("banque_populaire", "Banque Populaire", 1800, "BCP"),
    BankConfig("cih", "CIH Bank", 626, "CIH"),
    BankConfig("bmci", "BMCI", 249, "BMC"),
]

# Types de lieux
LOCATION_TYPES = [
    LocationType("branch", "Agence", 45),
    LocationType("mall", "Centre Commercial", 15),
    LocationType("supermarket", "Supermarché", 10),
    LocationType("station", "Station Service", 8),
    LocationType("hospital", "Hôpital/Clinique", 5),
    LocationType("university", "Université", 5),
    LocationType("airport", "Aéroport", 2),
    LocationType("train_station", "Gare", 3),
    LocationType("hotel", "Hôtel", 4),
    LocationType("standalone", "Kiosque", 3),
]

# Services disponibles
SERVICES_OPTIONS = [
    ["withdrawal", "balance"],
    ["withdrawal", "deposit", "balance"],
    ["withdrawal", "balance", "transfer"],
    ["withdrawal", "deposit", "balance", "transfer"],
    ["withdrawal", "deposit", "balance", "transfer", "bill_payment"],
]

# Villes marocaines
CITIES = [
    # Grandes métropoles (35%)
    CityConfig("Casablanca", 33.5731, -7.5898, 18, [
        "Maarif", "Anfa", "Gauthier", "Bourgogne", "Centre Ville", "Hay Hassani",
        "Sidi Belyout", "Ain Chock", "Ain Sebaa", "Ben M'sick", "Bernoussi",
        "Sidi Moumen", "Sbata", "Roches Noires", "Derb Sultan", "Habous",
        "Mers Sultan", "2 Mars", "Oulfa", "Hay Mohammadi"
    ]),
    CityConfig("Rabat", 34.0209, -6.8416, 10, [
        "Agdal", "Hassan", "Hay Riad", "Souissi", "Yacoub El Mansour",
        "Akkari", "Océan", "Médina", "Takaddoum", "Youssoufia", "Temara", "Salé Centre"
    ]),
    CityConfig("Marrakech", 31.6295, -7.9811, 8, [
        "Guéliz", "Hivernage", "Médina", "Palmeraie", "Targa", "Semlalia",
        "Daoudiate", "M'hamid", "Sidi Youssef Ben Ali", "Massira", "Ménara", "Annakhil"
    ]),

    # Grandes villes (25%)
    CityConfig("Fès", 34.0181, -5.0078, 6, [
        "Ville Nouvelle", "Médina", "Saiss", "Narjiss", "Mont Fleuri",
        "Adarissa", "Zouagha", "Dhar El Mahraz", "Oued Fès"
    ]),
    CityConfig("Tanger", 35.7595, -5.8340, 5, [
        "Centre Ville", "Malabata", "Médina", "Moujahidine", "Marshan",
        "Beni Makada", "Val Fleuri", "Tanger City Center", "Iberia", "Souani"
    ]),
    CityConfig("Agadir", 30.4278, -9.5981, 4, [
        "Centre Ville", "Talborjt", "Hay Mohammadi", "Founty", "Tikouine",
        "Charaf", "Dakhla", "Tilila", "Agadir Oufella"
    ]),
    CityConfig("Meknès", 33.8935, -5.5473, 3, [
        "Ville Nouvelle", "Médina", "Hamria", "Marjane", "Zitoune", "Rouamzine"
    ]),
    CityConfig("Oujda", 34.6805, -1.9076, 3, [
        "Centre Ville", "Médina", "Lazaret", "Hay Al Andalous", "Si Kaddour"
    ]),

    # Villes moyennes (20%)
    CityConfig("Kenitra", 34.2541, -6.5890, 2.5, [
        "Centre Ville", "Bir Rami", "Oulad Oujih", "Maamora", "Mehdia"
    ]),
    CityConfig("Tétouan", 35.5785, -5.3684, 2, [
        "Centre Ville", "Médina", "Martil", "M'diq", "Touabel"
    ]),
    CityConfig("El Jadida", 33.2316, -8.5007, 2, [
        "Centre Ville", "Cité Portugaise", "Hay Essalam", "Sidi Bouzid"
    ]),
    CityConfig("Safi", 32.2833, -9.2333, 1.5, [
        "Centre Ville", "Médina", "Jrifate", "Sidi Bouzid"
    ]),
    CityConfig("Mohammedia", 33.6861, -7.3828, 2, [
        "Centre Ville", "Alia", "Hassania", "Palmier"
    ]),
    CityConfig("Béni Mellal", 32.3373, -6.3498, 1.5, [
        "Centre Ville", "Hay Al Qods", "Ouled M'Barek"
    ]),
    CityConfig("Nador", 35.1681, -2.9287, 1.5, [
        "Centre Ville", "Selouane", "Al Aaroui"
    ]),
    CityConfig("Khouribga", 32.8811, -6.9063, 1, [
        "Centre Ville", "Hay Al Qods", "Hay Riad"
    ]),

    # Petites villes (20%)
    CityConfig("Settat", 33.0019, -7.6166, 1, ["Centre Ville", "Hay Salam"]),
    CityConfig("Taza", 34.2100, -4.0100, 0.8, ["Centre Ville", "Médina"]),
    CityConfig("Errachidia", 31.9314, -4.4267, 0.7, ["Centre Ville", "Hay Riad"]),
    CityConfig("Essaouira", 31.5085, -9.7595, 0.8, ["Centre Ville", "Médina"]),
    CityConfig("Khémisset", 33.8242, -6.0661, 0.7, ["Centre Ville"]),
    CityConfig("Larache", 35.1932, -6.1561, 0.7, ["Centre Ville", "Médina"]),
    CityConfig("Ksar El Kébir", 35.0000, -5.9000, 0.6, ["Centre Ville"]),
    CityConfig("Guelmim", 28.9870, -10.0574, 0.5, ["Centre Ville"]),
    CityConfig("Ouarzazate", 30.9189, -6.8973, 0.6, ["Centre Ville", "Tabounte"]),
    CityConfig("Al Hoceima", 35.2517, -3.9372, 0.7, ["Centre Ville", "Calabonita"]),
    CityConfig("Berkane", 34.9167, -2.3167, 0.5, ["Centre Ville"]),
    CityConfig("Taourirt", 34.4167, -2.8833, 0.4, ["Centre Ville"]),
    CityConfig("Dakhla", 23.6848, -15.9579, 0.4, ["Centre Ville", "Port"]),
    CityConfig("Laayoune", 27.1536, -13.2033, 0.5, ["Centre Ville", "Hay Al Wahda"]),
    CityConfig("Tan-Tan", 28.4378, -11.1033, 0.3, ["Centre Ville"]),
    CityConfig("Tiznit", 29.7000, -9.7333, 0.4, ["Centre Ville", "Médina"]),
    CityConfig("Taroudant", 30.4706, -8.8769, 0.4, ["Centre Ville", "Médina"]),
    CityConfig("Chefchaouen", 35.1688, -5.2636, 0.4, ["Centre Ville", "Médina"]),
    CityConfig("Ifrane", 33.5333, -5.1000, 0.3, ["Centre Ville"]),
    CityConfig("Azrou", 33.4333, -5.2167, 0.3, ["Centre Ville"]),
]


# ============================================================================
# DATABASE
# ============================================================================

class Database:
    """Gestionnaire de connexion MongoDB"""

    def __init__(self):
        self.client: Optional[MongoClient] = None
        self.db = None

    def connect(self) -> bool:
        """Établit la connexion à MongoDB"""
        try:
            mongo_uri = os.getenv('MONGO_URI')
            if not mongo_uri:
                print("❌ MONGO_URI non défini dans .env")
                return False

            # Extraire le nom de la DB
            db_name = 'SarfX_Enhanced'
            if '/' in mongo_uri:
                potential_db = mongo_uri.split('/')[-1].split('?')[0]
                if potential_db:
                    db_name = potential_db

            print(f"🔗 Connexion à MongoDB Atlas...")
            self.client = MongoClient(
                mongo_uri,
                tlsCAFile=certifi.where(),
                serverSelectionTimeoutMS=10000
            )
            self.client.server_info()
            self.db = self.client[db_name]
            print(f"✅ Connexion réussie: {db_name}")
            return True

        except Exception as e:
            print(f"❌ Erreur de connexion: {e}")
            return False

    def close(self):
        """Ferme la connexion"""
        if self.client:
            self.client.close()


# ============================================================================
# ATM GENERATOR
# ============================================================================

class ATMGenerator:
    """Générateur d'ATM"""

    MALLS = ["Morocco Mall", "Marjane", "Carrefour", "Aswak Assalam", "Acima"]
    STATIONS = ["Shell", "Afriquia", "Total", "Winxo", "Ziz"]
    STREET_TYPES = ["Avenue", "Boulevard", "Rue", "Place"]
    STREET_NAMES = [
        "Mohammed V", "Hassan II", "Mohammed VI", "Moulay Youssef", "FAR",
        "Allal Ben Abdallah", "Zerktouni", "Abdelmoumen", "Massira", "Al Qods",
        "Palestine", "Nations Unies", "France", "Fès", "Marrakech"
    ]
    HOURS = ["08:00 - 18:00", "08:00 - 20:00", "09:00 - 19:00", "08:30 - 16:30"]

    def __init__(self, source_id: str):
        self.source_id = source_id
        self.global_index = 0

    @staticmethod
    def _weighted_choice(options: list, weight_attr: str = "weight"):
        """Sélection pondérée"""
        total = sum(getattr(o, weight_attr) if hasattr(o, weight_attr) else o[weight_attr]
                    for o in options)
        r = random.uniform(0, total)
        cumulative = 0
        for option in options:
            weight = getattr(option, weight_attr) if hasattr(option, weight_attr) else option[weight_attr]
            cumulative += weight
            if r <= cumulative:
                return option
        return options[-1]

    @staticmethod
    def _random_coords(base_lat: float, base_lon: float, radius_km: float = 5) -> tuple:
        """Génère des coordonnées aléatoires autour d'un point"""
        lat_offset = random.uniform(-radius_km/111, radius_km/111)
        lon_offset = random.uniform(-radius_km/111, radius_km/111)
        return round(base_lat + lat_offset, 6), round(base_lon + lon_offset, 6)

    def _generate_name(self, bank: BankConfig, loc_type: LocationType,
                       city: CityConfig, district: str) -> str:
        """Génère un nom d'ATM réaliste"""
        bank_short = bank.name.split()[0]

        if loc_type.type == "branch":
            return f"ATM {bank_short} {district}"
        elif loc_type.type == "mall":
            return f"ATM {bank_short} {random.choice(self.MALLS)} {city.name}"
        elif loc_type.type == "station":
            return f"ATM {bank_short} Station {random.choice(self.STATIONS)}"
        elif loc_type.type == "airport":
            return f"ATM {bank_short} Aéroport {city.name}"
        elif loc_type.type == "train_station":
            return f"ATM {bank_short} Gare {city.name}"
        else:
            return f"ATM {bank_short} {district} {self.global_index}"

    def _generate_address(self, loc_type: LocationType, city: CityConfig, district: str) -> str:
        """Génère une adresse réaliste"""
        if loc_type.type == "branch":
            return f"{random.choice(self.STREET_TYPES)} {random.choice(self.STREET_NAMES)}, {district}"
        elif loc_type.type == "mall":
            return f"Centre Commercial, {district}, {city.name}"
        else:
            return f"{random.choice(self.STREET_TYPES)} {random.choice(self.STREET_NAMES)}, {district}, {city.name}"

    def generate(self, bank: BankConfig, city: CityConfig) -> Dict:
        """Génère un ATM complet"""
        self.global_index += 1

        district = random.choice(city.districts)
        loc_type = self._weighted_choice(LOCATION_TYPES)
        lat, lon = self._random_coords(city.lat, city.lon)
        services = random.choice(SERVICES_OPTIONS)
        is_24h = random.random() < 0.7

        atm = {
            "atm_id": f"{bank.prefix}_{city.name[:3].upper()}_{self.global_index:05d}",
            "bank_code": bank.code,
            "name": self._generate_name(bank, loc_type, city, district),
            "address": self._generate_address(loc_type, city, district),
            "city": city.name,
            "district": district,
            "location": {
                "type": "Point",
                "coordinates": [lon, lat]
            },
            "location_type": loc_type.type,
            "services": services,
            "available_24h": is_24h,
            "has_wheelchair_access": random.random() < 0.6,
            "has_nfc": random.random() < 0.4,
            "has_deposit": "deposit" in services,
            "status": "active",
            "source_id": self.source_id,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }

        if not is_24h:
            atm["hours"] = random.choice(self.HOURS)

        return atm


# ============================================================================
# SEEDER
# ============================================================================

class ATMSeeder:
    """Classe principale pour le seeding des ATM"""

    def __init__(self, db: Database):
        self.db = db.db
        self.source_id = f"SRC_SEED_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.generator = ATMGenerator(self.source_id)

    def _create_source(self) -> str:
        """Crée l'entrée source pour traçabilité"""
        source = {
            "source_id": self.source_id,
            "type": "seed_script",
            "name": "Import ATM banques partenaires",
            "description": "Données des 4577 ATM des 5 banques partenaires",
            "banks": [b.code for b in BANKS],
            "total_atms": sum(b.atm_target for b in BANKS),
            "imported_at": datetime.now(),
            "imported_by": "system",
            "status": "completed"
        }
        self.db.sources.insert_one(source)
        print(f"✅ Source créée: {self.source_id}")
        return self.source_id

    def _create_indexes(self):
        """Crée les index nécessaires"""
        print("📊 Création des index...")
        self.db.atm_locations.create_index([("location", "2dsphere")])
        self.db.atm_locations.create_index([("bank_code", 1)])
        self.db.atm_locations.create_index([("city", 1)])
        self.db.atm_locations.create_index([("status", 1)])
        self.db.atm_locations.create_index([("atm_id", 1)], unique=True)
        print("✅ Index créés")

    def _distribute_by_city(self, total: int) -> List[Dict]:
        """Distribue les ATM selon le poids des villes"""
        total_weight = sum(c.weight for c in CITIES)
        distribution = []
        remaining = total

        for i, city in enumerate(CITIES):
            if i == len(CITIES) - 1:
                count = remaining
            else:
                count = int(total * city.weight / total_weight)
                remaining -= count
            distribution.append({"city": city, "count": count})

        return distribution

    def _generate_bank_atms(self, bank: BankConfig) -> List[Dict]:
        """Génère tous les ATM d'une banque"""
        print(f"\n🏧 Génération de {bank.atm_target} ATM pour {bank.name}...")

        distribution = self._distribute_by_city(bank.atm_target)
        atms = []

        for dist in distribution:
            for _ in range(dist["count"]):
                atm = self.generator.generate(bank, dist["city"])
                atms.append(atm)

        print(f"   ✓ {len(atms)} ATM générés")
        return atms

    def _insert_batch(self, atms: List[Dict], batch_size: int = 500):
        """Insère les ATM par batch"""
        total = len(atms)
        print(f"\n💾 Insertion de {total} ATM...")

        for i in range(0, total, batch_size):
            batch = atms[i:i+batch_size]
            self.db.atm_locations.insert_many(batch)
            batch_num = i // batch_size + 1
            total_batches = (total + batch_size - 1) // batch_size
            print(f"   ✓ Batch {batch_num}/{total_batches}")

    def _print_stats(self):
        """Affiche les statistiques finales"""
        print("\n" + "=" * 60)
        print("📊 STATISTIQUES FINALES")
        print("=" * 60)

        total = self.db.atm_locations.count_documents({})
        print(f"\n🏧 Total ATM: {total}")

        print("\n📍 Par banque:")
        for bank in BANKS:
            count = self.db.atm_locations.count_documents({"bank_code": bank.code})
            status = "✅" if count == bank.atm_target else "⚠️"
            print(f"   {status} {bank.name}: {count}/{bank.atm_target}")

        print("\n🏙️ Top 10 villes:")
        pipeline = [
            {"$group": {"_id": "$city", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        for city in self.db.atm_locations.aggregate(pipeline):
            print(f"   • {city['_id']}: {city['count']} ATM")

    def run(self, clear_existing: bool = True):
        """Exécute le seeding complet"""
        print("🏦 Initialisation des ATM (sans toucher aux banques)...")
        print(f"   Total prévu: {sum(b.atm_target for b in BANKS)} ATM")

        # Créer la source
        self._create_source()

        # Supprimer les anciennes données si demandé
        if clear_existing:
            print("\n🗑️  Suppression des anciennes données ATM...")
            result = self.db.atm_locations.delete_many({})
            print(f"   ✓ {result.deleted_count} ATM supprimés")

        # Créer les index
        self._create_indexes()

        # Générer et insérer les ATM par banque
        all_atms = []
        for bank in BANKS:
            atms = self._generate_bank_atms(bank)
            all_atms.extend(atms)

        # Insertion en batch
        self._insert_batch(all_atms)

        # Statistiques
        self._print_stats()

        print("\n✅ Seeding terminé avec succès!")
        return True


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Point d'entrée principal"""
    db = Database()

    if not db.connect():
        return False

    try:
        seeder = ATMSeeder(db)
        return seeder.run(clear_existing=True)
    finally:
        db.close()


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
