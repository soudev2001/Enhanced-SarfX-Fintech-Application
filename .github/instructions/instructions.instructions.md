---
applyTo: '**'
---

# 🏦 SarfX Enhanced - Instructions pour le Développement IA

## ⚠️ RÈGLE CRITIQUE #1 - NE JAMAIS DÉMARRER L'APPLICATION

```
🚫 INTERDIT: python run.py, flask run, ou tout démarrage de serveur
✅ L'utilisateur gère le serveur lui-même
```

L'application tourne DÉJÀ sur le port **5050** ou **5051**. Ne jamais:
- Exécuter `python run.py`
- Exécuter `flask run`
- Démarrer un serveur de quelque manière que ce soit

---

## 🔐 Authentification pour Tests API (curl)

### Credentials Admin
```bash
# Email: admin@sarfx.io
# Password: admin123
```

### Processus de Login avec curl
```bash
# 1. Obtenir le CSRF token
CSRF=$(curl -s -c /tmp/cookies.txt "http://127.0.0.1:5050/auth/login" | grep -oP 'name="csrf_token" value="\K[^"]+')

# 2. Se connecter
curl -s -b /tmp/cookies.txt -c /tmp/cookies.txt -X POST "http://127.0.0.1:5050/auth/login" \
  -d "email=admin@sarfx.io&password=admin123&csrf_token=$CSRF" -L

# 3. Tester une API authentifiée
curl -s -b /tmp/cookies.txt "http://127.0.0.1:5050/api/user/profile" | jq
```

### Autres Comptes de Test
| Role | Email | Password |
|------|-------|----------|
| Admin | admin@sarfx.io | admin123 |
| Bank | bank@sarfx.io | bank123 |
| User | user@sarfx.io | user123 |

---

## 🗄️ MongoDB Atlas - Configuration

### URL de Connexion
```
mongodb+srv://soufiane:gogo@cluster0.05omqhe.mongodb.net/SarfX_Enhanced
```

### Collections Principales

#### `users` - Utilisateurs
```javascript
{
  _id: ObjectId,
  email: String,              // Unique
  password: String,           // Hash bcrypt
  first_name: String,
  last_name: String,
  role: String,               // "admin", "bank", "user"
  status: String,             // "active", "inactive", "pending"
  avatar: String,             // URL image

  // Préférences
  theme: String,              // "light", "dark"
  accent_color: String,       // "orange", "blue", "green", etc.
  notification_preferences: {
    email: Boolean,
    push: Boolean,
    sms: Boolean
  },

  // 2FA
  two_factor_enabled: Boolean,
  two_factor_secret: String,
  two_factor_backup_codes: [String],

  // Métadonnées
  created_at: Date,
  updated_at: Date,
  last_login: Date,
  login_count: Number
}
```

#### `wallets` - Portefeuilles
```javascript
{
  _id: ObjectId,
  user_id: ObjectId,          // Référence users._id
  balances: {
    USD: Number,
    EUR: Number,
    MAD: Number,
    GBP: Number,
    CAD: Number,
    AED: Number,
    SAR: Number,
    TRY: Number
  },
  is_active: Boolean,
  created_at: Date,
  updated_at: Date
}
```

#### `transactions` - Transactions
```javascript
{
  _id: ObjectId,
  user_id: ObjectId,
  transaction_id: String,     // "TXN-XXXXXX" unique
  type: String,               // "exchange", "transfer", "deposit", "withdrawal"
  status: String,             // "pending", "completed", "failed", "cancelled"

  // Détails échange
  from_currency: String,
  to_currency: String,
  from_amount: Number,
  to_amount: Number,
  rate: Number,

  // Bénéficiaire (si transfer)
  beneficiary_id: ObjectId,
  beneficiary_name: String,

  // Métadonnées
  description: String,
  created_at: Date,
  completed_at: Date
}
```

#### `banks` - Banques
```javascript
{
  _id: ObjectId,
  name: String,
  code: String,               // "BOA", "AWB", "CIH", etc.
  logo: String,               // URL image
  color: String,              // Couleur hex
  is_active: Boolean,
  swift_code: String,
  country: String,
  created_at: Date
}
```

