# 🚀 Guide de Déploiement SarfX Enhanced + Backend IA

## Architecture du Système

```
┌─────────────────────────────────────────────────────────────┐
│                     Serveur Production                       │
│                    srv1264625 (sarfx.io)                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────┐        ┌───────────────────────┐   │
│  │  Flask App         │        │  Backend IA (FastAPI) │   │
│  │  Port: 8002        │◄───────┤  Port: 8087           │   │
│  │  Service:          │  API   │  Service:             │   │
│  │  sarfx-enhanced    │  Call  │  sarfx-ai-backend     │   │
│  └────────┬───────────┘        └───────────────────────┘   │
│           │                                                  │
│  ┌────────▼────────────────────────────────────────────┐   │
│  │              Nginx (Reverse Proxy)                   │   │
│  │  Port 80/443 → 8002 (Flask)                          │   │
│  │  api.sarfx.io → 8087 (Optionnel)                     │   │
│  └──────────────────────────────────────────────────────┘   │
│                          ▲                                   │
└──────────────────────────┼───────────────────────────────────┘
                           │
                 Internet  │
                    ───────┴────────
                      sarfx.io
                   (SSL: Let's Encrypt)
```

## 📦 État Actuel

✅ **Flask App** : `sarfx-enhanced.service` - **ACTIF** sur port 8002
⏳ **Backend IA** : À déployer sur port 8087

---

## 🔧 Déploiement du Backend IA

### Étape 1 : Mettre à jour le code

```bash
cd /var/www/sarfx-enhanced
git pull origin main
```

### Étape 2 : Déployer le Backend IA

```bash
# Rendre le script exécutable
chmod +x deploy_ai_backend.sh

# Lancer le déploiement
./deploy_ai_backend.sh
```

**Le script va :**
1. Créer un environnement virtuel Python dans `SarfX Backend/venv`
2. Installer les dépendances (FastAPI, Uvicorn, certifi, etc.)
3. Créer un service systemd `sarfx-ai-backend.service`
4. Démarrer le service sur le port **8087**
5. Vous demander si vous voulez exposer l'API publiquement

### Étape 3 : Vérifier le déploiement

```bash
# Statut du service
systemctl status sarfx-ai-backend

# Test de l'API
curl http://127.0.0.1:8087/

# Test du Smart Rate
curl "http://127.0.0.1:8087/smart-rate/EUR/MAD?amount=1000"

# Test des prédictions
curl http://127.0.0.1:8087/predict/EURMAD
```

**Réponse attendue :**
```json
{
  "system": "SarfX Core",
  "status": "operational",
  "db": "connected"
}
```

---

## 🔄 Mises à jour futures

Pour mettre à jour **les deux services** (Flask + IA) en une seule commande :

```bash
cd /var/www/sarfx-enhanced
./update_all.sh
```

Ce script va :
- Pull les dernières modifications Git
- Mettre à jour les dépendances Python
- Redémarrer `sarfx-enhanced` (Flask)
- Redémarrer `sarfx-ai-backend` (FastAPI)

---

## 🐛 Debugging

### Flask App - Logs en temps réel
```bash
journalctl -u sarfx-enhanced -f
```

### Backend IA - Logs en temps réel
```bash
journalctl -u sarfx-ai-backend -f
```

### Erreur 500 sur /auth/login ?

**Causes possibles :**

1. **MongoDB non accessible**
   ```bash
   # Vérifier que MONGO_URI est dans .env
   cat /var/www/sarfx-enhanced/.env | grep MONGO_URI
   ```

2. **Certifi manquant (SSL MongoDB)**
   ```bash
   cd /var/www/sarfx-enhanced
   source venv/bin/activate
   pip install certifi
   systemctl restart sarfx-enhanced
   ```

3. **Variable SECRET_KEY manquante**
   ```bash
   echo "SECRET_KEY=$(openssl rand -hex 32)" >> /var/www/sarfx-enhanced/.env
   systemctl restart sarfx-enhanced
   ```

### Tester la connexion MongoDB

