# SarfX - Mapping Routes, Templates et Sélecteurs pour Tests Robot

## 📋 Vue d'ensemble

Ce document décrit toutes les routes, templates, sélecteurs et actions CRUD pour les tests automatisés Robot/Playwright avec sous-titres.

---

## 🔐 Authentification

### Page de Login

| Élément | Valeur |
|---------|--------|
| **URL** | `/auth/login` |
| **Template** | `app_login.html` |

### Boutons Quick Login (Connexion Rapide)

| Rôle | Bouton | Email | Password |
|------|--------|-------|----------|
| **Admin** | `Admin Demo` | `admin@sarfx.io` | `admin123` |
| **Bank** | `Bank Respo Demo` | `bank@attijariwafa.ma` | `bank123` |
| **User** | `User Demo` | `user@demo.com` | `demo123` |

### Sélecteurs Playwright pour Quick Login

```python
# Admin Demo Button
page.click('button:has-text("Admin Demo")')

# Bank Respo Demo Button
page.click('button:has-text("Bank Respo Demo")')

# User Demo Button
page.click('button:has-text("User Demo")')
```

---

## 📱 app_base.html - Structure de Navigation

### Sidebar Desktop (class: `wise-sidebar`)

```python
# Logo
page.click('a.wise-sidebar-logo')

# Menu Items (class: wise-nav-item)
page.click('a[href="/app/"]')              # Accueil
page.click('a[href="/app/wallets"]')       # Wallets
page.click('a[href="/app/converter"]')     # Exchange
page.click('a[href="/app/atms"]')          # ATMs
page.click('a[href="/app/beneficiaries"]') # Bénéficiaires
page.click('a[href="/app/transactions"]')  # Historique
page.click('a[href="/app/faq"]')           # FAQ
page.click('a[href="/app/rate-history"]')  # Historique Taux
page.click('a[href="/app/ai"]')            # IA Prédictions
page.click('a[href="/app/profile"]')       # Profil

# Section Admin (visible si admin/bank_superadmin)
page.click('a[href="/admin/"]')            # Admin Dashboard
page.click('a[href="/admin/users"]')       # Utilisateurs
page.click('a[href="/admin/banks"]')       # Banques
page.click('a[href="/admin/atms"]')        # ATMs Admin

# Section Bank Admin (visible si bank_admin)
page.click('a[href="/app/bank-settings"]') # Config Banque

# Footer
page.click('a[href="/app/settings"]')      # Réglages
page.click('button:has-text("Mode sombre")') # Toggle thème
page.click('a[href="/auth/logout"]')       # Déconnexion
```

### Mobile Bottom Nav (class: `wise-bottom-nav`)

```python
page.click('.wise-bottom-item[href="/app/"]')
page.click('.wise-bottom-item[href="/app/wallets"]')
page.click('.wise-bottom-item[href="/app/converter"]')
page.click('.wise-bottom-item[href="/app/atms"]')
page.click('.wise-bottom-item[href="/auth/logout"]')
```

---

## 👤 Routes Admin - Détails

### `/app/` - Dashboard App

| Élément | Valeur |
|---------|--------|
| **Template** | `app_dashboard.html` |
| **Sous-titre** | "Dashboard principal avec vue d'ensemble des activités" |

---

### `/admin/` - Dashboard Admin

| Élément | Valeur |
|---------|--------|
| **Template** | `admin_dashboard.html` |
| **Sous-titre** | "Tableau de bord administrateur avec statistiques globales" |

---

### `/admin/users` - Gestion Utilisateurs

| Élément | Valeur |
|---------|--------|
| **Template** | `admin_users.html` |
| **Sous-titre** | "Liste et gestion des comptes utilisateurs" |

#### Sélecteurs

```python
# Recherche
page.fill('#search-input', 'email@test.com')

# Filtres
page.select_option('#filter-role', 'admin')
page.select_option('#filter-status', 'active')

# Export CSV
page.click('a:has-text("CSV")')

# Liste utilisateurs
page.locator('.user-card')

# Actions sur un utilisateur
page.click('button[title="Voir détails"]')
page.click('button[onclick*="toggleUser"]')
page.click('button[onclick*="deleteUser"]')
```

#### Actions CRUD

