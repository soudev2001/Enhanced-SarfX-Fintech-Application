# 🔧 GUIDE DE FIX - Backend IA SarfX

## 🚨 Problème Identifié

Le service `sarfx-ai-backend` échoue avec l'erreur:
```
Unable to locate executable '/var/www/sarfx-enhanced/SarfX Backend/venv/bin/uvicorn'
```

**Cause**: Le dossier "SarfX Backend" contient un espace, ce qui pose problème avec systemd et les chemins de l'environnement virtuel Python.

---

## ✅ Solution Complète

### Étape 1: Télécharger le script de fix

```bash
cd /var/www/sarfx-enhanced
git pull origin main
```

### Étape 2: Rendre le script exécutable

```bash
chmod +x fix_ai_backend.sh
```

### Étape 3: Exécuter le script de fix

```bash
./fix_ai_backend.sh
```

**Ce script va automatiquement:**
1. ✅ Arrêter l'ancien service défaillant
2. ✅ Renommer "SarfX Backend" → "sarfx-backend" (sans espace)
3. ✅ Supprimer l'ancien environnement virtuel corrompu
4. ✅ Créer un nouveau venv propre
5. ✅ Installer toutes les dépendances (FastAPI, Uvicorn, etc.)
6. ✅ Vérifier que uvicorn est bien installé
7. ✅ Créer un service systemd corrigé
8. ✅ Démarrer le service
9. ✅ Tester l'API automatiquement

---

## 🧪 Vérification

Après l'exécution du script, vous devriez voir:

```
✅ Service sarfx-ai-backend démarré avec succès !

=== INFORMATIONS ===
Port interne   : 8087
Répertoire     : /var/www/sarfx-enhanced/sarfx-backend
Logs           : journalctl -u sarfx-ai-backend -f

=== TESTS ===
curl http://127.0.0.1:8087/
curl "http://127.0.0.1:8087/smart-rate/EUR/MAD?amount=1000"

✅ API répond correctement !
{
  "system": "SarfX Core",
  "status": "operational",
  "db": "connected"
}

🎉 Déploiement terminé !
```

---

## 🔍 Vérifications Manuelles

### 1. Statut du service

```bash
systemctl status sarfx-ai-backend
```

**Attendu**: 
- Status: `active (running)`
- Vert `●`

### 2. Logs en temps réel

```bash
journalctl -u sarfx-ai-backend -f
```

**Attendu**:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8087
```

### 3. Test API

```bash
curl http://127.0.0.1:8087/
```

**Réponse attendue**:
```json
{
  "system": "SarfX Core",
  "version": "2.0.0",
  "status": "operational",
  "db": "connected",
  "timestamp": "2026-01-22T..."
}
```

### 4. Test Smart Rate

```bash
curl "http://127.0.0.1:8087/smart-rate/EUR/MAD?amount=1000"
```

**Réponse attendue**:
```json
{
  "base": "EUR",
  "target": "MAD",
  "amount": 1000,
  "rate": 10.85,
  "converted_amount": 10850.0,
  "source": "best_rate",
  "timestamp": "..."
}
```

---

## 🔧 Commandes Utiles

### Gérer le service

```bash
# Démarrer
systemctl start sarfx-ai-backend

# Arrêter
systemctl stop sarfx-ai-backend

# Redémarrer
systemctl restart sarfx-ai-backend

# Statut
systemctl status sarfx-ai-backend

# Logs
journalctl -u sarfx-ai-backend -f

# Logs des 100 dernières lignes
journalctl -u sarfx-ai-backend -n 100 --no-pager
```

### Vérifier les ports

```bash
# Vérifier que le port 8087 est bien en écoute
netstat -tulpn | grep 8087
```

**Attendu**:
```
tcp  0  0  127.0.0.1:8087  0.0.0.0:*  LISTEN  PID/python
```

### Tester depuis l'application Flask

```bash
cd /var/www/sarfx-enhanced
source venv/bin/activate
python3 -c "
import requests
try:
    r = requests.get('http://127.0.0.1:8087/')
    print('✅ Flask peut contacter le backend IA')
    print(r.json())
