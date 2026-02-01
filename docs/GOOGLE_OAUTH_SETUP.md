# 🔐 Configuration Google OAuth 2.0 - SarfX

## 📋 Prérequis

- Compte Google Cloud Platform
- Projet GCP créé
- Domaine vérifié (sarfx.io)

---

## 🚀 Étapes de Configuration Google Cloud Console

### Étape 1 : Accéder à la Console Google Cloud

1. Rendez-vous sur [console.cloud.google.com](https://console.cloud.google.com)
2. Connectez-vous avec votre compte Google
3. Sélectionnez ou créez un projet

### Étape 2 : Activer l'API Google OAuth

1. Allez dans **APIs & Services** > **Library**
2. Recherchez "Google+ API" ou "Google Identity"
3. Activez les APIs suivantes :
   - ✅ Google+ API
   - ✅ Google Identity Toolkit API
   - ✅ People API (optionnel, pour plus d'infos profil)

### Étape 3 : Configurer l'écran de consentement OAuth

1. Allez dans **APIs & Services** > **OAuth consent screen**
2. Sélectionnez **External** (pour tous les utilisateurs)
3. Remplissez les informations :

| Champ | Valeur |
|-------|--------|
| **App name** | SarfX |
| **User support email** | support@sarfx.io |
| **App logo** | Logo SarfX (512x512 PNG) |
| **App domain** | sarfx.io |
| **Application home page** | https://sarfx.io |
| **Application privacy policy** | https://sarfx.io/privacy |
| **Application terms of service** | https://sarfx.io/terms |
| **Developer contact email** | dev@sarfx.io |

4. **Scopes** - Ajoutez :
   - `openid`
   - `email`
   - `profile`

5. **Test users** (en mode test) :
   - Ajoutez vos emails de test

### Étape 4 : Créer les identifiants OAuth 2.0

1. Allez dans **APIs & Services** > **Credentials**
2. Cliquez sur **+ CREATE CREDENTIALS** > **OAuth client ID**
3. Configuration :

```
Type d'application : Application Web
Nom : sarfx.io
```

#### Origines JavaScript autorisées

```
https://sarfx.io
https://www.sarfx.io
http://localhost:5000    (développement)
http://127.0.0.1:5000    (développement)
```

#### URIs de redirection autorisés

```
https://sarfx.io/auth/login/google/callback
https://www.sarfx.io/auth/login/google/callback
http://localhost:5000/auth/login/google/callback    (développement)
http://127.0.0.1:5000/auth/login/google/callback    (développement)
```

4. Cliquez sur **CREATE**
5. **Copiez** le Client ID et Client Secret

---

## 🔧 Configuration SarfX

### Variables d'environnement (.env)

Ajoutez ces variables dans votre fichier `.env` :

```bash
# Google OAuth 2.0
GOOGLE_CLIENT_ID=123456789-xxxxxxxxxxxxxxxxxxxxxxxxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxxxxxxxxxxxxxxxxxxxxxxx

# OAuth Redirect URI (production)
OAUTH_REDIRECT_URI=https://sarfx.io/auth/login/google/callback

# Secret Key (IMPORTANT: générez une clé unique)
SECRET_KEY=votre-cle-secrete-tres-longue-et-complexe-minimum-32-caracteres

# Redis (pour cache et rate limiting)
REDIS_URL=redis://localhost:6379/0
```

### Génération d'une SECRET_KEY sécurisée

```python
import secrets
print(secrets.token_hex(32))
```

Ou en ligne de commande :
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## 🖥️ Configuration Serveur (Production)

### Variables d'environnement sur le serveur

```bash
# SSH sur le serveur
ssh root@srv1264625

# Éditer le fichier de configuration
nano /var/www/sarfx-enhanced/.env

# Ajouter les variables
GOOGLE_CLIENT_ID=votre-client-id
GOOGLE_CLIENT_SECRET=votre-client-secret
OAUTH_REDIRECT_URI=https://sarfx.io/auth/login/google/callback
SECRET_KEY=votre-secret-key-genere
REDIS_URL=redis://localhost:6379/0
FLASK_ENV=production

# Sauvegarder et quitter (Ctrl+X, Y, Enter)

# Redémarrer l'application
systemctl restart sarfx-enhanced
```

### Installation Redis (si pas déjà installé)

```bash
# Ubuntu/Debian
apt update
apt install redis-server -y

# Démarrer Redis
systemctl start redis-server
systemctl enable redis-server

# Vérifier que Redis fonctionne
redis-cli ping
# Devrait répondre: PONG
```

---

## 🧪 Test de la Configuration

### 1. Vérifier les logs

```bash
# Voir les logs de l'application
journalctl -u sarfx-enhanced -f
```

Vous devriez voir :
```
✅ Google OAuth configured successfully
```

### 2. Tester manuellement

1. Accédez à https://sarfx.io/auth/login
2. Cliquez sur "Continuer avec Google"
3. Connectez-vous avec un compte Google
4. Vérifiez la redirection vers /app/

### 3. Vérifier en base de données

```javascript
// MongoDB
db.users.find({google_id: {$exists: true}})
```

---

## ⚠️ Sécurité - Points Importants

### ✅ À faire

- [ ] Générer une SECRET_KEY unique et longue (min 32 caractères)
- [ ] Configurer HTTPS obligatoire en production
- [ ] Limiter les URIs de redirection au strict nécessaire
- [ ] Activer le mode "Published" sur l'écran de consentement une fois testé
- [ ] Configurer des alertes de sécurité Google Cloud

### ❌ À éviter

- Ne JAMAIS commiter les secrets dans Git
- Ne pas utiliser les mêmes credentials en dev et prod
- Ne pas exposer le Client Secret côté client (JavaScript)

---

## 🔄 Migration des Utilisateurs Existants

Les utilisateurs existants (email/password) peuvent lier leur compte Google :

1. Se connecter avec email/password
2. Dans Profil/Paramètres, cliquer "Lier compte Google"
3. Authentification Google
4. Le `google_id` est ajouté au compte existant

**OU**

1. Se connecter directement avec Google (même email)
2. Le système détecte l'email existant
3. Le compte est automatiquement lié

---

## 📊 Structure des données utilisateur

```javascript
{
  "_id": ObjectId("..."),
  "email": "user@gmail.com",
  "full_name": "John Doe",
  "password": "hash...", // null si Google-only
  "role": "user",
  "verified": true,
  "google_id": "123456789012345678901", // ID Google unique
  "google_picture": "https://lh3.googleusercontent.com/...",
  "google_linked_at": ISODate("2026-01-31T..."),
  "auth_provider": "google", // ou "email", ou "both"
  "created_at": ISODate("...")
}
```

---

## 🆘 Dépannage

### Erreur : "redirect_uri_mismatch"

**Cause** : L'URI de redirection ne correspond pas à ceux configurés dans Google Cloud.

**Solution** :
1. Vérifiez l'URL exacte dans les logs
2. Ajoutez-la dans Google Cloud Console > Credentials > URIs de redirection

### Erreur : "invalid_client"

**Cause** : Client ID ou Secret incorrect.

**Solution** :
1. Vérifiez les variables d'environnement
2. Régénérez les credentials si nécessaire

### Erreur : "access_denied"

**Cause** : L'utilisateur a refusé les permissions ou l'app n'est pas publiée.

**Solution** :
1. Vérifiez que l'email est dans les "Test users" (mode test)
2. Ou publiez l'application (passer en mode "In production")

---

## 📞 Support

Pour toute question :
- Email : support@sarfx.io
- Documentation Google : https://developers.google.com/identity/protocols/oauth2

---

*Dernière mise à jour : 31 Janvier 2026*
