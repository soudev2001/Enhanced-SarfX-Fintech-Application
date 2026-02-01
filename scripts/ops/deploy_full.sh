#!/bin/bash

# Couleurs
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}=== DÉPLOIEMENT COMPLET SARFX ===${NC}"

# 1. Seed les données ATM
echo -e "\n${YELLOW}> Insertion des données ATM...${NC}"
cd /var/www/sarfx-enhanced
source venv/bin/activate
python3 seed_atm_data.py

# 1.5. Seed les données des banques
echo -e "\n${YELLOW}> Insertion des données des banques partenaires...${NC}"
python3 seed_banks.py

# 2. Redémarrer Flask
echo -e "\n${YELLOW}> Redémarrage de Flask...${NC}"
systemctl restart sarfx-enhanced
sleep 3

# 3. Vérifier les services
echo -e "\n${GREEN}=== STATUT DES SERVICES ===${NC}"
echo -e "\n${YELLOW}Flask (Port 8002):${NC}"
systemctl status sarfx-enhanced --no-pager | grep "Active:"

echo -e "\n${YELLOW}Backend IA (Port 8087):${NC}"
systemctl status sarfx-ai-backend --no-pager | grep "Active:"

# 4. Tester les APIs
echo -e "\n${GREEN}=== TESTS DES APIs ===${NC}"

echo -e "\n${YELLOW}1. Flask Health:${NC}"
curl -s http://127.0.0.1:8002/ | head -n 5

echo -e "\n${YELLOW}2. Backend IA:${NC}"
curl -s http://127.0.0.1:8087/ | jq '.'

echo -e "\n${YELLOW}3. API Banques:${NC}"
curl -s http://127.0.0.1:8002/api/banks | jq '.'

echo -e "\n${YELLOW}4. API ATM (Casablanca):${NC}"
curl -s "http://127.0.0.1:8002/api/atms?city=Casablanca&limit=3" | jq '.'

echo -e "\n${YELLOW}5. Smart Rate (EUR→MAD):${NC}"
curl -s "http://127.0.0.1:8087/smart-rate/EUR/MAD?amount=1000" | jq '.'

# 5. Vérifier MongoDB
echo -e "\n${GREEN}=== BASE DE DONNÉES ===${NC}"
cd /var/www/sarfx-enhanced
source venv/bin/activate
python3 << 'PYEOF'
from pymongo import MongoClient
import certifi

uri = 'mongodb+srv://soufiane:gogo@cluster0.05omqhe.mongodb.net/SarfX_Enhanced'
client = MongoClient(uri, tlsCAFile=certifi.where())
db = client['SarfX_Enhanced']

atm_count = db.atm_locations.count_documents({})
banks = db.atm_locations.distinct('bank_code')
cities = db.atm_locations.distinct('city')

print(f"\n✅ ATM: {atm_count}")
print(f"✅ Banques: {len(banks)} ({', '.join(banks)})")
print(f"✅ Villes: {len(cities)} ({', '.join(cities)})")
PYEOF

echo -e "\n${GREEN}🎉 Déploiement complet terminé !${NC}"
echo -e "\n${YELLOW}Accès:${NC}"
echo -e "  - Application: https://sarfx.io"
echo -e "  - Backend IA:  http://127.0.0.1:8087"
echo -e "\n${YELLOW}Logs:${NC}"
echo -e "  - Flask:       journalctl -u sarfx-enhanced -f"
echo -e "  - Backend IA:  journalctl -u sarfx-ai-backend -f"