| Action | Sélecteur | Description |
|--------|-----------|-------------|
| **View** | `button[onclick*="showUserDetails"]` | Voir détails utilisateur |
| **Toggle** | `button[onclick*="toggleUser"]` | Activer/Désactiver |
| **Delete** | `button[onclick*="deleteUser"]` | Supprimer utilisateur |
| **Export** | `a[href*="export_users"]` | Export CSV |

---

### `/app/wallets` - Gestion Wallets

| Élément | Valeur |
|---------|--------|
| **Template** | `app_wallets.html` |
| **Sous-titre** | "Portefeuilles multi-devises avec soldes et transactions" |

#### Sélecteurs

```python
# Total balance
page.locator('.wise-total-balance-card')
page.locator('.wise-total-value')

# Ajouter devise
page.click('button:has-text("Add Currency")')

# Wallet cards
page.locator('.wise-wallet-card')
page.click('.wise-wallet-card')

# Modal détails
page.locator('#walletDetailsModal')
page.click('.wise-modal-close')

# Tabs dans modal
page.click('.wise-modal-tab[data-tab="history"]')
page.click('.wise-modal-tab[data-tab="alerts"]')
page.click('.wise-modal-tab[data-tab="accounts"]')
```

---

### `/app/transactions` - Historique Transactions

| Élément | Valeur |
|---------|--------|
| **Template** | `app_transactions.html` |
| **Sous-titre** | "Historique complet des transactions et transferts" |

#### Sélecteurs

```python
page.locator('.wise-tx-item')
page.locator('.wise-tx-amount')
page.locator('.wise-tx-date')
```

---

### `/admin/banks` - Gestion Banques

| Élément | Valeur |
|---------|--------|
| **Template** | `admin_banks.html` |
| **Sous-titre** | "Administration des banques partenaires" |

#### Sélecteurs

```python
# Ajouter banque
page.click('a:has-text("Ajouter")')

# Recherche
page.fill('#search-input', 'attijariwafa')

# Liste banques
page.locator('.bank-card')

# Actions
page.click('a:has-text("Modifier")')
page.click('button[onclick*="toggleBank"]')
page.click('button[onclick*="deleteBank"]')
```

#### Actions CRUD

| Action | Sélecteur | Description |
|--------|-----------|-------------|
| **Create** | `a[href*="add_bank"]` | Ajouter banque |
| **Read** | `.bank-card` | Voir banque |
| **Update** | `a[href*="edit_bank"]` | Modifier banque |
| **Delete** | `button[onclick*="deleteBank"]` | Supprimer banque |
| **Toggle** | `button[onclick*="toggleBank"]` | Activer/Désactiver |

---

### `/app/beneficiaries` - Bénéficiaires

| Élément | Valeur |
|---------|--------|
| **Template** | `app_beneficiaries.html` |
| **Sous-titre** | "Gestion des bénéficiaires pour les transferts" |

#### Sélecteurs

```python
# Ajouter
page.click('button:has-text("Ajouter")')

# Stats
page.locator('.stat-card')
page.locator('.stat-value')

# Liste
page.locator('.beneficiary-card')
page.locator('.beneficiary-avatar')
page.locator('.beneficiary-name')

# Actions
page.click('button[onclick*="sendToBeneficiary"]')
page.click('button[onclick*="editBeneficiary"]')

# Historique par bénéficiaire
page.locator('.beneficiary-history')
page.locator('.history-item')
```

---

### `/app/converter` - Convertisseur

| Élément | Valeur |
|---------|--------|
| **Template** | `app_converter.html` |
| **Sous-titre** | "Convertisseur de devises avec comparaison des taux en temps réel" |

#### Sélecteurs

```python
# Exchange card
page.fill('#smart-amount', '1000')
page.select_option('#from-currency', 'USD')
page.select_option('#to-currency', 'MAD')
page.locator('#recipient-amount')

# Refresh
page.click('button:has-text("Refresh Rates")')

# Tabs
page.click('.wise-tab[data-tab="providers"]')
page.click('.wise-tab[data-tab="pairs"]')
page.click('.wise-tab[data-tab="alerts"]')
```

---

### `/app/atms` - ATMs

| Élément | Valeur |
|---------|--------|
| **Template** | `app_atms.html` |
| **Sous-titre** | "Localisation des distributeurs automatiques à proximité" |

