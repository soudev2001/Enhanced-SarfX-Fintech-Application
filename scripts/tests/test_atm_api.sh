#!/bin/bash

echo "🧪 Test des routes API ATM & Banques"
echo "====================================="

# Démarrer le serveur en arrière-plan si nécessaire
# python run.py &
# SERVER_PID=$!
# sleep 3

BASE_URL="http://localhost:5000/api"

echo ""
echo "1️⃣  Test GET /api/banks"
curl -s "${BASE_URL}/banks" | python -m json.tool | head -n 20

echo ""
echo "2️⃣  Test GET /api/banks/attijariwafa"
curl -s "${BASE_URL}/banks/attijariwafa" | python -m json.tool

echo ""
echo "3️⃣  Test GET /api/atms?bank_code=attijariwafa&limit=3"
curl -s "${BASE_URL}/atms?bank_code=attijariwafa&limit=3" | python -m json.tool | head -n 30

echo ""
echo "4️⃣  Test POST /api/atms/nearest (Casablanca)"
curl -s -X POST "${BASE_URL}/atms/nearest" \
  -H "Content-Type: application/json" \
  -d '{"latitude": 33.5731, "longitude": -7.5898, "max_distance_km": 5, "limit": 3}' \
  | python -m json.tool | head -n 40

echo ""
echo "5️⃣  Test GET /api/atms/search?q=Morocco"
curl -s "${BASE_URL}/atms/search?q=Morocco" | python -m json.tool | head -n 20

echo ""
echo "6️⃣  Test GET /api/cities"
curl -s "${BASE_URL}/cities" | python -m json.tool

# Arrêter le serveur
# kill $SERVER_PID

echo ""
echo "✅ Tests terminés !"
