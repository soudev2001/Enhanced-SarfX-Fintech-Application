# 🔐 Accès Serveur Production SarfX

> ⚠️ **CONFIDENTIEL** - Ne pas partager ce fichier

## 📡 Informations Serveur

| Élément | Valeur |
|---------|--------|
| **IP** | `195.35.28.227` |
| **Hostname** | `srv1264625` |
| **OS** | Ubuntu 25.10 |
| **Domain** | `sarfx.io` |

## 🔑 Accès SSH

```bash
ssh root@195.35.28.227
# Password: EKt+yAYuDeM96A@x(5nR
```

### Connexion rapide
```bash
# Ajouter à ~/.ssh/config pour accès simplifié
Host sarfx
    HostName 195.35.28.227
    User root
    # Password: EKt+yAYuDeM96A@x(5nR
```

## 📁 Chemins Importants

| Chemin | Description |
|--------|-------------|
| `/var/www/sarfx-enhanced` | Code source de l'application |
| `/var/www/sarfx-enhanced/.env` | Variables d'environnement |
| `/etc/letsencrypt` | Certificats SSL |

## 🐳 Commandes Docker

```bash
# Aller dans le dossier
cd /var/www/sarfx-enhanced

# Voir les containers
docker ps

# Logs en temps réel
docker logs -f sarfx-flask
docker logs -f sarfx-nginx
docker logs -f sarfx-mongo

# Redémarrer un service
docker compose -f docker-compose.yml -f docker-compose.prod.yml restart flask-app

# Rebuild complet
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# Arrêter tout
docker compose -f docker-compose.yml -f docker-compose.prod.yml down
```

## 🔄 Mise à jour du code

```bash
cd /var/www/sarfx-enhanced
git pull origin main
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build flask-app
```

## 👥 Comptes de Test

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@sarfx.io | admin123 |
| Bank | bank@sarfx.io | bank123 |
| User | user@sarfx.io | user123 |
| Demo | demo@sarfx.io | demo123 |

## 🌐 URLs

| Service | URL |
|---------|-----|
| Landing | https://sarfx.io |
| Login | https://sarfx.io/auth/login |
| Admin | https://sarfx.io/admin |
| Health | https://sarfx.io/health |

## 📊 MongoDB

```bash
# Accéder au shell MongoDB
docker exec -it sarfx-mongo mongosh -u admin -p "SarfX_Prod_2026_SecurePass!" --authenticationDatabase admin

# Commandes utiles
use SarfX_Enhanced
db.users.find()
db.wallets.find()
db.transactions.find()
```

## 🔧 Dépannage

### Voir les logs d'erreur Flask
```bash
docker logs sarfx-flask --tail 100 2>&1 | grep -i error
```

### Redémarrer Nginx
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml restart nginx
```

### Vérifier les certificats SSL
```bash
certbot certificates
```

### Renouveler SSL manuellement
```bash
certbot renew --dry-run
```

---
**Dernière mise à jour:** 5 Février 2026
