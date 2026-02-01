# 🏦 Module ATM & Banques Partenaires - SarfX Fintech

## 📋 Vue d'ensemble

Module complet pour la gestion des distributeurs automatiques (ATM) des banques partenaires au Maroc, avec géolocalisation, calcul de distance et intégration au convertisseur de devises.

## 🎯 Fonctionnalités

### 1. **Service ATM** (`app/services/atm_service.py`)
- ✅ Gestion complète des ATM (CRUD)
- ✅ Calcul de distance avec formule Haversine
- ✅ Recherche géospatiale avec MongoDB (index 2dsphere)
- ✅ Filtrage par banque, ville, proximité
- ✅ Estimation du temps de trajet (marche/voiture)

### 2. **Logos des Banques** (`app/static/images/banks/`)
Logos SVG optimisés pour:
- 🏦 **Attijariwafa Bank** - Rouge (#E30613)
- 🏦 **Bank of Africa (BOA)** - Vert (#00843D)
- 🏦 **Banque Populaire** - Bleu (#005BAA)
- 🏦 **CIH Bank** - Rouge foncé (#C41E3A)
- 🏦 **Al Barid Bank** - Jaune/Bleu (#FFD700/#0066CC)
- 🏦 **BMCI** - Rouge (#DC0032)

### 3. **API REST** (`app/routes/api_routes.py`)

#### Endpoints disponibles:

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/banks` | Liste toutes les banques + nombre d'ATM |
| GET | `/api/banks/<code>` | Détails d'une banque |
| GET | `/api/atms` | Liste ATM (filtres: bank_code, city, limit) |
| POST | `/api/atms/nearest` | ATM les plus proches (géolocalisation) |
| GET | `/api/atms/search?q=<term>` | Recherche textuelle |
| GET | `/api/atms/<atm_id>` | Détails d'un ATM |
| GET | `/api/cities` | Villes avec ATM |

### 4. **Interface Utilisateur**

#### Page d'accueil (`app/templates/app_home.html`)
- ✅ Section "Nos Banques Partenaires" avec carousel
- ✅ Logos animés avec hover effects
- ✅ Auto-scroll toutes les 3 secondes
- ✅ Compteur total d'ATM

#### Convertisseur (`app/templates/app_converter.html`)
- ✅ Étape de sélection de banque (grid 2 colonnes)
- ✅ Liste des ATM de la banque sélectionnée
- ✅ Bouton géolocalisation
- ✅ Tri par distance si position activée
- ✅ Affichage détaillé: adresse, horaires, services, accessibilité
- ✅ Clic sur ATM → Google Maps

## 🗄️ Base de Données

### Collection `atm_locations`

Structure d'un document ATM:

```json
{
  "atm_id": "ATM_attijariwafa_20260122153045",
  "bank_code": "attijariwafa",
  "name": "ATM Attijariwafa Twin Center",
  "address": "Boulevard Zerktouni, Twin Center",
  "city": "Casablanca",
  "district": "Maarif",
  "location": {
    "type": "Point",
    "coordinates": [-7.626690, 33.591370]
  },
  "services": ["withdrawal", "deposit", "balance", "transfer"],
  "available_24h": true,
  "hours": null,
  "has_wheelchair_access": true,
  "status": "active",
  "created_at": "2026-01-22T15:30:45.123Z"
}
```

### Index MongoDB

- **Géospatial (2dsphere)** sur `location` pour recherche proximité
- **Ascendant** sur `bank_code` pour filtrage
- **Ascendant** sur `city` pour filtrage

## 🚀 Initialisation

### Seed des données ATM

```bash
python seed_atm_data.py
```

**Résultat:**
- 25 ATM insérés
- Répartis dans 6 villes (Casablanca, Rabat, Marrakech, Tanger, Fès, Agadir)
- 6 banques représentées

## 📊 Statistiques

### ATM par banque (après seed)
- Attijariwafa Bank: **10 ATM**
- Bank of Africa: **5 ATM**
- Banque Populaire: **4 ATM**
- CIH Bank: **4 ATM**
- Al Barid Bank: **1 ATM**
- BMCI: **1 ATM**

### ATM par ville
- Casablanca: **11 ATM**
- Marrakech: **4 ATM**
- Rabat: **4 ATM**
- Tanger: **2 ATM**
- Fès: **2 ATM**
- Agadir: **2 ATM**

## 🧮 Calcul de Distance

Formule Haversine pour précision géodésique:

```python
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Rayon Terre en km
    Δlat = radians(lat2 - lat1)
    Δlon = radians(lon2 - lon1)
    
    a = sin²(Δlat/2) + cos(lat1) * cos(lat2) * sin²(Δlon/2)
    c = 2 * atan2(√a, √(1-a))
    distance = R * c
    
    return distance  # en km
```

## 🌍 Géolocalisation

### Activation

1. L'utilisateur clique sur **"Ma Position"**
2. Navigateur demande permission
3. API Geolocation retourne coordonnées GPS
4. ATM rechargés et triés par distance
5. Affichage distance + temps estimé

### Temps estimés
- **Marche**: ~3 km/h → `distance * 20 min/km`
- **Voiture**: ~30 km/h en ville → `distance * 2 min/km`

## 🎨 Styles CSS

### Classes ajoutées dans `app.css`

```css
.bank-card             /* Carte de sélection banque */
.bank-card:hover       /* Effet hover avec scale */
.bank-card.selected    /* État sélectionné (border bleue) */
.atm-card              /* Carte ATM avec hover slide */
.location-active       /* Animation pulse pour bouton localisation */
```

### Partner Cards (home)

```css
.partner-card          /* Logo banque dans carousel */
.partner-card:hover    /* Transform + shadow */
```

## 🔧 Configuration

### Variables d'environnement

```bash
MONGO_URI=mongodb://localhost:27017/
DB_NAME=sarfx_db
```

### Dépendances Python

Déjà présentes dans `requirements.txt`:
- `pymongo` - MongoDB driver
- `certifi` - SSL certificates
- `flask` - Framework web

## 📱 Responsive & Compatibilité

### Mobile (< 768px)
- ✅ Grid 2 colonnes pour banques
- ✅ Carousel partenaires avec 2 cartes visibles
- ✅ Navigation bottom bar
- ✅ Touch-friendly (tap zones > 44px)

### Tablet (768px - 1024px)
- ✅ Grid 3 colonnes pour banques
- ✅ Carousel avec 3 cartes
- ✅ Layout étendu

### Desktop (> 1024px)
- ✅ Grid 4 colonnes
- ✅ Sidebar navigation (à venir)
- ✅ Multi-colonnes dashboard

## 🔐 Sécurité

- ✅ Géolocalisation avec permission utilisateur
- ✅ Validation des coordonnées GPS
- ✅ Index MongoDB optimisés
- ✅ Timeout de requêtes (5s)
- ✅ Soft delete (status: "inactive")

## 🚧 Prochaines Étapes

1. **Intégration Google Maps API**
   - Carte interactive avec marqueurs
   - Itinéraires en temps réel
   
2. **Notifications Push**
   - Alerte quand proche d'un ATM
   
3. **Favoris ATM**
   - Enregistrer ATM préférés
   
4. **Horaires dynamiques**
   - Afficher si ATM ouvert maintenant
   
5. **État des ATM**
   - Disponibilité en temps réel
   - Signalement de pannes

## 📞 Support

Pour toute question ou bug:
- 📧 Email: support@sarfx.ma
- 📱 Tél: +212 XXX XXX XXX

---

**Version:** 1.0.0  
**Date:** 22 janvier 2026  
**Auteur:** SarfX Fintech Team