```bash
cd /var/www/sarfx-enhanced
source venv/bin/activate
python3 -c "
from pymongo import MongoClient
import certifi
uri = 'mongodb+srv://soufiane:gogo@cluster0.05omqhe.mongodb.net/SarfX_Enhanced'
client = MongoClient(uri, tlsCAFile=certifi.where())
client.admin.command('ping')
print('✅ MongoDB OK')
"
```

---

## 🌐 Exposer l'API IA publiquement (Optionnel)

Si vous voulez que l'API IA soit accessible publiquement sur `api.sarfx.io` :

### 1. Configurer le DNS
Ajoutez un enregistrement A sur votre DNS :
```
A    api.sarfx.io    195.35.28.227
```

### 2. Créer la configuration Nginx

```bash
nano /etc/nginx/sites-available/sarfx-ai
```

```nginx
server {
    listen 80;
    server_name api.sarfx.io;

    location / {
        proxy_pass http://127.0.0.1:8087;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # CORS Headers
        add_header 'Access-Control-Allow-Origin' '*' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS' always;
    }
}
```

```bash
# Activer le site
ln -s /etc/nginx/sites-available/sarfx-ai /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx

# SSL avec Certbot
certbot --nginx -d api.sarfx.io
```

---

## 📊 Endpoints de l'API IA

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/` | GET | Health check |
| `/smart-rate/{base}/{target}?amount=X` | GET | Meilleur taux de change avec arbitrage |
| `/predict/{pair}` | GET | Prédictions IA (7 jours) |

### Exemples

**Smart Rate :**
```bash
curl "http://127.0.0.1:8087/smart-rate/EUR/MAD?amount=1000"
```

**Prédiction :**
```bash
curl http://127.0.0.1:8087/predict/EURMAD
```

---

## 🔐 Variables d'environnement

### Flask App (`/var/www/sarfx-enhanced/.env`)
```env
MONGO_URI=mongodb+srv://soufiane:gogo@cluster0.05omqhe.mongodb.net/SarfX_Enhanced
SECRET_KEY=votre_cle_secrete_longue
AI_BACKEND_URL=http://127.0.0.1:8087
SMTP_EMAIL=starkxgroup@gmail.com
SMTP_PASSWORD=mpnkmpqeypjsvern
```

### Backend IA (`/var/www/sarfx-enhanced/SarfX Backend/.env`)
```env
MONGO_URI=mongodb+srv://soufiane:gogo@cluster0.05omqhe.mongodb.net/SarfX_Enhanced
AI_PORT=8087
PORT=8087
```

---

## 📝 Services Systemd

### sarfx-enhanced.service (Flask)
```bash
systemctl status sarfx-enhanced
systemctl restart sarfx-enhanced
systemctl stop sarfx-enhanced
systemctl start sarfx-enhanced
```

### sarfx-ai-backend.service (FastAPI)
```bash
systemctl status sarfx-ai-backend
systemctl restart sarfx-ai-backend
systemctl stop sarfx-ai-backend
systemctl start sarfx-ai-backend
```

---

## 🎯 Checklist de Déploiement

- [x] Flask App installé et tournant (port 8002)
- [ ] Backend IA installé et tournant (port 8087)
- [ ] Test de connexion MongoDB avec certifi
- [ ] Vérifier que Flask peut appeler l'API IA
- [ ] (Optionnel) Exposer l'API sur api.sarfx.io
- [ ] Configurer SSL pour api.sarfx.io

---

## 🆘 Support

En cas de problème :
1. Vérifiez les logs : `journalctl -u sarfx-enhanced -f`
2. Vérifiez les logs IA : `journalctl -u sarfx-ai-backend -f`
3. Testez MongoDB : Script Python ci-dessus
4. Vérifiez Nginx : `nginx -t`
5. Vérifiez les ports : `netstat -tulpn | grep -E '8002|8087'`

---

**Dernière mise à jour :** 17 janvier 2026  
**Version :** 2.0 (Flask + Backend IA)
