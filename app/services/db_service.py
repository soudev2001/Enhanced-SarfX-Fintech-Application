from pymongo import MongoClient
from flask import current_app, g
import certifi # Nécessaire pour SSL sur certains environnements

def get_db():
    """
    Récupère ou crée une connexion MongoDB.
    Gère les erreurs de connexion SSL courantes sur le cloud.
    """
    if 'db' not in g:
        try:
            # Utilisation de certifi pour garantir les certificats SSL valides
            client = MongoClient(
                current_app.config['MONGO_URI'],
                tlsCAFile=certifi.where(),
                serverSelectionTimeoutMS=5000
            )
            g.db = client[current_app.config['DB_NAME']]
        except Exception as e:
            print(f"❌ CRITICAL DB ERROR: {e}")
            g.db = None
    return g.db

def close_db(e=None):
    """Ferme la connexion proprement"""
    db = g.pop('db', None)
    if db is not None:
        db.client.close()

def log_history(action, details, user="System"):
    """Enregistre une action dans l'historique"""
    db = get_db()
    if db is not None:
        from datetime import datetime
        try:
            db.history.insert_one({
                "action": action,
                "details": details,
                "user": user,
                "timestamp": datetime.utcnow()
            })
        except Exception as e:
            print(f"⚠️ Log failed: {e}")