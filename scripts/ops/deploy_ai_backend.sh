#!/bin/bash

# ==========================================
# DÉPLOIEMENT DU BACKEND IA SARFX
# Port: 8087 | Service: sarfx-ai-backend
# ==========================================

APP_NAME="sarfx-ai-backend"
BASE_DIR="/var/www/sarfx-enhanced"
# IMPORTANT: Renommer le dossier pour éviter les espaces (problème systemd)
OLD_DIR="$BASE_DIR/SarfX Backend"
APP_DIR="$BASE_DIR/sarfx-backend"
INTERNAL_PORT=8087
USER="root"
GROUP="root"

# Couleurs
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}=== DÉPLOIEMENT DU BACKEND IA SARFX (Port $INTERNAL_PORT) ===${NC}"

# 0. Renommer le dossier si nécessaire (espaces non supportés par systemd)
if [ -d "$OLD_DIR" ] && [ ! -d "$APP_DIR" ]; then
    echo -e "${YELLOW}> Renommage du dossier (suppression des espaces)...${NC}"
    mv "$OLD_DIR" "$APP_DIR"
fi

# 1. Vérification du répertoire
if [ ! -d "$APP_DIR" ]; then
    echo -e "${RED}❌ Le dossier $APP_DIR n'existe pas.${NC}"
    echo -e "Lancez d'abord le script deploy_enhanced.sh pour cloner le repo principal."
    exit 1
fi

cd "$APP_DIR"

# 2. Création de l'environnement virtuel
echo -e "${YELLOW}> Création de l'environnement virtuel Python...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate

# 3. Installation des dépendances
echo -e "${YELLOW}> Installation des dépendances...${NC}"
pip install --upgrade pip -q
pip install -r requirements.txt

# 4. Création du fichier .env si nécessaire
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}> Génération du fichier .env...${NC}"
    cat > .env <<EOF
MONGO_URI=mongodb+srv://soufiane:gogo@cluster0.05omqhe.mongodb.net/SarfX_Enhanced
AI_PORT=$INTERNAL_PORT
PORT=$INTERNAL_PORT
EOF
fi

# 5. Configuration du service Systemd
echo -e "${YELLOW}> Configuration du service Systemd...${NC}"
SERVICE_FILE="/etc/systemd/system/$APP_NAME.service"

cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=SarfX AI Backend (FastAPI/Uvicorn)
After=network.target

[Service]
User=$USER
Group=$GROUP
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
Environment="PORT=$INTERNAL_PORT"
Environment="AI_PORT=$INTERNAL_PORT"
ExecStart=$APP_DIR/venv/bin/uvicorn main:app --host 127.0.0.1 --port $INTERNAL_PORT --workers 1
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable $APP_NAME
systemctl restart $APP_NAME

# 6. Vérification du service
echo -e "${YELLOW}> Vérification du service...${NC}"
sleep 2
if systemctl is-active --quiet $APP_NAME; then
    echo -e "${GREEN}✅ Service $APP_NAME démarré avec succès sur le port $INTERNAL_PORT${NC}"
else
    echo -e "${RED}❌ Erreur de démarrage. Vérifiez avec: journalctl -u $APP_NAME${NC}"
    exit 1
fi

# 7. Configuration Nginx (Optionnel - exposer publiquement)
echo -e "${YELLOW}> Voulez-vous exposer l'API IA publiquement via Nginx ? (o/N)${NC}"
read -r EXPOSE_API

if [[ "$EXPOSE_API" =~ ^[Oo]$ ]]; then
    NGINX_AI_CONF="/etc/nginx/sites-available/sarfx-ai"
    
    cat > "$NGINX_AI_CONF" <<EOF
server {
    listen 80;
    server_name api.sarfx.io;

    location / {
        proxy_pass http://127.0.0.1:$INTERNAL_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # CORS Headers
        add_header 'Access-Control-Allow-Origin' '*' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS' always;
        add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range' always;
    }
}
EOF
    
    if [ ! -f "/etc/nginx/sites-enabled/sarfx-ai" ]; then
        ln -s "$NGINX_AI_CONF" "/etc/nginx/sites-enabled/"
    fi
    
    nginx -t && systemctl reload nginx
    echo -e "${GREEN}✅ API exposée sur http://api.sarfx.io${NC}"
    echo -e "${BLUE}N'oubliez pas de configurer le DNS pour api.sarfx.io${NC}"
else
    echo -e "${BLUE}ℹ️  L'API IA reste accessible en interne sur http://127.0.0.1:$INTERNAL_PORT${NC}"
fi

# 8. Test de l'API
echo -e "${YELLOW}> Test de l'API...${NC}"
HEALTH=$(curl -s http://127.0.0.1:$INTERNAL_PORT/ 2>/dev/null)
if [ -n "$HEALTH" ]; then
    echo -e "${GREEN}✅ API répond: $HEALTH${NC}"
else
    echo -e "${YELLOW}⚠️  L'API met du temps à démarrer. Réessayez dans quelques secondes.${NC}"
fi

echo ""
echo -e "${GREEN}=== DÉPLOIEMENT TERMINÉ ===${NC}"
echo -e "Service    : $APP_NAME"
echo -e "Port       : $INTERNAL_PORT"
echo -e "Health     : curl http://127.0.0.1:$INTERNAL_PORT/"
echo -e "Smart Rate : curl http://127.0.0.1:$INTERNAL_PORT/smart-rate/EUR/MAD?amount=1000"
echo -e "Predict    : curl http://127.0.0.1:$INTERNAL_PORT/predict/EURMAD"
echo ""
echo -e "Commandes utiles:"
echo -e "  ${BLUE}systemctl status $APP_NAME${NC}     - État du service"
echo -e "  ${BLUE}journalctl -u $APP_NAME -f${NC}     - Logs en temps réel"
echo -e "  ${BLUE}systemctl restart $APP_NAME${NC}   - Redémarrer le service"