---

### `/app/ai` - IA Prédictions

| Élément | Valeur |
|---------|--------|
| **Template** | `app_ai.html` |
| **Sous-titre** | "Prédictions de taux de change par intelligence artificielle" |

---

### `/app/settings` - Paramètres

| Élément | Valeur |
|---------|--------|
| **Template** | `app_settings.html` |
| **Sous-titre** | "Configuration du compte et préférences utilisateur" |

---

## 🎬 Scénarios de Démo avec Sous-titres

### Admin Demo

| Étape | Route | Sous-titre |
|-------|-------|------------|
| 1 | `/auth/login` | "Connexion avec le compte administrateur" |
| 2 | `/app/` | "Dashboard principal avec vue d'ensemble" |
| 3 | `/admin/` | "Tableau de bord administrateur" |
| 4 | `/admin/users` | "Gestion des utilisateurs" |
| 5 | `/app/wallets` | "Portefeuilles multi-devises" |
| 6 | `/app/transactions` | "Historique des transactions" |
| 7 | `/admin/banks` | "Administration des banques partenaires" |
| 8 | `/app/beneficiaries` | "Gestion des bénéficiaires" |
| 9 | `/app/converter` | "Comparaison des taux en temps réel" |
| 10 | `/app/atms` | "Localisation des distributeurs" |
| 11 | `/app/ai` | "Prédictions par intelligence artificielle" |
| 12 | `/app/settings` | "Configuration du compte" |

### Bank Demo

| Étape | Route | Sous-titre |
|-------|-------|------------|
| 1 | `/auth/login` | "Connexion compte responsable banque" |
| 2 | `/app/` | "Tableau de bord banque" |
| 3 | `/app/wallets` | "Portefeuilles de la banque" |
| 4 | `/app/converter` | "Taux de change" |
| 5 | `/app/atms` | "ATMs de la banque" |
| 6 | `/app/transactions` | "Historique des opérations" |
| 7 | `/app/bank-settings` | "Configuration API banque" |
| 8 | `/app/ai` | "Prévisions et analyses" |
| 9 | `/app/rate-history` | "Historique des taux" |
| 10 | `/app/profile` | "Profil utilisateur" |
| 11 | `/app/settings` | "Préférences" |

### User Demo

| Étape | Route | Sous-titre |
|-------|-------|------------|
| 1 | `/auth/login` | "Connexion utilisateur standard" |
| 2 | `/app/` | "Mon tableau de bord" |
| 3 | `/app/wallets` | "Mes portefeuilles" |
| 4 | `/app/converter` | "Convertir mes devises" |
| 5 | `/app/atms` | "Trouver un distributeur" |
| 6 | `/app/beneficiaries` | "Mes bénéficiaires" |
| 7 | `/app/transactions` | "Mon historique" |
| 8 | `/app/ai` | "Prédictions de taux" |
| 9 | `/app/rate-history` | "Évolution des taux" |
| 10 | `/app/faq` | "Aide et support" |
| 11 | `/app/profile` | "Mon profil" |
| 12 | `/app/settings` | "Mes préférences" |

---

## 📁 Structure des Outputs

```
sarfx_demo_output/
├── demo_admin_YYYYMMDD_HHMMSS.webm
├── demo_bank_YYYYMMDD_HHMMSS.webm
├── demo_user_YYYYMMDD_HHMMSS.webm
├── admin_dashboard.png
├── admin__admin_.png
├── admin__admin_users.png
└── ...
```

---

## 🔧 Commandes d'Exécution

```bash
python sarfx_demo.py --role admin --visible
python sarfx_demo.py --role bank --visible
python sarfx_demo.py --role user --visible
python sarfx_demo.py --role admin --headless
```
| `/app/ai` | `app_ai.html` | Prévisions IA |
| `/app/rate-history` | `app_rate_history.html` | Historique des taux |
| `/app/faq` | `app_faq.html` | Questions fréquentes |
| `/app/profile` | `app_profile.html` | Profil utilisateur |
| `/app/settings` | `app_settings.html` | Paramètres |

---

## 🏦 Routes Bank Respo

