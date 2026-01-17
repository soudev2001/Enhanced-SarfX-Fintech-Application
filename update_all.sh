#!/bin/bash

# ==========================================
# MISE À JOUR COMPLÈTE SARFX (App + Backend IA)
# ==========================================

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

APP_DIR="/var/www/sarfx-enhanced"
AI_DIR="/var/www/sarfx-enhanced/SarfX Backend"

echo -e "${GREEN}🔄 MISE À JOUR SARFX COMPLÈTE${NC}"

# 1. Pull du repository
echo -e "${YELLOW}> Récupération des dernières modifications...${NC}"
cd "$APP_DIR"
git pull origin main

# 2. Mise à jour de l'application Flask
echo -e "${YELLOW}> Mise à jour de l'application Flask...${NC}"
source venv/bin/activate
pip install -r requirements.txt -q
systemctl restart sarfx-enhanced

if systemctl is-active --quiet sarfx-enhanced; then
    echo -e "${GREEN}✅ Flask App (Port 8002) - OK${NC}"
else
    echo -e "${RED}❌ Flask App - ERREUR${NC}"
fi

# 3. Mise à jour du Backend IA (si configuré)
if [ -f "/etc/systemd/system/sarfx-ai-backend.service" ]; then
    echo -e "${YELLOW}> Mise à jour du Backend IA...${NC}"
    cd "$AI_DIR"
    
    if [ -d "venv" ]; then
        source venv/bin/activate
    else
        python3 -m venv venv
        source venv/bin/activate
    fi
    
    pip install -r requirements.txt -q
    systemctl restart sarfx-ai-backend
    
    if systemctl is-active --quiet sarfx-ai-backend; then
        echo -e "${GREEN}✅ AI Backend (Port 8087) - OK${NC}"
    else
        echo -e "${RED}❌ AI Backend - ERREUR${NC}"
    fi
else
    echo -e "${BLUE}ℹ️  Backend IA non configuré. Lancez deploy_ai_backend.sh pour l'installer.${NC}"
fi

echo ""
echo -e "${GREEN}=== MISE À JOUR TERMINÉE ===${NC}"
echo -e "Flask App    : https://sarfx.io"
echo -e "AI Backend   : http://127.0.0.1:8087 (interne)"
