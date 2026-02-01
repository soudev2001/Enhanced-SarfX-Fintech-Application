# 🎬 Guide de Démonstration - Wallets

## 📱 UTILISATEUR - Page Wallets

### 1. Accéder à la page
```
URL: http://localhost:5000/app/wallets
Login: user@demo.com / demo123
```

### 2. Interface Principale
```
┌─────────────────────────────────────────────┐
│  💼 Mes Portefeuilles                       │
│                                      [+ Ajouter Devise] │
├─────────────────────────────────────────────┤
│  ┌─────────────────────────────────────┐   │
│  │ 📈 Solde Total (équivalent USD)    │   │
│  │      $2,534.67                      │   │
│  └─────────────────────────────────────┘   │
├─────────────────────────────────────────────┤
│  Grille des Devises:                        │
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐   │
│  │ 🇺🇸   │  │ 🇪🇺   │  │ 🇬🇧   │  │ 🇲🇦   │   │
│  │ USD  │  │ EUR  │  │ GBP  │  │ MAD  │   │
│  │$1000 │  │€850  │  │£450  │  │1200DH│   │
│  │~$1000│  │~$935 │  │~$562 │  │~$120 │   │
│  └──────┘  └──────┘  └──────┘  └──────┘   │
├─────────────────────────────────────────────┤
│  📜 Transactions Récentes:                  │
│  • Transfer  -$100 USD  • 30 Jan 14:32     │
│  • Deposit   +€200 EUR  • 29 Jan 09:15     │
│  • Convert   -£50 GBP   • 28 Jan 18:45     │
└─────────────────────────────────────────────┘
```

### 3. Cliquer sur une Carte de Devise
```
┌───────────────────────────────────────┐
│  Modal "Détails USD"                  │
│                                  [×]  │
├───────────────────────────────────────┤
│  🇺🇸 USD                              │
│  Balance: $1,000.00                   │
├───────────────────────────────────────┤
│  [Historique] [Statistiques] [Actions]│
├───────────────────────────────────────┤
│  📜 Historique Tab:                   │
│  • Received from John - +$500         │
│  • Sent to Maria - -$200              │
│  • Withdrawal - -$100                 │
│                                       │
│  📊 Statistiques Tab:                 │
│  Total Reçu:    $5,234.00             │
│  Total Envoyé:  $4,234.00             │
│  Transactions:  47                    │
│  Valeur USD:    $1,000.00             │
│                                       │
│  ⚙️ Actions Tab:                      │
│  [📤 Envoyer] [📥 Recevoir]           │
│  [🔄 Convertir] [🗑️ Retirer]          │
└───────────────────────────────────────┘
```

### 4. Ajouter une Devise
```
Cliquer: [+ Ajouter Devise]

┌───────────────────────────────────────┐
│  Ajouter une Devise              [×] │
├───────────────────────────────────────┤
│  Sélectionnez une devise à ajouter   │
│                                       │
│  ┌──────┐  ┌──────┐  ┌──────┐       │
│  │ 🇺🇸   │  │ 🇪🇺   │  │ 🇬🇧   │       │
│  │ USD  │  │ EUR  │  │ GBP  │       │
│  │Dollar│  │Euro  │  │Livre │       │
│  └──────┘  └──────┘  └──────┘       │
│                                       │
│  ┌──────┐  ┌──────┐  ┌──────┐       │
│  │ 🇲🇦   │  │ 🇨🇭   │  │ 🇨🇦   │       │
│  │ MAD  │  │ CHF  │  │ CAD  │       │
│  │Dirham│  │Franc │  │Dollar│       │
│  └──────┘  └──────┘  └──────┘       │
│                                       │
│  [  Ajouter au Portefeuille  ]       │
└───────────────────────────────────────┘
```

---

## 👨‍💼 ADMIN - Page Wallets

### 1. Accéder à la page Admin
```
URL: http://localhost:5000/admin/wallets
Login: admin@sarfx.com / admin123
```

### 2. Interface Principale
```
┌─────────────────────────────────────────────┐
│  ← Retour    💼 Portefeuilles    [📊 Stats] │
│  23 portefeuilles actifs                    │
├─────────────────────────────────────────────┤
│  [🔍 Rechercher par email...]               │
│  [Toutes] [🇺🇸 USD] [🇪🇺 EUR] [🇬🇧 GBP] [🇲🇦 MAD] │
├─────────────────────────────────────────────┤
│  ┌──────────────────────────────────────┐  │
│  │ (U) user@demo.com          [🕐] [✓]  │  │
│  │     abc123def456...                   │  │
│  │                                       │  │
│  │ ┌────────┐ ┌────────┐ ┌────────┐    │  │
│  │ │🇺🇸 USD │ │🇪🇺 EUR │ │🇲🇦 MAD │    │  │
│  │ │ 1,000  │ │  850   │ │ 1,200  │    │  │
│  │ └────────┘ └────────┘ └────────┘    │  │
│  │                                       │  │
│  │ Ajuster le solde:                    │  │
│  │ [Devise ▼] [+/- Montant]             │  │
│  │ [Raison de l'ajustement...]          │  │
│  │ [+ Ajuster le solde]                 │  │
│  └──────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
```

