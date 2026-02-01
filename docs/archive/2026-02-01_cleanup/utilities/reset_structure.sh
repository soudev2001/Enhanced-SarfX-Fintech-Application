#!/bin/bash

echo "⚠️  ATTENTION : Suppression de tout le contenu dans $(pwd)..."
echo "⏳ 3 secondes pour annuler (Ctrl+C)..."
sleep 3

# 1. Nettoyage (garde le script lui-même)
find . -maxdepth 1 ! -name 'reset_structure.sh' ! -name '.' -exec rm -rf {} +

echo "✅ Dossier vidé."
echo "🏗️  Création de la structure SarfX Enhanced..."

# 2. Création des dossiers principaux
mkdir -p "SarfX Backend"
mkdir -p "SarfX Mobile App"
mkdir -p "documentation"

# 3. Création de l'arborescence Backend (Flask)
mkdir -p "app/services"
mkdir -p "app/routes"
mkdir -p "app/static/css"
mkdir -p "app/templates"

# 4. Création des fichiers à la racine
touch .env.example
touch requirements.txt
touch run.py

# 5. Fichiers SarfX Backend
touch "SarfX Backend/main.py"
touch "SarfX Backend/Dockerfile"
touch "SarfX Backend/requirements.txt"

# 6. Fichiers App (Config & Init)
touch app/config.py
touch app/__init__.py

# 7. Services
touch app/services/db_service.py
touch app/services/email_service.py

# 8. Routes
touch app/routes/auth_routes.py
touch app/routes/admin_routes.py
touch app/routes/supplier_routes.py

# 9. Static & Templates
touch app/static/css/style.css
touch app/templates/base.html
touch app/templates/login.html
touch app/templates/dashboard.html
touch app/templates/suppliers.html
touch app/templates/404.html

# 10. Documentation
touch documentation/app_assurance.txt

echo "🎉 Terminé ! Nouvelle structure en place."
