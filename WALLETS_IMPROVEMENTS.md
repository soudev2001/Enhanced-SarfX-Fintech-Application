# 💼 Documentation Wallets - Améliorations

## 🎨 Nouvelles Fonctionnalités

### Pages Utilisateur (`app_wallets.html`)

#### ✨ Design & UI
- **Total Balance Card**: Carte gradient orange affichant le solde total en USD
- **Wallets Grid Responsive**: Grille adaptative pour tous les écrans
- **Logos de Devises**: Drapeaux emoji pour chaque devise (🇺🇸 🇪🇺 🇬🇧 🇲🇦 etc.)
- **Glassmorphism**: Effet de verre moderne avec backdrop-filter
- **Animations Smooth**: Transitions et hover effects élégants

#### 🔧 Fonctionnalités
1. **Ajouter une Devise**
   - Modal responsive avec grille de devises
   - 8 devises disponibles: USD, EUR, GBP, MAD, CHF, CAD, AED, SAR
   - Sélection visuelle avec drapeaux

2. **Détails de Portefeuille (Modal)**
   - 3 Tabs:
     - **Historique**: Liste des transactions
     - **Statistiques**: Total reçu, envoyé, nombre de transactions
     - **Actions**: Envoyer, Recevoir, Convertir, Retirer

3. **Transactions Récentes**
   - Affiche les 5 dernières transactions
   - Icônes selon le type (transfer, deposit, withdrawal)
   - Montants colorés (vert/rouge)

#### 🛣️ Routes Ajoutées
```python
# Ajouter une devise
POST /app/wallets/add-currency
- Paramètre: currency (USD, EUR, etc.)

# Retirer une devise (solde = 0 requis)
POST /app/wallets/remove-currency
- Paramètre: currency

# Récupérer transactions par devise
GET /app/wallets/transactions/<currency>
- Retourne: {transactions: [...]}
```

---

### Pages Admin (`admin_wallets.html`)

#### ✨ Design & UI
- **Header avec Stats**: Bouton "Statistiques" pour vue globale
- **Search & Filter**: Recherche par email + filtres par devise
- **Balance Cards**: Cartes de solde avec drapeaux et hover effects
- **Historique Button**: Bouton dédié pour voir l'historique de chaque wallet

#### 🔧 Fonctionnalités
1. **Filtrage Avancé**
   - Recherche par email en temps réel
   - Filtres par devise (Toutes, USD, EUR, GBP, MAD)
   - Boutons de filtre avec style actif

2. **Historique des Ajustements (Modal)**
   - Liste chronologique des modifications
   - Affiche: ancien solde → nouveau solde
   - Info admin, date/heure, raison
   - Badges colorés (+/- montant)

3. **Statistiques Globales (Modal)**
   - Total portefeuilles
   - Portefeuilles actifs
   - Devises populaires
   - Cartes avec icônes Lucide

#### 🛣️ Routes Ajoutées
```python
# Récupérer historique d'un wallet
GET /admin/wallets/<wallet_id>/history
- Retourne: {history: [
    {
      adjustment_id, wallet_id, currency,
      old_balance, new_balance, difference,
      admin_email, reason, created_at
    }
  ]}
```

---

## 📊 Services Wallet Améliorés

### `wallet_service.py` - Nouvelles Fonctions

```python
# Récupérer transactions d'un utilisateur
get_wallet_transactions(user_id, limit=50)
- Retourne toutes les transactions (envoi + réception)

# Ajouter une devise au portefeuille
add_currency_to_wallet(user_id, currency)
- Ajoute une devise avec solde 0
- Devises supportées: USD, EUR, MAD, GBP, CHF, CAD, AED, SAR

# Retirer une devise (si solde = 0)
remove_currency_from_wallet(user_id, currency)
- Supprime la devise uniquement si balance = 0
```

---

## 🎨 Composants CSS Réutilisables

