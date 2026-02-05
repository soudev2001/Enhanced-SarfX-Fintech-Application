# 🐳 Guide Docker - SarfX Enhanced

## 📋 Table des matières

1. [Prérequis](#prérequis)
2. [Démarrage Rapide](#démarrage-rapide)
3. [Architecture Docker](#architecture-docker)
4. [Environnement de Développement](#environnement-de-développement)
5. [Environnement de Production](#environnement-de-production)
6. [Commandes Make](#commandes-make)
7. [Gestion de la Base de Données](#gestion-de-la-base-de-données)
8. [Dépannage](#dépannage)

---

## 🔧 Prérequis

- **Docker** 20.10+ ([Installation](https://docs.docker.com/get-docker/))
- **Docker Compose** v2.0+ ([Installation](https://docs.docker.com/compose/install/))
- **Make** (optionnel, pour les commandes simplifiées)

### Vérification de l'installation

```bash
docker --version          # Docker version 20.10+
docker compose version    # Docker Compose version v2.0+
make --version           # GNU Make 4.x
```

---

## 🚀 Démarrage Rapide

### Première installation

```bash
# 1. Cloner le repository
git clone https://github.com/votre-repo/sarfx-enhanced.git
cd sarfx-enhanced

# 2. Copier le fichier d'environnement
cp .env.example .env

# 3. Éditer .env avec vos valeurs (optionnel pour dev)
nano .env

# 4. Lancer l'environnement de développement
make init
# OU manuellement:
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

### Accès aux services

| Service | URL | Description |
|---------|-----|-------------|
| 🌐 **Flask App** | http://localhost:5050 | Application principale |
| 🤖 **AI Backend** | http://localhost:8087 | API FastAPI + Swagger |
| 📊 **Mongo Express** | http://localhost:8081 | Interface MongoDB (dev) |
| 📈 **Redis Commander** | http://localhost:8082 | Interface Redis (dev) |

### Credentials par défaut

| Compte | Email | Mot de passe |
|--------|-------|--------------|
| Admin | admin@sarfx.io | admin123 |
| User | user@sarfx.io | user123 |
| Bank | bank@attijariwafa.ma | bank123 |

---

## 🏗️ Architecture Docker

```
┌─────────────────────────────────────────────────────────────┐
│                      Docker Network                         │
│                      sarfx-network                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐    │
│  │  flask-app   │   │  ai-backend  │   │    nginx     │    │
│  │  Port: 5050  │   │  Port: 8087  │   │  Port: 80/443│    │
│  └──────┬───────┘   └──────┬───────┘   └──────┬───────┘    │
│         │                   │                   │            │
│         └───────────────────┼───────────────────┘            │
│                             │                                │
│  ┌──────────────┐   ┌──────▼───────┐                        │
│  │    redis     │   │    mongo     │                        │
│  │  Port: 6379  │   │  Port: 27017 │                        │
│  └──────────────┘   └──────────────┘                        │
│                                                              │
│  Volumes:                                                    │
│  - mongo_data    (persistance MongoDB)                       │
│  - redis_data    (persistance Redis)                         │
│  - flask_logs    (logs applicatifs)                          │
│  - flask_uploads (fichiers uploadés)                         │
└─────────────────────────────────────────────────────────────┘
```

### Services

| Service | Image | Port | Description |
|---------|-------|------|-------------|
| `mongo` | mongo:7.0 | 27017 | Base de données MongoDB |
| `redis` | redis:7-alpine | 6379 | Cache et sessions |
| `flask-app` | Custom | 5050 | Application Flask |
| `ai-backend` | Custom | 8087 | Backend IA FastAPI |
| `nginx` | nginx:alpine | 80/443 | Reverse proxy (prod) |
| `mongo-express` | mongo-express | 8081 | UI MongoDB (dev) |
| `redis-commander` | redis-commander | 8082 | UI Redis (dev) |

---

## 💻 Environnement de Développement

### Caractéristiques

- ✅ Hot-reload (code source monté en volume)
- ✅ Mode debug Flask activé
- ✅ Mongo Express pour visualiser les données
- ✅ Redis Commander pour le cache
- ✅ Logs verbeux

### Lancement

```bash
# Avec Make
make dev        # Premier plan (voir les logs)
make dev-d      # Arrière-plan (détaché)

# Sans Make
docker compose -f docker-compose.yml -f docker-compose.dev.yml up
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

### Structure des fichiers

```
docker-compose.yml        # Configuration de base
docker-compose.dev.yml    # Overrides pour développement
```

### Variables d'environnement (dev)

```env
FLASK_ENV=development
MONGO_LOCAL=true
MONGO_HOST=mongo
REDIS_URL=redis://redis:6379/0
AI_BACKEND_URL=http://ai-backend:8087
```

---

## 🚀 Environnement de Production

### Caractéristiques

- ✅ Gunicorn avec 4 workers
- ✅ Nginx reverse proxy avec SSL
- ✅ Authentification MongoDB et Redis
- ✅ Rate limiting
- ✅ Logs structurés avec rotation
- ✅ Health checks
- ✅ Limites de ressources

### Lancement

```bash
# Avec Make
make prod       # Lance en arrière-plan
make prod-down  # Arrête les services

# Sans Make
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
docker compose -f docker-compose.yml -f docker-compose.prod.yml down
```

### Configuration SSL

```bash
# 1. Créer les répertoires
mkdir -p nginx/ssl certbot

# 2. Obtenir le certificat Let's Encrypt
docker run -it --rm -v $(pwd)/certbot:/etc/letsencrypt \
  -v $(pwd)/nginx/ssl:/var/www/certbot \
  certbot/certbot certonly --webroot \
  -w /var/www/certbot -d sarfx.io -d www.sarfx.io

# 3. Les certificats seront dans certbot/live/sarfx.io/
```

### Variables d'environnement (prod)

```env
FLASK_ENV=production
SECRET_KEY=votre_cle_secrete_32_chars_minimum
MONGO_ROOT_USERNAME=admin
MONGO_ROOT_PASSWORD=mot_de_passe_fort
REDIS_PASSWORD=mot_de_passe_redis
GUNICORN_WORKERS=4
```

---

## 📋 Commandes Make

### Commandes principales

```bash
make help          # Affiche toutes les commandes disponibles

# Développement
make dev           # Lance l'env dev (premier plan)
make dev-d         # Lance l'env dev (détaché)
make dev-down      # Arrête l'env dev

# Production
make prod          # Lance l'env prod
make prod-down     # Arrête l'env prod

# Général
make build         # Build les images
make up            # Démarre (config de base)
make down          # Arrête tout
make restart       # Redémarre
```

### Logs et monitoring

```bash
make logs          # Tous les logs
make logs-flask    # Logs Flask uniquement
make logs-ai       # Logs AI backend
make logs-mongo    # Logs MongoDB
make logs-redis    # Logs Redis
make ps            # Liste les conteneurs
make stats         # Statistiques ressources
make health        # Vérifie l'état des services
```

### Shells et debug

```bash
make shell-flask   # Shell dans Flask
make shell-ai      # Shell dans AI backend
make shell-mongo   # mongosh SarfX_Enhanced
make shell-redis   # redis-cli
```

### Base de données

```bash
make seed          # Seed la base de données
make backup        # Sauvegarde MongoDB
make restore       # Restaure la dernière sauvegarde
```

### Nettoyage

```bash
make clean         # Supprime conteneurs + volumes
make clean-images  # + supprime les images
make prune         # Nettoie tout Docker (⚠️ dangereux)
```

### Tests

```bash
make test          # Lance les tests
make test-cov      # Tests avec couverture
```

---

## 🗄️ Gestion de la Base de Données

### Accéder à MongoDB

```bash
# Via Make
make shell-mongo

# Manuellement
docker exec -it sarfx-mongo mongosh SarfX_Enhanced
```

### Requêtes utiles

```javascript
// Voir les collections
show collections

// Compter les utilisateurs
db.users.countDocuments()

// Trouver un utilisateur
db.users.findOne({email: "admin@sarfx.io"})

// Voir les transactions récentes
db.transactions.find().sort({created_at: -1}).limit(5)

// Statistiques
db.stats()
```

### Sauvegardes

```bash
# Créer une sauvegarde
make backup
# → Sauvegardé dans backups/backup-YYYYMMDD-HHMMSS.archive

# Restaurer la dernière sauvegarde
make restore

# Sauvegarde manuelle
docker exec sarfx-mongo mongodump \
  --db SarfX_Enhanced \
  --archive=/data/db/backup.archive
docker cp sarfx-mongo:/data/db/backup.archive ./backup.archive
```

### Données de test

Les données initiales sont créées par `scripts/seed/mongo-init.js` :

- 3 utilisateurs (admin, user, bank)
- 1 wallet pour l'utilisateur test
- 6 banques marocaines
- Taux de change initiaux
- 3 ATMs de test

---

## 🔧 Dépannage

### Le conteneur Flask ne démarre pas

```bash
# Vérifier les logs
make logs-flask

# Erreur fréquente: MongoDB pas prêt
# Solution: Attendre ou relancer
docker compose restart flask-app
```

### Erreur de connexion MongoDB

```bash
# Vérifier que MongoDB est up
docker exec sarfx-mongo mongosh --eval "db.adminCommand('ping')"

# Vérifier les variables d'environnement
docker exec sarfx-flask env | grep MONGO
```

### Port déjà utilisé

```bash
# Identifier le processus
lsof -i :5050
netstat -tulpn | grep 5050

# Changer le port dans .env
FLASK_PORT=5051
```

### Réinitialiser complètement

```bash
# Arrêter et supprimer tout
make clean

# OU plus radical (attention!)
docker compose down -v --rmi all
docker system prune -af --volumes

# Relancer
make init
```

### Problème de permissions (Linux)

```bash
# Si erreur de permission sur les volumes
sudo chown -R $USER:$USER ./backups ./logs

# Pour les fichiers créés par Docker
sudo chown -R 1000:1000 ./app
```

### Les changements de code ne sont pas reflétés

```bash
# Forcer le rebuild
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build

# Ou
make build && make dev
```

---

## 📁 Structure des fichiers Docker

```
sarfx-enhanced/
├── Dockerfile                    # Build Flask app
├── .dockerignore                 # Fichiers exclus du build
├── docker-compose.yml            # Config de base
├── docker-compose.dev.yml        # Override dev
├── docker-compose.prod.yml       # Override prod
├── Makefile                      # Commandes simplifiées
├── .env.example                  # Template variables
├── nginx/
│   ├── nginx.conf                # Config Nginx principale
│   └── conf.d/
│       └── sarfx.conf            # Server block SarfX
├── scripts/
│   └── seed/
│       └── mongo-init.js         # Init MongoDB
└── SarfX Backend/
    └── Dockerfile                # Build AI backend
```

---

## 🔐 Sécurité en Production

### Checklist

- [ ] Changer `SECRET_KEY` (32+ caractères)
- [ ] Définir `MONGO_ROOT_PASSWORD` fort
- [ ] Définir `REDIS_PASSWORD`
- [ ] Configurer SSL avec Let's Encrypt
- [ ] Activer les limites de ressources
- [ ] Configurer les backups automatiques
- [ ] Mettre en place la rotation des logs

### Exemple .env production

```env
FLASK_ENV=production
SECRET_KEY=votre_cle_ultra_secrete_minimum_32_caracteres_aleatoires
MONGO_ROOT_USERNAME=sarfx_admin
MONGO_ROOT_PASSWORD=MotDePasseForT123!@#ComplexE
REDIS_PASSWORD=RedisPasswordSecure456!
GUNICORN_WORKERS=4
LOG_LEVEL=WARNING
```

---

## 📞 Support

En cas de problème :
1. Consultez les logs : `make logs`
2. Vérifiez les health checks : `make health`
3. Consultez cette documentation
4. Ouvrez une issue sur GitHub

---

**Dernière mise à jour :** Février 2026
**Version Docker :** 2.0
