from pymongo import MongoClient
from flask import current_app, g, session
from bson import ObjectId
from bson.errors import InvalidId
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

def safe_object_id(id_str):
    """Convertit une chaîne en ObjectId de manière sécurisée"""
    if id_str is None:
        return None
    if isinstance(id_str, ObjectId):
        return id_str
    try:
        return ObjectId(id_str)
    except (InvalidId, TypeError):
        return None

def get_current_user_from_session():
    """Récupère l'utilisateur connecté de manière sécurisée"""
    if 'user_id' not in session:
        return None
    db = get_db()
    if db is None:
        return None
    
    user_id = safe_object_id(session['user_id'])
    if user_id:
        return db.users.find_one({"_id": user_id})
    # Fallback par email
    if 'email' in session:
        return db.users.find_one({"email": session['email']})
    return None

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