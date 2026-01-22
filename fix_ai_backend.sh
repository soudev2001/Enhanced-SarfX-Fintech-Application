#!/bin/bash

# ==========================================
# FIX & REDÉPLOIEMENT BACKEND IA SARFX
# Corrige les problèmes de chemins et redéploie proprement
# ==========================================

set -e  # Exit on error

BASE_DIR="/var/www/sarfx-enhanced"
OLD_DIR="$BASE_DIR/SarfX Backend"
APP_DIR="$BASE_DIR/sarfx-backend"
APP_NAME="sarfx-ai-backend"
INTERNAL_PORT=8087
USER="root"
GROUP="root"

# Couleurs
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}=== FIX & REDÉPLOIEMENT BACKEND IA SARFX ===${NC}"

# 1. Arrêter et désactiver l'ancien service
echo -e "${YELLOW}> Nettoyage de l'ancien service...${NC}"
if systemctl is-active --quiet $APP_NAME; then
    systemctl stop $APP_NAME
fi
if systemctl is-enabled --quiet $APP_NAME 2>/dev/null; then
    systemctl disable $APP_NAME
fi

# 2. Renommer le dossier si nécessaire
if [ -d "$OLD_DIR" ] && [ ! -d "$APP_DIR" ]; then
    echo -e "${YELLOW}> Renommage du dossier (suppression des espaces)...${NC}"
    mv "$OLD_DIR" "$APP_DIR"
elif [ -d "$OLD_DIR" ] && [ -d "$APP_DIR" ]; then
    echo -e "${YELLOW}> Les deux dossiers existent. Fusion en cours...${NC}"
    rsync -av "$OLD_DIR/" "$APP_DIR/"
    rm -rf "$OLD_DIR"
fi

# 3. Vérification du répertoire
if [ ! -d "$APP_DIR" ]; then
    echo -e "${RED}❌ Le dossier $APP_DIR n'existe pas.${NC}"
    exit 1
fi

cd "$APP_DIR"

# 4. Supprimer l'ancien venv corrompu
if [ -d "venv" ]; then
    echo -e "${YELLOW}> Suppression de l'ancien environnement virtuel...${NC}"
    rm -rf venv
fi

# 5. Créer un nouveau venv propre
echo -e "${YELLOW}> Création d'un nouvel environnement virtuel...${NC}"
python3 -m venv venv

# 6. Activer et installer les dépendances
echo -e "${YELLOW}> Installation des dépendances...${NC}"
source venv/bin/activate
pip install --upgrade pip setuptools wheel

# Installer depuis requirements.txt
if [ -f "requirements.txt" ]; then
    echo -e "${YELLOW}> Installation depuis requirements.txt...${NC}"
    pip install -r requirements.txt
else
    echo -e "${YELLOW}> Installation manuelle des dépendances...${NC}"
    pip install fastapi uvicorn pymongo certifi dnspython python-dotenv requests yfinance pandas numpy statsmodels prophet scikit-learn tensorflow gunicorn
fi

# 7. Vérifier que uvicorn est bien installé
if [ ! -f "venv/bin/uvicorn" ]; then
    echo -e "${RED}❌ Uvicorn n'a pas été installé correctement.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Uvicorn installé : $(venv/bin/uvicorn --version)${NC}"

# 8. Créer le fichier .env si nécessaire
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}> Génération du fichier .env...${NC}"
    cat > .env <<EOF
MONGO_URI=mongodb+srv://soufiane:gogo@cluster0.05omqhe.mongodb.net/SarfX_Enhanced
AI_PORT=$INTERNAL_PORT
PORT=$INTERNAL_PORT
EOF
fi

# 9. Vérifier que main.py existe
if [ ! -f "main.py" ]; then
    echo -e "${RED}❌ Le fichier main.py est introuvable dans $APP_DIR${NC}"
    echo -e "${YELLOW}Contenu du dossier :${NC}"
    ls -la
    exit 1
fi

# 10. Test rapide de l'application
echo -e "${YELLOW}> Test de l'import de l'application...${NC}"
venv/bin/python3 -c "from main import app; print('✅ Import OK')" || {
    echo -e "${RED}❌ Erreur d'import de main.py${NC}"
    exit 1
}

# 11. Créer le service systemd avec les bons chemins
echo -e "${YELLOW}> Configuration du service Systemd...${NC}"
SERVICE_FILE="/etc/systemd/system/$APP_NAME.service"

cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=SarfX AI Backend (FastAPI/Uvicorn)
After=network.target

[Service]
Type=simple
User=$USER
Group=$GROUP
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="PYTHONPATH=$APP_DIR"
Environment="PORT=$INTERNAL_PORT"
Environment="AI_PORT=$INTERNAL_PORT"
ExecStart=$APP_DIR/venv/bin/uvicorn main:app --host 127.0.0.1 --port $INTERNAL_PORT --workers 1
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# 12. Recharger et démarrer le service
echo -e "${YELLOW}> Rechargement de systemd...${NC}"
systemctl daemon-reload

echo -e "${YELLOW}> Activation du service...${NC}"
systemctl enable $APP_NAME

echo -e "${YELLOW}> Démarrage du service...${NC}"
systemctl start $APP_NAME

# 13. Attendre et vérifier
echo -e "${YELLOW}> Vérification du service (10 secondes)...${NC}"
sleep 10

if systemctl is-active --quiet $APP_NAME; then
    echo -e "${GREEN}✅ Service $APP_NAME démarré avec succès !${NC}"
    echo ""
    echo -e "${BLUE}=== INFORMATIONS ===${NC}"
    echo -e "Port interne   : ${GREEN}$INTERNAL_PORT${NC}"
    echo -e "Répertoire     : ${GREEN}$APP_DIR${NC}"
    echo -e "Logs           : ${YELLOW}journalctl -u $APP_NAME -f${NC}"
    echo ""
    echo -e "${BLUE}=== TESTS ===${NC}"
    echo -e "curl http://127.0.0.1:$INTERNAL_PORT/"
    echo -e "curl \"http://127.0.0.1:$INTERNAL_PORT/smart-rate/EUR/MAD?amount=1000\""
    echo ""
    
    # Test de l'API
    echo -e "${YELLOW}> Test de l'API...${NC}"
    sleep 2
    RESPONSE=$(curl -s http://127.0.0.1:$INTERNAL_PORT/ || echo "failed")
    if [[ "$RESPONSE" == *"SarfX"* ]]; then
        echo -e "${GREEN}✅ API répond correctement !${NC}"
        echo "$RESPONSE" | python3 -m json.tool || echo "$RESPONSE"
    else
        echo -e "${RED}❌ L'API ne répond pas comme attendu${NC}"
        echo -e "${YELLOW}Logs récents :${NC}"
        journalctl -u $APP_NAME -n 20 --no-pager
    fi
else
    echo -e "${RED}❌ Le service n'a pas démarré correctement${NC}"
    echo -e "${YELLOW}Logs d'erreur :${NC}"
    journalctl -u $APP_NAME -n 50 --no-pager
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 Déploiement terminé !${NC}"