#### `atm_locations` - Distributeurs
```javascript
{
  _id: ObjectId,
  bank_code: String,          // Référence banks.code
  name: String,
  address: String,
  city: String,
  latitude: Number,
  longitude: Number,
  services: [String],         // ["cash", "deposit", "transfer"]
  is_active: Boolean,
  created_at: Date
}
```

#### `beneficiaries` - Bénéficiaires
```javascript
{
  _id: ObjectId,
  user_id: ObjectId,
  name: String,
  email: String,
  phone: String,
  bank_name: String,
  account_number: String,
  iban: String,
  swift_code: String,
  country: String,
  is_favorite: Boolean,
  created_at: Date
}
```

#### `exchange_rates` - Taux de Change
```javascript
{
  _id: ObjectId,
  base_currency: String,
  target_currency: String,
  rate: Number,
  source: String,             // "api", "manual"
  updated_at: Date
}
```

#### `trusted_devices` - Appareils de Confiance (2FA)
```javascript
{
  _id: ObjectId,
  user_id: ObjectId,
  device_token: String,
  device_name: String,
  browser: String,
  os: String,
  ip_address: String,
  created_at: Date,
  expires_at: Date
}
```

---

## 🏗️ Architecture de l'Application

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (Jinja2 + JS)                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  Templates  │  │   Static    │  │   Service Worker    │ │
│  │  (HTML)     │  │  (CSS/JS)   │  │   (sw.js - PWA)     │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│                     FLASK APPLICATION                        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                    Routes Layer                       │   │
│  │  ┌────────────┐ ┌────────────┐ ┌──────────────────┐  │   │
│  │  │ auth_      │ │ app_       │ │ api_routes.py    │  │   │
│  │  │ routes.py  │ │ routes.py  │ │ (REST API)       │  │   │
│  │  └────────────┘ └────────────┘ └──────────────────┘  │   │
│  │  ┌────────────┐ ┌────────────┐ ┌──────────────────┐  │   │
│  │  │ admin_     │ │ admin_bank │ │ landing_         │  │   │
│  │  │ routes.py  │ │ _routes.py │ │ routes.py        │  │   │
│  │  └────────────┘ └────────────┘ └──────────────────┘  │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                   Services Layer                      │   │
│  │  ┌────────────┐ ┌────────────┐ ┌──────────────────┐  │   │
│  │  │ db_service │ │ wallet_    │ │ exchange_        │  │   │
│  │  │ .py        │ │ service.py │ │ service.py       │  │   │
│  │  └────────────┘ └────────────┘ └──────────────────┘  │   │
│  │  ┌────────────┐ ┌────────────┐ ┌──────────────────┐  │   │
│  │  │ email_     │ │ ai_service │ │ two_factor_      │  │   │
│  │  │ service.py │ │ .py        │ │ service.py       │  │   │
│  │  └────────────┘ └────────────┘ └──────────────────┘  │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│                    MONGODB ATLAS                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   │
│  │  users   │ │ wallets  │ │ banks    │ │ transactions │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────┘   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   │
│  │ atm_     │ │beneficia │ │exchange_ │ │ trusted_     │   │
│  │locations │ │ ries     │ │ rates    │ │ devices      │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Structure des Routes

### `auth_routes.py` - Authentification
| Route | Méthode | Description |
|-------|---------|-------------|
| `/auth/login` | GET/POST | Page de connexion |
| `/auth/logout` | GET | Déconnexion |
| `/auth/register` | GET/POST | Inscription |
| `/auth/forgot-password` | GET/POST | Mot de passe oublié |
| `/auth/reset-password/<token>` | GET/POST | Réinitialisation |
| `/auth/google/login` | GET | OAuth Google |
| `/auth/google/callback` | GET | Callback OAuth |

