# 📸 Guide Visuel - Module ATM & Banques Partenaires

## 🏠 Page d'Accueil - Section Partenaires

### Emplacement
Après la section "Features Cards" et avant "Recent Transactions"

### Apparence Attendue
```
┌─────────────────────────────────────────┐
│  🏦 Nos Banques Partenaires             │
├─────────────────────────────────────────┤
│                                         │
│  [Attijariwafa] [Bank of Africa]       │
│                                         │
│         ← [•••] →                       │
│                                         │
│  Plus de 250 distributeurs répartis    │
│  dans tout le Maroc                     │
└─────────────────────────────────────────┘
```

### Détails
- **Fond**: Glass panel avec backdrop blur
- **Titre**: Icône landmark + "Nos Banques Partenaires"
- **Logos**: 6 cartes SVG colorées (2 visibles sur mobile)
- **Navigation**: Flèches gauche/droite
- **Animation**: Auto-scroll toutes les 3s
- **Footer**: Texte avec compteur d'ATM en bleu

---

## 💱 Convertisseur - Sélection Banque

### Emplacement
Après la section "Bénéficiaire"

### Apparence Attendue
```
┌─────────────────────────────────────────┐
│  🏦 Banque de Retrait                   │
│  Choisissez votre banque préférée       │
├─────────────────────────────────────────┤
│                                         │
│  ┌──────────┐  ┌──────────┐           │
│  │Attijariwafa│ │Bank of    │          │
│  │    10 ATM   │ │Africa 5ATM│         │
│  └──────────┘  └──────────┘           │
│                                         │
│  ┌──────────┐  ┌──────────┐           │
│  │  Banque   │  │   CIH     │          │
│  │Populaire4│  │Bank 4 ATM │          │
│  └──────────┘  └──────────┘           │
│                                         │
│  ┌──────────┐  ┌──────────┐           │
│  │Al Barid   │  │   BMCI    │          │
│  │Bank 1 ATM │  │   1 ATM   │          │
│  └──────────┘  └──────────┘           │
└─────────────────────────────────────────┘
```

### Détails
- **Fond**: Glass panel
- **Titre**: Icône landmark violet + texte
- **Grid**: 2 colonnes sur mobile, 3 sur tablette
- **Cartes**: Logo centré + compteur ATM
- **Hover**: Scale 1.05 + shadow bleue
- **Sélection**: Border bleue + background bleu/10

---

## 📍 Convertisseur - Distributeurs Proches

### Emplacement
Après la section "Banque de Retrait" (visible uniquement si banque sélectionnée)

### Apparence Attendue (Avant géolocalisation)
```
┌─────────────────────────────────────────┐
│  📍 Distributeurs Proches               │
│  Détectez votre position   [Ma Position]│
├─────────────────────────────────────────┤
│                                         │
│         🧭                              │
│                                         │
│  Sélectionnez une banque et activez    │
│  votre position                         │
│                                         │
└─────────────────────────────────────────┘
```

