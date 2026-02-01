#!/bin/bash

# ==========================================
# COMMANDES RAPIDES - SarfX Enhanced
# Copier-coller ces commandes sur le serveur
# ==========================================

echo "🚀 SarfX Enhanced - Guide Rapide"
echo "=================================="
echo ""

# Couleurs
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

show_menu() {
    echo -e "${BLUE}Que voulez-vous faire ?${NC}"
    echo ""
    echo "1. 🔧 Fixer le backend IA (RECOMMANDÉ)"
    echo "2. 📊 Vérifier le statut des services"
    echo "3. 📝 Voir les logs Flask"
    echo "4. 📝 Voir les logs Backend IA"
    echo "5. 🔄 Redémarrer Flask"
    echo "6. 🔄 Redémarrer Backend IA"
    echo "7. 🧪 Tester les APIs"
    echo "8. 🗑️  Nettoyer et tout redémarrer"
    echo "9. ❌ Quitter"
    echo ""
    read -p "Choix [1-9]: " choice
    
    case $choice in
        1) fix_backend_ai ;;
        2) check_status ;;
        3) show_flask_logs ;;
        4) show_ai_logs ;;
        5) restart_flask ;;
        6) restart_ai ;;
        7) test_apis ;;
        8) clean_restart ;;
        9) exit 0 ;;
        *) echo "Choix invalide" && show_menu ;;
    esac
}

fix_backend_ai() {
    echo -e "${GREEN}🔧 Fix du Backend IA...${NC}"
    cd /var/www/sarfx-enhanced
    git pull origin main
    chmod +x fix_ai_backend.sh
    ./fix_ai_backend.sh
    echo ""
    read -p "Appuyez sur Entrée pour continuer..."
    show_menu
}

check_status() {
    echo -e "${BLUE}📊 Statut des Services${NC}"
    echo "======================="
    echo ""
    echo -e "${YELLOW}Flask App (Port 8002):${NC}"
    systemctl status sarfx-enhanced --no-pager -l | head -10
    echo ""
    echo -e "${YELLOW}Backend IA (Port 8087):${NC}"
    systemctl status sarfx-ai-backend --no-pager -l | head -10
    echo ""
    echo -e "${YELLOW}Ports en écoute:${NC}"
    netstat -tulpn | grep -E '8002|8087' || echo "Aucun port actif"
    echo ""
    read -p "Appuyez sur Entrée pour continuer..."
    show_menu
}

show_flask_logs() {
    echo -e "${BLUE}📝 Logs Flask (temps réel)${NC}"
    echo "Appuyez sur Ctrl+C pour arrêter"
    echo ""
    journalctl -u sarfx-enhanced -f
}

show_ai_logs() {
    echo -e "${BLUE}📝 Logs Backend IA (temps réel)${NC}"
    echo "Appuyez sur Ctrl+C pour arrêter"
    echo ""
    journalctl -u sarfx-ai-backend -f
}

restart_flask() {
    echo -e "${GREEN}🔄 Redémarrage Flask...${NC}"
    systemctl restart sarfx-enhanced
    sleep 2
    systemctl status sarfx-enhanced --no-pager | head -10
    echo ""
    read -p "Appuyez sur Entrée pour continuer..."
    show_menu
}

restart_ai() {
    echo -e "${GREEN}🔄 Redémarrage Backend IA...${NC}"
    systemctl restart sarfx-ai-backend
    sleep 2
    systemctl status sarfx-ai-backend --no-pager | head -10
    echo ""
    read -p "Appuyez sur Entrée pour continuer..."
    show_menu
}

test_apis() {
    echo -e "${BLUE}🧪 Test des APIs${NC}"
    echo "================"
    echo ""
    
    echo -e "${YELLOW}1. Flask App (http://127.0.0.1:8002/)${NC}"
    curl -s http://127.0.0.1:8002/ | head -20 || echo "❌ Flask ne répond pas"
    echo ""
    
    echo -e "${YELLOW}2. Backend IA (http://127.0.0.1:8087/)${NC}"
    curl -s http://127.0.0.1:8087/ | python3 -m json.tool || echo "❌ Backend IA ne répond pas"
    echo ""
    
    echo -e "${YELLOW}3. Smart Rate (EUR → MAD)${NC}"
    curl -s "http://127.0.0.1:8087/smart-rate/EUR/MAD?amount=1000" | python3 -m json.tool || echo "❌ Smart Rate ne répond pas"
    echo ""
    
    echo -e "${YELLOW}4. Site public (https://sarfx.io)${NC}"
    curl -sI https://sarfx.io | grep -E 'HTTP|Server' || echo "❌ Site non accessible"
    echo ""
    
    read -p "Appuyez sur Entrée pour continuer..."
    show_menu
}

clean_restart() {
    echo -e "${GREEN}🗑️  Nettoyage et redémarrage complet...${NC}"
    echo ""
    
    echo "1. Arrêt des services..."
    systemctl stop sarfx-enhanced
    systemctl stop sarfx-ai-backend
    
    echo "2. Pull des dernières modifications..."
    cd /var/www/sarfx-enhanced
    git pull origin main
    
    echo "3. Mise à jour des dépendances Flask..."
    source venv/bin/activate
    pip install -r requirements.txt -q
    
    echo "4. Fix du backend IA..."
    chmod +x fix_ai_backend.sh
    ./fix_ai_backend.sh
    
    echo "5. Redémarrage Flask..."
    systemctl restart sarfx-enhanced
    
    echo "6. Vérification..."
    sleep 5
    systemctl status sarfx-enhanced --no-pager | head -10
    systemctl status sarfx-ai-backend --no-pager | head -10
    
    echo ""
    echo -e "${GREEN}✅ Redémarrage complet terminé !${NC}"
    echo ""
    read -p "Appuyez sur Entrée pour continuer..."
    show_menu
}

# Démarrage du menu
show_menu
