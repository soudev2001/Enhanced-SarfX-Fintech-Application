#!/bin/bash
# Script de diagnostic et correction 502 Bad Gateway
# Exécuter sur le serveur: bash fix_502.sh

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}=== DIAGNOSTIC 502 BAD GATEWAY ===${NC}"

# 1. Vérifier le statut du service Flask
echo -e "\n${YELLOW}1. Statut du service sarfx-enhanced:${NC}"
systemctl status sarfx-enhanced --no-pager | head -20

# 2. Voir les dernières erreurs dans les logs
echo -e "\n${YELLOW}2. Dernières erreurs (logs):${NC}"
journalctl -u sarfx-enhanced -n 30 --no-pager | grep -E "Error|Exception|Failed|error|Traceback"

# 3. Vérifier si le port est utilisé
echo -e "\n${YELLOW}3. Port 8002 (Flask):${NC}"
ss -tlnp | grep 8002 || echo "❌ Aucun service n'écoute sur le port 8002!"

# 4. Vérifier la mémoire et les processus
echo -e "\n${YELLOW}4. Processus gunicorn:${NC}"
ps aux | grep gunicorn | head -5

# 5. Mémoire disponible
echo -e "\n${YELLOW}5. Mémoire:${NC}"
free -h

# 6. Espace disque
echo -e "\n${YELLOW}6. Espace disque:${NC}"
df -h /

# 7. Test de connexion MongoDB depuis le serveur
echo -e "\n${YELLOW}7. Test MongoDB:${NC}"
cd /var/www/sarfx-enhanced
source venv/bin/activate
python3 << 'PYEOF'
try:
    from pymongo import MongoClient
    import certifi
    import os

    # Lire la config
    from dotenv import load_dotenv
    load_dotenv()

    uri = os.getenv('MONGO_URI', 'mongodb+srv://soufiane:gogo@cluster0.05omqhe.mongodb.net/SarfX_Enhanced')
    client = MongoClient(uri, tlsCAFile=certifi.where(), serverSelectionTimeoutMS=5000)

    # Test de connexion
    client.admin.command('ping')
    print("✅ MongoDB OK")
except Exception as e:
    print(f"❌ MongoDB ERREUR: {e}")
PYEOF

echo -e "\n${GREEN}=== TENTATIVE DE RÉPARATION ===${NC}"

# Redémarrer le service
echo -e "\n${YELLOW}Redémarrage du service...${NC}"
systemctl restart sarfx-enhanced
sleep 3

# Vérifier après redémarrage
echo -e "\n${YELLOW}Statut après redémarrage:${NC}"
systemctl status sarfx-enhanced --no-pager | head -10

# Test final
echo -e "\n${YELLOW}Test de la page de login:${NC}"
curl -s -o /dev/null -w "HTTP Code: %{http_code}\n" http://127.0.0.1:8002/auth/login

echo -e "\n${GREEN}=== FIN DU DIAGNOSTIC ===${NC}"
echo -e "Si le problème persiste, regardez les logs complets:"
echo -e "  ${GREEN}journalctl -u sarfx-enhanced -f${NC}"
