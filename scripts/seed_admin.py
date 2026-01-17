import os
from dotenv import load_dotenv
from pymongo import MongoClient
from werkzeug.security import generate_password_hash

# Charger les variables d'environnement
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

client = MongoClient(MONGO_URI)
db = client.get_default_database()
users = db["users"]

# Vérifier si l'utilisateur admin existe déjà
admin = users.find_one({"email": ADMIN_EMAIL})
if admin:
    print("L'utilisateur admin existe déjà.")
else:
    hashed_password = generate_password_hash(ADMIN_PASSWORD)
    users.insert_one({
        "email": ADMIN_EMAIL,
        "password": hashed_password,
        "role": "admin",
        "is_active": True
    })
    print("Utilisateur admin créé avec succès.")

client.close()