| Route | Template | Description |
|-------|----------|-------------|
| `/app/` | `app_dashboard.html` | Dashboard principal |
| `/app/wallets` | `app_wallets.html` | Portefeuilles |
| `/app/converter` | `app_converter.html` | Convertisseur |
| `/app/atms` | `app_atms.html` | ATMs |
| `/app/transactions` | `app_transactions.html` | Transactions |
| `/app/bank-settings` | `app_bank_settings.html` | Configuration banque |
| `/app/ai` | `app_ai.html` | Prévisions IA |
| `/app/rate-history` | `app_rate_history.html` | Historique taux |
| `/app/profile` | `app_profile.html` | Profil |
| `/app/settings` | `app_settings.html` | Paramètres |

---

## 🛡️ Routes Admin

| Route | Template | Description |
|-------|----------|-------------|
| `/admin/` | `admin_dashboard.html` | Dashboard admin |
| `/admin/users` | `admin_users.html` | Gestion utilisateurs |
| `/admin/wallets` | `admin_wallets.html` | Gestion wallets |
| `/admin/transactions` | `admin_transactions.html` | Gestion transactions |
| `/admin/banks` | `admin_banks.html` | Gestion banques |
| `/admin/atms` | `admin_atms.html` | Gestion ATMs |
| `/admin/sources` | `admin_sources.html` | Sources de données |
| `/admin/beneficiaries` | `admin_beneficiaries.html` | Bénéficiaires |
| `/admin/demo` | `admin_demo.html` | Page démo Robot |

---

## 🎯 Sélecteurs Communs

### Navigation Sidebar

```python
# Menu items (data-lucide icons)
page.click('a[href="/app/wallets"]')
page.click('a[href="/app/converter"]')
page.click('a[href="/app/atms"]')
page.click('a[href="/admin/"]')
```

### Formulaire de Login (si besoin)

```python
# Champs
page.fill('input[name="email"]', email)
page.fill('input[name="password"]', password)
page.click('button[type="submit"]')
```

### Logout

```python
page.click('a[href="/auth/logout"]')
# ou
page.click('button:has-text("Déconnexion")')
```

---

## 🤖 Scénarios de Test Robot

### Scénario Admin Complet

```
1. Aller sur /auth/login
2. Cliquer sur "Admin Demo"
3. Attendre redirection vers /app/
4. Naviguer vers /admin/
5. Parcourir: /admin/users → /admin/wallets → /admin/transactions → /admin/banks → /admin/atms → /admin/sources
6. Revenir sur /app/wallets, /app/converter
7. Screenshot chaque page
```

### Scénario Bank Complet

```
1. Aller sur /auth/login
2. Cliquer sur "Bank Respo Demo"
3. Attendre redirection vers /app/
4. Parcourir: /app/wallets → /app/converter → /app/atms → /app/transactions → /app/bank-settings → /app/ai
5. Screenshot chaque page
```

### Scénario User Complet

```
1. Aller sur /auth/login
2. Cliquer sur "User Demo"
3. Attendre redirection vers /app/
4. Parcourir: /app/wallets → /app/converter → /app/atms → /app/beneficiaries → /app/transactions → /app/ai → /app/faq → /app/profile
5. Screenshot chaque page
```

---

## 📁 Structure des Outputs

```
sarfx_demo_output/
├── demo_admin_20260130_143022/
│   └── video.webm
├── demo_bank_20260130_143522/
│   └── video.webm
├── demo_user_20260130_144022/
│   └── video.webm
├── admin__.png
├── admin__admin_.png
├── admin__admin_users.png
├── bank__app_wallets.png
├── user__app_converter.png
└── ...
```

---

## 🔧 Commandes d'Exécution

```bash
# Admin visible
python sarfx_demo.py --role admin --visible

# Bank visible
python sarfx_demo.py --role bank --visible

# User visible
python sarfx_demo.py --role user --visible

# Headless (sans affichage)
python sarfx_demo.py --role admin --headless
```

---

## ⚠️ Notes Importantes

1. **Quick Login Buttons** : Utilisez les boutons de connexion rapide plutôt que de remplir le formulaire
2. **Attente après login** : Attendre 2-3 secondes après le clic pour la redirection
3. **Screenshots** : Prendre un screenshot après chaque navigation
4. **Vidéo** : Enregistrer automatiquement en 1920x1080
5. **slow_mo** : Utiliser 300-500ms pour des démos lisibles