### Classes Principales
```css
/* Cards */
.wallet-total-card       - Carte solde total avec gradient
.wallet-card             - Carte de devise individuelle
.balance-card            - Carte de solde dans admin

/* Modals */
.wise-modal              - Container modal
.wise-modal-backdrop     - Fond flouté
.wise-modal-content      - Contenu avec glassmorphism
.wise-modal-header       - En-tête avec titre et close
.wise-modal-tabs         - Navigation par tabs
.wise-modal-body         - Corps du modal

/* Buttons */
.wise-btn-add-currency   - Bouton orange "Ajouter Devise"
.action-btn              - Bouton d'action avec icône
.filter-btn              - Bouton de filtre

/* Transactions */
.transaction-item        - Item de transaction
.transaction-icon        - Icône de transaction
.transaction-amount      - Montant (positive/negative)

/* Stats */
.stats-grid              - Grille de statistiques
.stat-card               - Carte de stat individuelle
```

### Animations
```css
@keyframes fadeIn        - Apparition douce
@keyframes slideUp       - Slide vers le haut
@keyframes spin          - Rotation (loader)
```

---

## 🔒 Sécurité & Validation

### Validation des Devises
- Liste whitelist dans `wallet_service.py`
- Vérification avant ajout/retrait
- Protection contre injection

### Contrôle d'Accès
- Routes protégées par `@login_required`
- Routes admin par `@admin_required`
- Session validation

### Validation des Soldes
- Solde négatif interdit
- Retrait uniquement si solde = 0
- Ajustements enregistrés dans `wallet_adjustments`

---

## 📱 Responsive Design

### Breakpoints
```css
Mobile First (< 640px):
- 2 colonnes pour currency grid
- Wallets grid: min 160px

Desktop (≥ 768px):
- Wallets grid: min 200px
- Max width modals: 600-700px
```

### Touch Optimized
- Grandes zones de clic
- Hover states adaptés
- Modals plein écran sur mobile

---

## 🚀 Utilisation

### Pour Utilisateurs
1. Accéder à `/app/wallets`
2. Cliquer "Ajouter Devise" pour ajouter une devise
3. Cliquer sur une carte de devise pour voir détails
4. Tabs: Historique / Stats / Actions
5. Retirer une devise depuis Actions (si solde = 0)

### Pour Admins
1. Accéder à `/admin/wallets`
2. Rechercher par email ou filtrer par devise
3. Ajuster solde avec formulaire en bas de chaque carte
4. Voir historique avec bouton horloge
5. Stats globales avec bouton en haut

---

## 🛠️ Technologies Utilisées

- **Frontend**: Jinja2, Vanilla JS, CSS3
- **Icons**: Lucide Icons
- **Backend**: Flask, MongoDB
- **Animations**: CSS Transitions & Keyframes
- **Design**: Glassmorphism, Gradients

---

## 📝 TODO / Améliorations Futures

- [ ] Graphiques de progression des soldes
- [ ] Export CSV de l'historique
- [ ] Notifications push pour ajustements
- [ ] Multi-devises dans une seule transaction
- [ ] Taux de change en temps réel dans les stats
- [ ] Dark/Light mode toggle
- [ ] Pagination pour historique long
- [ ] Filtres avancés (dates, montants)

---

## 🐛 Debugging

### Console JavaScript
```javascript
// Vérifier si modal s'ouvre
document.getElementById('walletDetailsModal').classList.contains('active')

// Forcer fermeture
closeWalletDetails()
closeAddCurrencyModal()
closeHistoryModal()

// Recharger icônes Lucide
lucide.createIcons()
```

### Backend
```python
# Vérifier wallet
from app.services.wallet_service import get_wallet
wallet = get_wallet(user_id)
print(wallet['balances'])

# Vérifier historique
from app.services.wallet_service import get_wallet_history
history = get_wallet_history(wallet_id)
print(len(history))
```

---

**Version**: 1.0.0
**Date**: 31 Janvier 2026
**Auteur**: SarfX Development Team