### `app_routes.py` - Application Utilisateur
| Route | Méthode | Description |
|-------|---------|-------------|
| `/app/` | GET | Dashboard utilisateur |
| `/app/home` | GET | Page d'accueil |
| `/app/wallets` | GET | Portefeuilles |
| `/app/transactions` | GET | Historique transactions |
| `/app/converter` | GET | Convertisseur devise |
| `/app/beneficiaries` | GET | Liste bénéficiaires |
| `/app/atms` | GET | Carte des DAB |
| `/app/settings` | GET | Paramètres utilisateur |
| `/app/profile` | GET | Profil utilisateur |
| `/app/ai` | GET | Assistant IA |

### `admin_routes.py` - Administration
| Route | Méthode | Description |
|-------|---------|-------------|
| `/admin/` | GET | Dashboard admin |
| `/admin/users` | GET | Gestion utilisateurs |
| `/admin/wallets` | GET | Gestion portefeuilles |
| `/admin/transactions` | GET | Toutes transactions |
| `/admin/banks` | GET | Gestion banques |
| `/admin/atms` | GET | Gestion DAB |
| `/admin/sources` | GET | Sources de taux |
| `/admin/demo` | GET | Mode démo |

### `api_routes.py` - API REST
| Route | Méthode | Description |
|-------|---------|-------------|
| `/api/user/profile` | GET | Profil utilisateur |
| `/api/user/preferences` | GET/POST | Préférences |
| `/api/wallets` | GET | Liste portefeuilles |
| `/api/wallets/balance` | GET | Soldes |
| `/api/transactions` | GET | Liste transactions |
| `/api/exchange/rates` | GET | Taux de change |
| `/api/exchange/convert` | POST | Conversion |
| `/api/beneficiaries` | GET/POST | Bénéficiaires |
| `/api/2fa/status` | GET | Statut 2FA |
| `/api/2fa/setup` | POST | Configuration 2FA |
| `/api/2fa/verify` | POST | Vérification code |
| `/api/banks` | GET | Liste banques |
| `/api/atms` | GET | Liste DAB |

---

## 🎨 Templates Actifs

### Templates Utilisateur (`app_*.html`)
| Template | Description | Route |
|----------|-------------|-------|
| `app_base.html` | Base template avec navbar | - |
| `app_home.html` | Dashboard principal | `/app/home` |
| `app_wallets.html` | Gestion portefeuilles | `/app/wallets` |
| `app_transactions.html` | Historique | `/app/transactions` |
| `app_converter.html` | Convertisseur | `/app/converter` |
| `app_beneficiaries.html` | Bénéficiaires | `/app/beneficiaries` |
| `app_send_beneficiary.html` | Envoi à bénéficiaire | `/app/send` |
| `app_atms.html` | Carte DAB | `/app/atms` |
| `app_settings.html` | Paramètres | `/app/settings` |
| `app_profile.html` | Profil | `/app/profile` |
| `app_ai.html` | Assistant IA | `/app/ai` |
| `app_faq.html` | FAQ | `/app/faq` |
| `app_wallet_recharge.html` | Recharge | `/app/recharge` |
| `app_wallet_swap.html` | Swap devises | `/app/swap` |
| `app_rate_history.html` | Historique taux | `/app/rates` |

### Templates Admin (`admin_*.html`)
| Template | Description | Route |
|----------|-------------|-------|
| `admin_dashboard.html` | Dashboard admin | `/admin/` |
| `admin_users.html` | Gestion users | `/admin/users` |
| `admin_wallets.html` | Gestion wallets | `/admin/wallets` |
| `admin_transactions.html` | Transactions | `/admin/transactions` |
| `admin_banks.html` | Gestion banques | `/admin/banks` |
| `admin_atms.html` | Gestion DAB | `/admin/atms` |
| `admin_sources.html` | Sources taux | `/admin/sources` |
| `admin_demo.html` | Mode démo | `/admin/demo` |
| `admin_beneficiaries.html` | Bénéficiaires | `/admin/beneficiaries` |

### Templates Auth (`auth/`)
| Template | Description |
|----------|-------------|
| `auth/login.html` | Page connexion |
| `auth/register.html` | Page inscription |
| `auth/forgot_password.html` | Mot de passe oublié |
| `auth/reset_password.html` | Réinitialisation |

