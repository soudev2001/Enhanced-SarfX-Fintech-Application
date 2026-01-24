# 🚀 Nouvelles Fonctionnalités SarfX

## 📋 Résumé des Modifications

### 1. ✅ Correction de l'Erreur 500 sur /app/beneficiaries
- Ajout de gestion d'erreurs robuste
- Protection contre les erreurs de base de données
- Messages d'erreur clairs pour l'utilisateur

### 2. 🤖 Intégration Chatbot AI avec Gemini
**Service Backend**: `app/services/chatbot_service.py`
- API Gemini 2.0 Flash intégrée
- Contexte SarfX personnalisé
- Gestion d'erreurs complète

**Widget Frontend**: `app/static/js/chatbot.js`
- Interface moderne et responsive
- Animation de saisie
- Design cohérent avec SarfX

**Intégration**:
- ✅ Landing page (`landing.html`)
- ✅ Application (`app_base.html`)
- Widget accessible partout

**Route API**: `/api/chatbot/message` (POST)

### 3. 👥 Système de Rôles Avancé

#### Rôles Disponibles:
- **user**: Utilisateur standard
- **bank_user**: Utilisateur associé à une banque
- **admin**: Administrateur système complet
- **admin_sr_bank**: Administrateur senior banque (vue d'ensemble)
- **admin_associate_bank**: Admin associé banque (contrôle API)

#### Décorateurs de Protection:
```python
@role_required('admin', 'admin_sr_bank')
def protected_route():
    # Accès limité aux rôles spécifiés
    pass
```

### 4. 🎨 Dashboards Basés sur les Rôles

#### Admin SR Bank (`/app/admin-sr-bank`)
- Vue d'ensemble de toutes les banques
- Statistiques globales (ATMs, utilisateurs, transactions)
- Volume total des transactions
- Actions rapides (gérer banques, ATMs, utilisateurs)

#### Admin Associate Bank (`/app/admin-associate-bank`)
- Informations de la banque associée
- Statistiques spécifiques à la banque
- Gestion des ATMs de la banque
- Contrôle API

### 5. 🔌 Contrôle API pour Banques (`/app/admin-associate-bank/api-control`)

**Fonctionnalités**:
- Génération/régénération de clés API
- Configuration webhook
- Limite de requêtes personnalisable
- Synchronisation des données
- Documentation API intégrée

**Routes API**:
- `POST /api/bank-settings/regenerate-keys` - Régénérer les clés
- `POST /api/bank-settings/sync` - Synchroniser les données

**Sécurité**:
- Clés API format: `sk_` + token sécurisé
- Secret API token 48 caractères
- Historique des régénérations

### 6. 🏧 Gestion des ATMs (`/app/admin-associate-bank/atm-management`)

**Interface Admin**:
- Liste complète des ATMs
- Ajout/modification/suppression
- Coordonnées GPS (latitude/longitude)
- Statut actif/inactif

**Routes API**:
- `GET /api/atms` - Liste des ATMs
- `POST /api/atms` - Créer un ATM
- `PUT /api/atms/<id>` - Modifier un ATM
- `DELETE /api/atms/<id>` - Supprimer un ATM

### 7. 🗺️ OpenStreetMaps Intégration

**Déjà intégré dans** `app_atms.html`:
- Leaflet.js pour la cartographie
- Marqueurs interactifs pour chaque banque/ATM
- Popup avec informations détaillées
- Filtre par ville et recherche
- Vue centrée sur le Maroc

**Villes principales**:
- Casablanca, Rabat, Marrakech
- Tanger, Fès, Agadir

## 🛠️ Installation et Configuration

### 1. Installer les Dépendances
```bash
pip install -r requirements.txt
```

### 2. Configurer la Clé API Gemini
Dans `.env`:
```
GEMINI_API_KEY=AIzaSyB5LeO-IZ2OHzec8XgxqVxXMgWMHOwQKag
```

### 3. Exécuter la Migration des Rôles
```bash
python migrate_roles.py
```

Cela va:
- ✅ Ajouter le rôle 'user' aux utilisateurs existants
- ✅ Créer les index pour optimiser les recherches
- ✅ Ajouter les champs API aux banques
- ✅ Créer des comptes admin de test

### 4. Comptes de Test Créés
```
Admin SR Bank:
  Email: admin.sr@sarfx.io
  Password: AdminSR123!
  Rôle: admin_sr_bank

Admin Associate Bank:
  Email: admin.bank@sarfx.io
  Password: AdminBank123!
  Rôle: admin_associate_bank
```

## 📁 Nouveaux Fichiers

### Services
- `app/services/chatbot_service.py` - Service chatbot Gemini

### Templates
- `app/templates/admin_sr_bank_dashboard.html`
- `app/templates/admin_associate_bank_dashboard.html`
- `app/templates/admin_api_control.html`
- `app/templates/admin_atm_management.html`

### Static
- `app/static/js/chatbot.js` - Widget chatbot

### Scripts
- `migrate_roles.py` - Script de migration

## 🔄 Routes Modifiées

### app_routes.py
- Ajout de `role_required()` decorator
- Routes admin SR bank
- Routes admin associate bank
- Route contrôle API
- Route gestion ATMs
- Correction route beneficiaries

### api_routes.py
- Route chatbot `/api/chatbot/message`
- CRUD ATMs `/api/atms`
- Régénération clés `/api/bank-settings/regenerate-keys`
- Synchronisation `/api/bank-settings/sync`

## 🎯 Fonctionnalités par Rôle

| Fonctionnalité | User | Bank User | Admin Associate | Admin SR | Admin |
|----------------|------|-----------|-----------------|----------|-------|
| Conversions | ✅ | ✅ | ✅ | ✅ | ✅ |
| Wallets | ✅ | ✅ | ✅ | ✅ | ✅ |
| Bénéficiaires | ✅ | ✅ | ✅ | ✅ | ✅ |
| Localiser ATMs | ✅ | ✅ | ✅ | ✅ | ✅ |
| Chatbot AI | ✅ | ✅ | ✅ | ✅ | ✅ |
| Dashboard Banque | ❌ | ❌ | ✅ | ✅ | ✅ |
| Gérer ATMs Banque | ❌ | ❌ | ✅ | ✅ | ✅ |
| Contrôle API | ❌ | ❌ | ✅ | ✅ | ✅ |
| Vue Globale | ❌ | ❌ | ❌ | ✅ | ✅ |
| Admin Système | ❌ | ❌ | ❌ | ❌ | ✅ |

## 🔒 Sécurité

### Protection des Routes
- Toutes les routes admin protégées par `@role_required`
- Vérification des rôles côté serveur
- Isolation des données bancaires

### API Keys
- Format sécurisé avec préfixe `sk_`
- Tokens générés avec `secrets.token_urlsafe()`
- Historique des régénérations

### Gestion des Erreurs
- Try-catch sur toutes les routes critiques
- Messages d'erreur utilisateur-friendly
- Logs détaillés pour le debugging

## 🧪 Tests

### Tester le Chatbot
```javascript
fetch('/api/chatbot/message', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    message: 'Comment fonctionne SarfX?'
  })
})
```

### Tester l'API ATMs
```bash
# Liste des ATMs
curl -X GET http://localhost:5000/api/atms \
  -H "Cookie: session=..."

# Ajouter un ATM
curl -X POST http://localhost:5000/api/atms \
  -H "Content-Type: application/json" \
  -H "Cookie: session=..." \
  -d '{
    "name": "ATM Test",
    "address": "123 Rue Test",
    "city": "Casablanca",
    "latitude": 33.5731,
    "longitude": -7.5898
  }'
```

## 📊 Base de Données

### Nouvelles Collections
- `atms` - Stockage des distributeurs automatiques

### Champs Ajoutés

#### users
- `role` (string) - Rôle de l'utilisateur
- `bank_code` (string) - Code banque associée

#### banks
- `api_key` (string) - Clé API
- `api_secret` (string) - Secret API
- `webhook_url` (string) - URL webhook
- `api_active` (boolean) - Statut API
- `api_rate_limit` (number) - Limite requêtes
- `last_api_sync` (datetime) - Dernière synchro
- `api_keys_regenerated_at` (datetime) - Date régénération

#### atms
```javascript
{
  name: String,
  address: String,
  city: String,
  latitude: Number,
  longitude: Number,
  bank_code: String,
  is_active: Boolean,
  created_at: Date
}
```

## 🚀 Déploiement

1. Faire un backup de la base de données
2. Exécuter `migrate_roles.py`
3. Vérifier que le chatbot fonctionne
4. Tester les nouveaux dashboards
5. Valider les permissions par rôle

## 📞 Support

Pour toute question sur les nouvelles fonctionnalités:
- Documentation API: `/docs/api`
- Email: support@sarfx.io

## ✨ Améliorations Futures

- [ ] Historique des appels API par banque
- [ ] Analytics avancés pour admin SR
- [ ] Export de données bancaires
- [ ] Notifications push pour événements API
- [ ] Tableau de bord temps réel
- [ ] Intégration SMS pour codes ATM
- [ ] Support multi-langue pour chatbot
