"""
Seed Demo Users for SarfX
Creates demo accounts with different roles
"""
from pymongo import MongoClient
from werkzeug.security import generate_password_hash
from datetime import datetime
import os

def seed_demo_users():
    """Create demo users with different roles"""
    
    # Connect to MongoDB
    mongo_uri = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/sarfx')
    client = MongoClient(mongo_uri)
    db = client.get_default_database() if 'mongodb+srv' in mongo_uri or '/' in mongo_uri.split('@')[-1] else client['sarfx']
    
    demo_users = [
        {
            "email": "admin@sarfx.io",
            "password": generate_password_hash("admin123"),
            "name": "Admin SarfX",
            "role": "admin",
            "is_active": True,
            "is_verified": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "email": "bank@sarfx.io",
            "password": generate_password_hash("bank123"),
            "name": "Bank Manager",
            "role": "bank_admin",
            "is_active": True,
            "is_verified": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "email": "user@sarfx.io",
            "password": generate_password_hash("user123"),
            "name": "Demo User",
            "role": "user",
            "is_active": True,
            "is_verified": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    ]
    
    for user_data in demo_users:
        # Check if user already exists
        existing = db.users.find_one({"email": user_data["email"]})
        
        if existing:
            # Update existing user
            db.users.update_one(
                {"email": user_data["email"]},
                {"$set": {
                    "password": user_data["password"],
                    "role": user_data["role"],
                    "is_active": True,
                    "is_verified": True,
                    "updated_at": datetime.utcnow()
                }}
            )
            print(f"✅ Updated: {user_data['email']} ({user_data['role']})")
        else:
            # Create new user
            result = db.users.insert_one(user_data)
            user_id = str(result.inserted_id)
            
            # Create default wallet for user
            wallet = {
                "user_id": user_id,
                "balances": {
                    "USD": 1000.00,
                    "EUR": 500.00,
                    "MAD": 5000.00
                },
                "created_at": datetime.utcnow()
            }
            db.wallets.insert_one(wallet)
            
            print(f"✅ Created: {user_data['email']} ({user_data['role']})")
    
    print("\n🎉 Demo users seeded successfully!")
    print("\n📋 Demo Accounts:")
    print("   Admin:  admin@sarfx.io / admin123")
    print("   Bank:   bank@sarfx.io / bank123")
    print("   User:   user@sarfx.io / user123")

if __name__ == "__main__":
    seed_demo_users()