### Templates Landing
| Template | Description |
|----------|-------------|
| `landing.html` | Page d'accueil publique |
| `landing_new.html` | Nouvelle landing |

---

## 🔧 Services Principaux

### `db_service.py`
```python
# Connexion MongoDB
from app.services.db_service import get_db
db = get_db()
users = db.users
wallets = db.wallets
```

### `wallet_service.py`
```python
# Opérations sur les portefeuilles
get_user_wallets(user_id)
update_balance(wallet_id, currency, amount)
create_wallet(user_id)
```

### `exchange_service.py`
```python
# Taux de change et conversions
get_exchange_rate(from_currency, to_currency)
convert_currency(amount, from_currency, to_currency)
get_all_rates()
```

### `two_factor_service.py`
```python
# Authentification à deux facteurs
generate_2fa_secret(user_id)
verify_2fa_code(user_id, code)
get_2fa_status(user_id)
generate_backup_codes(user_id)
trust_device(user_id, device_info)
```

### `ai_service.py`
```python
# Service d'IA pour le chatbot
process_message(user_id, message)
get_ai_response(context, query)
```

---

## 🎯 Couleurs d'Accent Disponibles

```javascript
const ACCENT_COLORS = {
  orange: '#F97316',
  blue: '#3B82F6',
  green: '#10B981',
  purple: '#8B5CF6',
  pink: '#EC4899',
  red: '#EF4444',
  teal: '#14B8A6',
  amber: '#F59E0B',
  cyan: '#06B6D4',
  indigo: '#6366F1',
  lime: '#84CC16',
  rose: '#F43F5E'
};
```

---

## 🛡️ Décorateurs Importants

```python
from app.decorators import login_required, admin_required, bank_required

@login_required
def protected_route():
    # Nécessite une session utilisateur
    pass

@admin_required
def admin_only_route():
    # Nécessite role == "admin"
    pass

@bank_required
def bank_only_route():
    # Nécessite role == "bank"
    pass
```

---

## 📝 Conventions de Code

### Python (Flask)
- Utiliser `snake_case` pour fonctions et variables
- Routes en minuscules avec tirets: `/api/user-profile`
- Docstrings pour toutes les fonctions publiques
- Type hints recommandés
- Gestion d'erreurs avec try/except et logs

### JavaScript
- Utiliser `camelCase` pour fonctions et variables
- Classes en `PascalCase`
- Préférer `const` à `let`, éviter `var`
- Async/await pour les appels API

### Templates (Jinja2)
- Blocs nommés: `{% block content %}{% endblock %}`
- Filtres: `{{ date | format_date }}`
- Macros pour composants réutilisables

---

## 🚀 Commandes Utiles

```bash
# Vérifier que l'app tourne
curl -s http://127.0.0.1:5050/health

# Logs en temps réel
tail -f /tmp/flask.log

# Tester une API avec auth
curl -s -b /tmp/cookies.txt "http://127.0.0.1:5050/api/wallets" | jq

# Seed la base de données
python scripts/seed_admin.py
```

---

## ⚠️ Points d'Attention

1. **ObjectId**: Toujours utiliser `from bson import ObjectId` pour les requêtes MongoDB
2. **CSRF**: Inclure le token dans tous les formulaires POST
3. **Session**: Vérifier `session.get('user_id')` avant d'accéder aux données utilisateur
4. **JSON API**: Toujours retourner `jsonify()` avec les bons codes HTTP
5. **Erreurs**: Logger les erreurs avec `current_app.logger.error()`

---

## 📚 Documentation Additionnelle

- [DEPLOYMENT.md](../../docs/DEPLOYMENT.md) - Guide de déploiement
- [GOOGLE_OAUTH_SETUP.md](../../docs/GOOGLE_OAUTH_SETUP.md) - Configuration OAuth
- [GUIDE_QUICKSTART.md](../../docs/GUIDE_QUICKSTART.md) - Guide de démarrage rapide