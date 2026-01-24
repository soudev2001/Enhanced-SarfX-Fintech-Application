#!/usr/bin/env python3
"""
Script de migration pour ajouter les nouveaux rôles utilisateurs
"""
import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

def migrate_user_roles():
    """Migre les rôles des utilisateurs existants"""
    
    # Connexion à MongoDB
    mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
    client = MongoClient(mongo_uri)
    db = client['sarfx']
    
    print("🔄 Démarrage de la migration des rôles utilisateurs...")
    
    # Mettre à jour les utilisateurs sans rôle
    result = db.users.update_many(
        {'role': {'$exists': False}},
        {'$set': {'role': 'user'}}
    )
    print(f"✅ {result.modified_count} utilisateurs mis à jour avec le rôle 'user'")
    
    # Créer des index pour optimiser les recherches
    db.users.create_index('role')
    db.users.create_index('bank_code')
    print("✅ Index créés pour 'role' et 'bank_code'")
    
    # Afficher les statistiques
    stats = {
        'user': db.users.count_documents({'role': 'user'}),
        'bank_user': db.users.count_documents({'role': 'bank_user'}),
        'admin': db.users.count_documents({'role': 'admin'}),
        'admin_sr_bank': db.users.count_documents({'role': 'admin_sr_bank'}),
        'admin_associate_bank': db.users.count_documents({'role': 'admin_associate_bank'})
    }
    
    print("\n📊 Statistiques des rôles:")
    for role, count in stats.items():
        print(f"   - {role}: {count}")
    
    print("\n✨ Migration terminée avec succès!")
    
    client.close()

def add_api_fields_to_banks():
    """Ajoute les champs API aux banques existantes"""
    
    mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
    client = MongoClient(mongo_uri)
    db = client['sarfx']
    
    print("\n🔄 Ajout des champs API aux banques...")
    
    result = db.banks.update_many(
        {'api_active': {'$exists': False}},
        {
            '$set': {
                'api_active': False,
                'api_key': None,
                'api_secret': None,
                'webhook_url': None,
                'api_rate_limit': 1000,
                'last_api_sync': None
            }
        }
    )
    
    print(f"✅ {result.modified_count} banques mises à jour")
    
    client.close()

def create_sample_admin_users():
    """Crée des utilisateurs admin de test"""
    
    mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
    client = MongoClient(mongo_uri)
    db = client['sarfx']
    
    print("\n🔄 Création d'utilisateurs admin de test...")
    
    # Admin SR Bank
    if not db.users.find_one({'email': 'admin.sr@sarfx.io'}):
        from werkzeug.security import generate_password_hash
        
        admin_sr = {
            'name': 'Admin SR Bank',
            'email': 'admin.sr@sarfx.io',
            'password': generate_password_hash('AdminSR123!'),
            'role': 'admin_sr_bank',
            'is_verified': True,
            'bank_code': None
        }
        db.users.insert_one(admin_sr)
        print("✅ Admin SR Bank créé (admin.sr@sarfx.io / AdminSR123!)")
    
    # Admin Associate Bank
    if not db.users.find_one({'email': 'admin.bank@sarfx.io'}):
        from werkzeug.security import generate_password_hash
        
        # Récupérer la première banque pour l'association
        first_bank = db.banks.find_one({})
        bank_code = first_bank['code'] if first_bank else None
        
        admin_associate = {
            'name': 'Admin Associate Bank',
            'email': 'admin.bank@sarfx.io',
            'password': generate_password_hash('AdminBank123!'),
            'role': 'admin_associate_bank',
            'is_verified': True,
            'bank_code': bank_code
        }
        db.users.insert_one(admin_associate)
        print(f"✅ Admin Associate Bank créé (admin.bank@sarfx.io / AdminBank123!) - Associé à: {bank_code or 'Aucune banque'}")
    
    client.close()

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Migration SarfX - Système de Rôles et API")
    print("=" * 60)
    
    try:
        migrate_user_roles()
        add_api_fields_to_banks()
        create_sample_admin_users()
        
        print("\n" + "=" * 60)
        print("✨ Toutes les migrations ont été effectuées avec succès!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Erreur lors de la migration: {e}")
        import traceback
        traceback.print_exc()