except Exception as e:
    print(f'❌ Erreur: {e}')
"
```

---

## 🐛 Dépannage

### Erreur: Port déjà utilisé

```bash
# Voir ce qui utilise le port 8087
lsof -i :8087

# Tuer le processus si nécessaire
kill -9 <PID>
```

### Erreur: MongoDB non accessible

```bash
cd /var/www/sarfx-enhanced/sarfx-backend
source venv/bin/activate
python3 -c "
from pymongo import MongoClient
import certifi
uri = 'mongodb+srv://soufiane:gogo@cluster0.05omqhe.mongodb.net/SarfX_Enhanced'
try:
    client = MongoClient(uri, tlsCAFile=certifi.where(), serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    print('✅ MongoDB accessible')
except Exception as e:
    print(f'❌ Erreur MongoDB: {e}')
"
```

### Erreur: Module manquant

```bash
cd /var/www/sarfx-enhanced/sarfx-backend
source venv/bin/activate
pip install fastapi uvicorn pymongo certifi python-dotenv requests
systemctl restart sarfx-ai-backend
```

### Réinstallation complète

Si tout échoue, réexécutez simplement:

```bash
cd /var/www/sarfx-enhanced
./fix_ai_backend.sh
```

---

## 📦 Structure Correcte Après Fix

```
/var/www/sarfx-enhanced/
├── sarfx-backend/              # ✅ Renommé (sans espace)
│   ├── main.py
│   ├── requirements.txt
│   ├── .env
│   └── venv/                   # ✅ Nouveau venv propre
│       └── bin/
│           ├── python3
│           ├── pip
│           └── uvicorn         # ✅ Correctement installé
├── venv/                       # Flask app venv
├── run.py
└── ...
```

---

## 🔄 Intégration avec Flask

Une fois le backend IA fonctionnel, l'application Flask peut l'utiliser automatiquement.

**Vérification dans l'app Flask:**

```bash
cd /var/www/sarfx-enhanced
source venv/bin/activate
python3 -c "
from app.services.ai_service import get_forecast
result = get_forecast('EURMAD', 7)
print('✅ AI Service OK' if result else '❌ AI Service KO')
"
```

**Dans le code Flask** (`app/services/ai_service.py`):

```python
AI_BACKEND_URL = os.getenv('AI_BACKEND_URL', 'http://127.0.0.1:8087')

def get_smart_rate(base, target, amount):
    try:
        response = requests.get(
            f"{AI_BACKEND_URL}/smart-rate/{base}/{target}",
            params={"amount": amount},
            timeout=5
        )
        return response.json()
    except Exception as e:
        # Fallback
        return None
```

---

## ✅ Checklist de Validation

- [ ] `systemctl status sarfx-ai-backend` → Active (running)
- [ ] `curl http://127.0.0.1:8087/` → Réponse JSON valide
- [ ] `curl http://127.0.0.1:8087/smart-rate/EUR/MAD?amount=1000` → Réponse avec taux
- [ ] `netstat -tulpn | grep 8087` → Port en écoute
- [ ] Flask peut contacter le backend (test ci-dessus)
- [ ] Logs propres: `journalctl -u sarfx-ai-backend -n 50`

---

## 📞 Support

Si le problème persiste après avoir suivi ce guide:

1. **Vérifier les logs détaillés:**
   ```bash
   journalctl -u sarfx-ai-backend -n 200 --no-pager
   ```

2. **Vérifier la structure:**
   ```bash
   ls -la /var/www/sarfx-enhanced/sarfx-backend/
   ls -la /var/www/sarfx-enhanced/sarfx-backend/venv/bin/
   ```

3. **Test manuel de l'app:**
   ```bash
   cd /var/www/sarfx-enhanced/sarfx-backend
   source venv/bin/activate
   uvicorn main:app --host 127.0.0.1 --port 8087
   # Ctrl+C pour arrêter
   ```

---

**Dernière mise à jour:** 22 janvier 2026  
**Version:** 2.1 (Fix chemin venv)