### Apparence Attendue (Après géolocalisation)
```
┌─────────────────────────────────────────┐
│  📍 Distributeurs Proches               │
│  Distributeurs triés par distance  [✓OK]│
├─────────────────────────────────────────┤
│  ┌───────────────────────────────────┐ │
│  │ ATM Attijariwafa Twin Center      │ │
│  │ 📍 Bd Zerktouni, Casa    🧭 2.26km│ │
│  │ 🕐 24/7  ♿ Accessible             │ │
│  │ ~45 min à pied                    │ │
│  │ [withdrawal][deposit][balance]    │ │
│  └───────────────────────────────────┘ │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │ ATM Attijariwafa Place Nations    │ │
│  │ 📍 Place Nations, Casa   🧭 3.50km│ │
│  │ 🕐 24/7  ♿ Accessible             │ │
│  │ ~70 min à pied                    │ │
│  │ [withdrawal][deposit][balance]    │ │
│  └───────────────────────────────────┘ │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │ ATM BP Casa Port                  │ │
│  │ 📍 Bd Almohades, Casa    🧭 3.82km│ │
│  │ 🕐 24/7                           │ │
│  │ ~76 min à pied                    │ │
│  │ [withdrawal][balance][transfer]   │ │
│  └───────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

### Détails
- **Fond**: Glass panel
- **Header**: 
  - Icône map-pin vert + titre
  - Sous-titre dynamique
  - Bouton géolocalisation à droite
- **Bouton États**:
  - Inactif: Bleu "Ma Position"
  - Loading: "Détection..." avec spinner
  - Actif: Vert "Position OK" avec checkmark
- **Cartes ATM**:
  - Nom en gras
  - Adresse avec icône map-pin
  - Distance (si géoloc) avec icône navigation
  - Temps estimé à pied
  - Horaires avec icône horloge
  - Accessibilité
  - Services en badges
- **Scroll**: Max height 96 (overflow-y auto)
- **Clic**: Ouvre Google Maps

---

## 🎨 Palette de Couleurs

### Banques
- **Attijariwafa Bank**: Rouge #E30613
- **Bank of Africa**: Vert #00843D  
- **Banque Populaire**: Bleu #005BAA
- **CIH Bank**: Rouge foncé #C41E3A
- **Al Barid Bank**: Jaune #FFD700 + Bleu #0066CC
- **BMCI**: Rouge #DC0032

### UI Elements
- **Primary**: Bleu #3B82F6
- **Success**: Vert #10B981
- **Warning**: Orange #F59E0B
- **Error**: Rouge #EF4444
- **Info**: Violet #8B5CF6

### Glass Effects
- **Background**: rgba(255, 255, 255, 0.05)
- **Border**: rgba(255, 255, 255, 0.1)
- **Backdrop blur**: 12px

---

## 📱 Responsive Breakpoints

### Mobile (< 768px)
- Carousel: 2 logos visibles
- Banques grid: 2 colonnes
- ATM cards: Full width
- Navigation: Bottom bar

### Tablet (768px - 1024px)
- Carousel: 3 logos visibles
- Banques grid: 3 colonnes
- ATM cards: Full width
- Navigation: Bottom bar

### Desktop (> 1024px)
- Carousel: 4 logos visibles
- Banques grid: 3 colonnes
- ATM cards: Max width 800px centered
- Navigation: Sidebar (futur)

---

## 🎬 Animations

### Carousel
- **Auto-scroll**: translate-x avec transition 500ms ease-out
- **Interval**: 3000ms
- **Hover**: Pause auto-scroll

### Bank Cards
- **Hover**: 
  - Transform: translateY(-4px) scale(1.02)
  - Shadow: 0 12px 28px rgba(59, 130, 246, 0.15)
  - Duration: 300ms cubic-bezier(0.4, 0, 0.2, 1)
- **Selected**:
  - Border: 2px solid #3B82F6
  - Background: rgba(59, 130, 246, 0.1)

### ATM Cards
- **Hover**:
  - Background: rgba(255, 255, 255, 0.08)
  - Transform: translateX(4px)
  - Left border: 3px gradient vert-bleu
  - Duration: 300ms ease

### Location Button
- **Loading**: Spinner rotate 360° infinite
- **Active**: Pulse animation 2s ease-in-out infinite

---

## 🔄 États de Chargement

### Pendant Chargement Banques
```
┌─────────────────────────────────────────┐
│  🏦 Banque de Retrait                   │
├─────────────────────────────────────────┤
│                                         │
│         ⭕ Chargement...                │
│                                         │
└─────────────────────────────────────────┘
```

### Pendant Chargement ATM
```
┌─────────────────────────────────────────┐
│  📍 Distributeurs Proches               │
├─────────────────────────────────────────┤
│                                         │
│         ⭕ Chargement...                │
│                                         │
└─────────────────────────────────────────┘
```

### Pendant Géolocalisation
```
┌─────────────────────────────────────────┐
│  📍 Distributeurs Proches               │
│  Détectez votre position  [⭕ Détection]│
├─────────────────────────────────────────┤
│  ...                                    │
└─────────────────────────────────────────┘
```

---

## ❌ États d'Erreur

### Erreur Chargement Banques
```
┌─────────────────────────────────────────┐
│  🏦 Banque de Retrait                   │
├─────────────────────────────────────────┤
│                                         │
│  ⚠️ Erreur lors du chargement          │
│                                         │
└─────────────────────────────────────────┘
```

### Erreur Géolocalisation (Permission refusée)
```
Toast notification (bottom center):
┌─────────────────────────────────────────┐
│  ⚠️ Permission de géolocalisation       │
│     refusée                             │
└─────────────────────────────────────────┘
```

### Aucun ATM Trouvé
```
┌─────────────────────────────────────────┐
│  📍 Distributeurs Proches               │
├─────────────────────────────────────────┤
│                                         │
│  Aucun distributeur trouvé             │
│                                         │
└─────────────────────────────────────────┘
```

---

## 🎯 Points de Validation Visuelle

### ✅ Page d'Accueil
- [ ] Section partenaires visible après features cards
- [ ] 6 logos banques correctement affichés
- [ ] Carousel s'anime automatiquement
- [ ] Flèches de navigation fonctionnent
- [ ] Hover sur logo donne scale + shadow
- [ ] Compteur "250+ distributeurs" visible
- [ ] Responsive: 2 logos mobile, 3 tablet, 4 desktop

### ✅ Convertisseur - Banques
- [ ] Section apparaît après montant > 0
- [ ] Grid 2 colonnes sur mobile
- [ ] Logos banques centrés et lisibles
- [ ] Compteur ATM sous chaque logo
- [ ] Hover donne effet scale
- [ ] Sélection donne border bleue
- [ ] Une seule banque sélectionnable à la fois

### ✅ Convertisseur - ATM
- [ ] Section apparaît après sélection banque
- [ ] Bouton "Ma Position" visible et cliquable
- [ ] Permission géolocalisation demandée au clic
- [ ] Loading state pendant détection
- [ ] Liste ATM s'affiche correctement
- [ ] Distance affichée si géoloc active
- [ ] Temps de trajet affiché
- [ ] Horaires et services visibles
- [ ] Clic sur ATM ouvre Google Maps
- [ ] Scroll vertical si > 96 height

### ✅ Mobile (< 768px)
- [ ] Tout est lisible sans zoom
- [ ] Zones de clic > 44x44px
- [ ] Scroll fluide
- [ ] Animations performantes (60fps)
- [ ] Navigation bottom bar accessible

### ✅ Dark/Light Theme
- [ ] Logos lisibles dans les 2 thèmes
- [ ] Glass effect adapté au thème
- [ ] Texte contrasté suffisamment
- [ ] Transitions fluides entre thèmes

---

## 📊 Performance Attendue

### Temps de Chargement
- **Logos banques**: < 100ms (SVG inline)
- **API /api/banks**: < 200ms
- **API /api/atms**: < 500ms
- **Géolocalisation**: 1-3s (dépend navigateur)
- **API /api/atms/nearest**: < 800ms

### Fluidité
- **FPS animations**: 60 fps
- **Scroll**: Smooth 60 fps
- **Hover effects**: Instant (<16ms)

---

## 🐛 Comportements à Éviter

### ❌ Bugs Communs
- [ ] Logos qui ne s'affichent pas → Vérifier chemins SVG
- [ ] ATM sans distance → Vérifier géolocalisation activée
- [ ] Carousel qui saute → Vérifier calcul offset
- [ ] Google Maps ne s'ouvre pas → Vérifier coordonnées valides
- [ ] Section ATM ne s'affiche pas → Vérifier banque sélectionnée

### ❌ Erreurs UX
- [ ] Trop d'ATM affichés (> 20) → Ajouter pagination
- [ ] Pas de feedback pendant chargement → Ajouter spinners
- [ ] Permission géoloc sans explication → Ajouter tooltip
- [ ] ATM non cliquables → Ajouter cursor pointer

---

**🎨 Design System: Glassmorphism + Gradient + Smooth Animations**

Inspiration: iOS Banking Apps + Modern Fintech UIs