### 3. Cliquer sur l'Historique [🕐]
```
┌───────────────────────────────────────┐
│  Historique des Ajustements      [×] │
│  user@demo.com                        │
├───────────────────────────────────────┤
│  USD: 900.00 → 1,000.00               │
│  admin@sarfx.com • 30 Jan 15:23       │
│  "Bonus mensuel"                [+100]│
├───────────────────────────────────────┤
│  EUR: 1,000.00 → 850.00               │
│  admin@sarfx.com • 29 Jan 10:45       │
│  "Correction d'erreur"         [-150]│
├───────────────────────────────────────┤
│  MAD: 0.00 → 1,200.00                 │
│  system • 28 Jan 09:00           [+1200]│
│  "Initialisation"                     │
└───────────────────────────────────────┘
```

### 4. Statistiques Globales [📊 Stats]
```
┌───────────────────────────────────────┐
│  Statistiques Globales           [×] │
├───────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  │
│  │ 💼 Total     │  │ ✓ Actifs     │  │
│  │    23        │  │    22        │  │
│  └──────────────┘  └──────────────┘  │
│                                       │
│  ┌─────────────────────────────────┐ │
│  │ 🪙 Devises Populaires           │ │
│  │ [🇺🇸 USD] [🇪🇺 EUR] [🇲🇦 MAD] [🇬🇧 GBP] │ │
│  └─────────────────────────────────┘ │
└───────────────────────────────────────┘
```

---

## 🎯 Scénarios de Test

### Scénario 1: Utilisateur Ajoute une Devise
```
1. Login → /app/wallets
2. Cliquer "Ajouter Devise"
3. Sélectionner "CHF"
4. Submit
5. ✅ Voir CHF avec solde 0.00 dans la grille
```

### Scénario 2: Admin Ajuste un Solde
```
1. Login admin → /admin/wallets
2. Chercher "user@demo.com"
3. Sélectionner "USD"
4. Entrer "+500" et "Bonus"
5. Submit
6. ✅ Voir solde USD +500
7. Cliquer [🕐] → Voir historique avec "+500 Bonus"
```

### Scénario 3: Utilisateur Retire une Devise
```
1. Login → /app/wallets
2. Cliquer sur carte avec solde = 0 (ex: CHF)
3. Tab "Actions" → Cliquer "Retirer"
4. Confirmer
5. ✅ CHF disparaît de la grille
```

### Scénario 4: Filtrage Admin
```
1. Login admin → /admin/wallets
2. Taper "demo" dans recherche
3. ✅ Voir seulement wallets avec "demo" dans email
4. Cliquer filtre "🇺🇸 USD"
5. ✅ Voir seulement wallets avec USD
```

---

## 🎨 Éléments à Vérifier

### Design
- ✅ Glassmorphism appliqué (fond flouté)
- ✅ Gradient orange sur Total Balance Card
- ✅ Hover effects sur cartes (translateY, border glow)
- ✅ Animations smooth (fadeIn, slideUp)
- ✅ Icons Lucide chargés correctement

### Responsive
- ✅ Mobile: 1 colonne pour wallets
- ✅ Tablet: 2-3 colonnes
- ✅ Desktop: 4+ colonnes
- ✅ Modals plein écran sur mobile
- ✅ Navigation sticky en bas

### Fonctionnalité
- ✅ Recherche temps réel fonctionne
- ✅ Filtres exclusifs (1 seul actif)
- ✅ Modals s'ouvrent/ferment (ESC key)
- ✅ Tabs switchent correctement
- ✅ Forms soumettent et redirectent
- ✅ Flash messages s'affichent

---

## 🐛 Debugging Console

### JavaScript Console Commands
```javascript
// Ouvrir modal wallet
showWalletDetails('USD', 1000, 1000)

// Fermer tous modals
closeWalletDetails()
closeAddCurrencyModal()
closeHistoryModal()

// Recharger icons
lucide.createIcons()

// Vérifier si modal est active
document.getElementById('walletDetailsModal').classList.contains('active')

// Forcer un filtre
filterByCurrency('EUR')

// Voir tous les wallets
document.querySelectorAll('.wallet-card')
```

### Python Backend Commands
```python
# Dans Python shell
from app.services.wallet_service import *

# Get wallet
wallet = get_wallet('user_id_123')
print(wallet['balances'])

# Add currency
add_currency_to_wallet('user_id_123', 'CHF')

# Get history
history = get_wallet_history('wallet_id_abc')
print(len(history), 'ajustements')
```

---

## 📊 Métriques de Performance

### Temps de Chargement
- Page load: < 1s
- Modal open: < 200ms
- Filter apply: < 100ms
- API call: < 500ms

### Taille des Fichiers
- app_wallets.html: ~15KB
- admin_wallets.html: ~18KB
- wallets.css: ~12KB
- Total JS inline: ~5KB

---

## ✅ Checklist Final

### Utilisateur
- [ ] Page charge sans erreur
- [ ] Total balance s'affiche
- [ ] Grille de devises responsive
- [ ] Modal détails s'ouvre
- [ ] Tabs fonctionnent
- [ ] Ajouter devise fonctionne
- [ ] Retirer devise fonctionne
- [ ] Transactions récentes affichées

### Admin
- [ ] Liste wallets charge
- [ ] Recherche fonctionne
- [ ] Filtres fonctionnent
- [ ] Ajuster solde fonctionne
- [ ] Historique s'affiche
- [ ] Stats modal fonctionne
- [ ] Navigation admin fonctionne

### Design
- [ ] Glassmorphism visible
- [ ] Animations smooth
- [ ] Hover effects
- [ ] Icons chargés
- [ ] Mobile responsive
- [ ] Dark theme appliqué

---

**🎉 Guide de démo complet!**
Suivez ces étapes pour une présentation réussie des nouvelles fonctionnalités Wallets.
