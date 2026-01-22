"""
Service de gestion des distributeurs automatiques (ATM) des banques partenaires
Inclut la géolocalisation et le calcul de distance
"""

from pymongo import ASCENDING
from bson import ObjectId
import math
from datetime import datetime


class ATMService:
    """Service pour gérer les ATM et calculer les distances"""
    
    def __init__(self, db):
        """
        Initialise le service ATM avec la connexion à la base de données
        
        Args:
            db: Instance de la base de données MongoDB
        """
        self.db = db
        self.atms = db.atm_locations
        
        # Créer les index pour optimiser les requêtes géospatiales
        try:
            self.atms.create_index([("location", "2dsphere")])
            self.atms.create_index([("bank_code", ASCENDING)])
            self.atms.create_index([("city", ASCENDING)])
        except Exception as e:
            print(f"Index déjà créés ou erreur: {e}")
    
    def calculate_distance(self, lat1, lon1, lat2, lon2):
        """
        Calcule la distance entre deux points GPS en kilomètres (formule Haversine)
        
        Args:
            lat1, lon1: Latitude et longitude du point 1
            lat2, lon2: Latitude et longitude du point 2
            
        Returns:
            float: Distance en kilomètres
        """
        # Rayon de la Terre en kilomètres
        R = 6371
        
        # Convertir en radians
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        # Formule Haversine
        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = R * c
        
        return round(distance, 2)
    
    def get_all_banks(self):
        """
        Récupère la liste de toutes les banques partenaires
        
        Returns:
            list: Liste des banques avec leurs informations
        """
        banks = [
            {
                "code": "attijariwafa",
                "name": "Attijariwafa Bank",
                "name_ar": "التجاري وفا بنك",
                "logo": "/static/images/banks/attijariwafa.svg",
                "color": "#E30613",
                "website": "https://www.attijariwafabank.com"
            },
            {
                "code": "boa",
                "name": "Bank of Africa",
                "name_ar": "بنك أفريقيا",
                "logo": "/static/images/banks/boa.svg",
                "color": "#00843D",
                "website": "https://www.bankofafrica.ma"
            },
            {
                "code": "banque_populaire",
                "name": "Banque Populaire",
                "name_ar": "البنك الشعبي",
                "logo": "/static/images/banks/banque-populaire.svg",
                "color": "#005BAA",
                "website": "https://www.gbp.ma"
            },
            {
                "code": "cih",
                "name": "CIH Bank",
                "name_ar": "بنك القرض العقاري والسياحي",
                "logo": "/static/images/banks/cih.svg",
                "color": "#C41E3A",
                "website": "https://www.cih.co.ma"
            },
            {
                "code": "albarid",
                "name": "Al Barid Bank",
                "name_ar": "بنك البريد",
                "logo": "/static/images/banks/albarid.svg",
                "color": "#FFD700",
                "website": "https://www.albaridbank.ma"
            },
            {
                "code": "bmci",
                "name": "BMCI",
                "name_ar": "البنك المغربي للتجارة والصناعة",
                "logo": "/static/images/banks/bmci.svg",
                "color": "#DC0032",
                "website": "https://www.bmci.ma"
            }
        ]
        
        # Ajouter le nombre d'ATM pour chaque banque
        for bank in banks:
            bank['atm_count'] = self.atms.count_documents({"bank_code": bank['code']})
        
        return banks
    
    def get_bank_by_code(self, bank_code):
        """
        Récupère les informations d'une banque par son code
        
        Args:
            bank_code: Code de la banque
            
        Returns:
            dict: Informations de la banque ou None
        """
        banks = self.get_all_banks()
        for bank in banks:
            if bank['code'] == bank_code:
                return bank
        return None
    
    def get_atms_by_bank(self, bank_code, limit=50):
        """
        Récupère tous les ATM d'une banque spécifique
        
        Args:
            bank_code: Code de la banque
            limit: Nombre maximum d'ATM à retourner
            
        Returns:
            list: Liste des ATM
        """
        try:
            atms = list(self.atms.find(
                {"bank_code": bank_code, "status": "active"},
                {"_id": 0}
            ).limit(limit))
            
            return atms
        except Exception as e:
            print(f"Erreur lors de la récupération des ATM: {e}")
            return []
    
    def get_atms_by_city(self, city, bank_code=None):
        """
        Récupère les ATM d'une ville spécifique
        
        Args:
            city: Nom de la ville
            bank_code: Code de la banque (optionnel)
            
        Returns:
            list: Liste des ATM
        """
        try:
            query = {"city": city, "status": "active"}
            if bank_code:
                query["bank_code"] = bank_code
            
            atms = list(self.atms.find(query, {"_id": 0}))
            return atms
        except Exception as e:
            print(f"Erreur lors de la récupération des ATM par ville: {e}")
            return []
    
    def get_nearest_atms(self, latitude, longitude, bank_code=None, max_distance_km=10, limit=10):
        """
        Trouve les ATM les plus proches d'une position GPS
        
        Args:
            latitude: Latitude de l'utilisateur
            longitude: Longitude de l'utilisateur
            bank_code: Code de la banque (optionnel)
            max_distance_km: Distance maximale en kilomètres
            limit: Nombre maximum d'ATM à retourner
            
        Returns:
            list: Liste des ATM triés par distance
        """
        try:
            # Requête de proximité géospatiale
            query = {
                "location": {
                    "$near": {
                        "$geometry": {
                            "type": "Point",
                            "coordinates": [longitude, latitude]
                        },
                        "$maxDistance": max_distance_km * 1000  # Convertir km en mètres
                    }
                },
                "status": "active"
            }
            
            if bank_code:
                query["bank_code"] = bank_code
            
            atms = list(self.atms.find(query, {"_id": 0}).limit(limit))
            
            # Calculer la distance exacte pour chaque ATM
            for atm in atms:
                coords = atm.get('location', {}).get('coordinates', [])
                if len(coords) == 2:
                    atm_lon, atm_lat = coords
                    distance = self.calculate_distance(latitude, longitude, atm_lat, atm_lon)
                    atm['distance_km'] = distance
                    
                    # Ajouter un temps de trajet estimé (3 km/h à pied, 30 km/h en ville)
                    atm['walk_time_min'] = round(distance * 20)  # ~3 km/h
                    atm['drive_time_min'] = round(distance * 2)  # ~30 km/h
            
            return atms
            
        except Exception as e:
            print(f"Erreur lors de la recherche des ATM proches: {e}")
            return []
    
    def get_atm_by_id(self, atm_id):
        """
        Récupère un ATM spécifique par son ID
        
        Args:
            atm_id: ID de l'ATM
            
        Returns:
            dict: Informations de l'ATM ou None
        """
        try:
            atm = self.atms.find_one({"atm_id": atm_id}, {"_id": 0})
            return atm
        except Exception as e:
            print(f"Erreur lors de la récupération de l'ATM: {e}")
            return None
    
    def add_atm(self, atm_data):
        """
        Ajoute un nouvel ATM à la base de données
        
        Args:
            atm_data: Dictionnaire contenant les informations de l'ATM
            
        Returns:
            dict: ATM créé avec son ID
        """
        try:
            # Générer un ID unique
            from datetime import datetime
            atm_data['atm_id'] = f"ATM_{atm_data['bank_code']}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            atm_data['created_at'] = datetime.now()
            atm_data['status'] = atm_data.get('status', 'active')
            
            # Valider la structure de location
            if 'location' in atm_data:
                if 'coordinates' not in atm_data['location']:
                    raise ValueError("Le champ 'coordinates' est requis dans 'location'")
                atm_data['location']['type'] = 'Point'
            
            result = self.atms.insert_one(atm_data)
            atm_data['_id'] = str(result.inserted_id)
            
            return atm_data
        except Exception as e:
            print(f"Erreur lors de l'ajout de l'ATM: {e}")
            return None
    
    def update_atm(self, atm_id, update_data):
        """
        Met à jour les informations d'un ATM
        
        Args:
            atm_id: ID de l'ATM
            update_data: Données à mettre à jour
            
        Returns:
            bool: True si la mise à jour a réussi
        """
        try:
            update_data['updated_at'] = datetime.now()
            result = self.atms.update_one(
                {"atm_id": atm_id},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Erreur lors de la mise à jour de l'ATM: {e}")
            return False
    
    def delete_atm(self, atm_id):
        """
        Supprime un ATM (désactivation soft)
        
        Args:
            atm_id: ID de l'ATM
            
        Returns:
            bool: True si la suppression a réussi
        """
        try:
            result = self.atms.update_one(
                {"atm_id": atm_id},
                {"$set": {"status": "inactive", "deleted_at": datetime.now()}}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Erreur lors de la suppression de l'ATM: {e}")
            return False
    
    def search_atms(self, search_term, bank_code=None):
        """
        Recherche des ATM par nom, adresse ou ville
        
        Args:
            search_term: Terme de recherche
            bank_code: Code de la banque (optionnel)
            
        Returns:
            list: Liste des ATM correspondants
        """
        try:
            query = {
                "$or": [
                    {"name": {"$regex": search_term, "$options": "i"}},
                    {"address": {"$regex": search_term, "$options": "i"}},
                    {"city": {"$regex": search_term, "$options": "i"}},
                    {"district": {"$regex": search_term, "$options": "i"}}
                ],
                "status": "active"
            }
            
            if bank_code:
                query["bank_code"] = bank_code
            
            atms = list(self.atms.find(query, {"_id": 0}).limit(20))
            return atms
        except Exception as e:
            print(f"Erreur lors de la recherche d'ATM: {e}")
            return []
    
    def get_cities_with_atms(self, bank_code=None):
        """
        Récupère la liste des villes avec des ATM
        
        Args:
            bank_code: Code de la banque (optionnel)
            
        Returns:
            list: Liste des villes avec le nombre d'ATM
        """
        try:
            match_query = {"status": "active"}
            if bank_code:
                match_query["bank_code"] = bank_code
            
            pipeline = [
                {"$match": match_query},
                {"$group": {
                    "_id": "$city",
                    "count": {"$sum": 1}
                }},
                {"$sort": {"count": -1}}
            ]
            
            cities = list(self.atms.aggregate(pipeline))
            return [{"city": c["_id"], "atm_count": c["count"]} for c in cities]
        except Exception as e:
            print(f"Erreur lors de la récupération des villes: {e}")
            return []
