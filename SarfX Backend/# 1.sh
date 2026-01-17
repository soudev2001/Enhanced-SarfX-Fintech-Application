# 1. Mettre à jour l'application Flask + corriger l'erreur 500
cd /var/www/sarfx-enhanced
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
systemctl restart sarfx-enhanced

# 2. Déployer le Backend IA (Port 8087)
chmod +x deploy_ai_backend.sh
./deploy_ai_backend.sh

# 3. Vérifier que les deux services tournent
systemctl status sarfx-enhanced
systemctl status sarfx-ai-backend

# 4. Tester l'API IA localement
curl http://127.0.0.1:8087/
curl "http://127.0.0.1:8087/smart-rate/EUR/MAD?amount=1000"