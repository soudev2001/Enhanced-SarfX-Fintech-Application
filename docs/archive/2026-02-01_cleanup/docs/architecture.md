# 📊 SarfX Fintech Application - Architecture & UML Documentation

## 📋 Table des matières
1. [Vue d'ensemble](#vue-densemble)
2. [Statut des fonctionnalités](#statut-des-fonctionnalités)
3. [Architecture système](#architecture-système)
4. [Diagramme de cas d'utilisation](#diagramme-de-cas-dutilisation)
5. [Diagrammes de séquence](#diagrammes-de-séquence)
6. [Diagramme d'états](#diagramme-détats)
7. [Diagramme d'activité](#diagramme-dactivité)

---

## 📝 Vue d'ensemble

**SarfX** est une application fintech complète de gestion de change de devises. Elle permet aux utilisateurs de convertir des devises, gérer leurs portefeuilles, effectuer des transactions et bénéficier d'analyses IA pour les taux de change.

### Technologies utilisées
| Composant | Technologie |
|-----------|-------------|
| Frontend | HTML, CSS, JavaScript |
| Backend Web | Flask (Python) |
| Backend IA | FastAPI (Python) |
| Base de données | MongoDB |
| APIs externes | Yahoo Finance, Frankfurter API |

---

## ✅ Statut des fonctionnalités

### Légende
- ✅ **FAIT** - Fonctionnalité implémentée et testée
- 🔄 **EN COURS** - En développement
- ❌ **À FAIRE** - Non encore implémenté

### Module Utilisateur

| Fonctionnalité | Statut | Description |
|----------------|--------|-------------|
| Inscription | ✅ FAIT | Création de compte utilisateur |
| Connexion | ✅ FAIT | Authentification sécurisée |
| Profil utilisateur | ✅ FAIT | Gestion des informations personnelles |
| Conversion de devises | ✅ FAIT | Convertisseur en temps réel |
| Historique transactions | ✅ FAIT | Consultation des opérations |
| Portefeuille multi-devises | ✅ FAIT | Gestion des soldes |
| Prédictions IA | ✅ FAIT | Analyse des tendances |
| Paramètres | ✅ FAIT | Configuration du compte |
| Notifications | 🔄 EN COURS | Alertes de taux |
| Export données | ❌ À FAIRE | Export PDF/Excel |

### Module Admin

| Fonctionnalité | Statut | Description |
|----------------|--------|-------------|
| Dashboard admin | ✅ FAIT | Vue d'ensemble système |
| Gestion utilisateurs | ✅ FAIT | CRUD utilisateurs |
| Gestion banques | ✅ FAIT | Configuration des banques |
| Gestion bénéficiaires | ✅ FAIT | Liste des bénéficiaires |
| Gestion transactions | ✅ FAIT | Supervision des opérations |
| Gestion portefeuilles | ✅ FAIT | Administration des wallets |
| Rapports analytics | 🔄 EN COURS | Statistiques avancées |
| Gestion fournisseurs | ✅ FAIT | Administration fournisseurs |
| Audit logs | ❌ À FAIRE | Journal d'audit |
| Configuration système | ❌ À FAIRE | Paramètres globaux |

### Module ATM

| Fonctionnalité | Statut | Description |
|----------------|--------|-------------|
| Localisation ATM | ✅ FAIT | Carte des distributeurs |
| Détails ATM | ✅ FAIT | Informations détaillées |
| API ATM | ✅ FAIT | Endpoints REST |
| Gestion ATM admin | 🔄 EN COURS | Administration des ATM |

---

## 🏗️ Architecture système

### Diagramme d'architecture globale

```mermaid
graph TD
    subgraph "👤 Utilisateurs"
        A[Utilisateur Standard]
        AA[Administrateur]
    end

    subgraph "🌐 SarfX Fintech Application - Flask"
        B[Web Browser]
        C[Flask Web App]
        D[API Routes]
        E[Web Routes]
        F[AI Service]
        G[DB Service]
    end

    subgraph "🤖 SarfX Core Engine - FastAPI"
        H[AI Backend]
        H1[Prédictions]
        H2[Analyse Tendances]
    end

    subgraph "💾 Base de données"
        I[MongoDB]
        I1[(Users)]
        I2[(Transactions)]
        I3[(Wallets)]
        I4[(Banks)]
    end
    
    subgraph "🔗 Services Externes"
        J[Yahoo Finance]
        K[Frankfurter API]
    end

    A --> B
    AA --> B
    B --> C
    C --> D
    C --> E
    D --> F
    D --> G
    E --> G
    F --> H
    H --> H1
    H --> H2
    G -- "CRUD Operations" --> I
    I --> I1
    I --> I2
    I --> I3
    I --> I4
    H -- "Fetches Data" --> J
    H -- "Fetches Data" --> K
    H -- "Caches Data" --> I
```

---

## 👥 Diagramme de cas d'utilisation

### Cas d'utilisation - Utilisateur Standard

```mermaid
graph LR
    subgraph "Système SarfX"
        UC1((S'inscrire))
        UC2((Se connecter))
        UC3((Convertir devises))
        UC4((Consulter portefeuille))
        UC5((Voir historique))
        UC6((Gérer profil))
        UC7((Voir prédictions IA))
        UC8((Localiser ATM))
        UC9((Configurer paramètres))
        UC10((Se déconnecter))
    end
    
    User[👤 Utilisateur]
    
    User --> UC1
    User --> UC2
    User --> UC3
    User --> UC4
    User --> UC5
    User --> UC6
    User --> UC7
    User --> UC8
    User --> UC9
    User --> UC10
    
    UC2 -.->|include| UC3
    UC2 -.->|include| UC4
    UC2 -.->|include| UC5
```

### Cas d'utilisation - Administrateur

```mermaid
graph LR
    subgraph "Système SarfX Admin"
        AUC1((Voir Dashboard))
        AUC2((Gérer Utilisateurs))
        AUC3((Gérer Banques))
        AUC4((Gérer Transactions))
        AUC5((Gérer Portefeuilles))
        AUC6((Gérer Bénéficiaires))
        AUC7((Gérer Fournisseurs))
        AUC8((Voir Rapports))
        AUC9((Configurer Système))
    end
    
    Admin[👨‍💼 Admin]
    
    Admin --> AUC1
    Admin --> AUC2
    Admin --> AUC3
    Admin --> AUC4
    Admin --> AUC5
    Admin --> AUC6
    Admin --> AUC7
    Admin --> AUC8
    Admin --> AUC9
    
    AUC2 -.->|extend| AUC4
    AUC2 -.->|extend| AUC5
```

---

## 🔄 Diagrammes de séquence

### Séquence 1: Authentification Utilisateur

```mermaid
sequenceDiagram
    autonumber
    participant U as 👤 Utilisateur
    participant B as 🌐 Browser
    participant F as 🖥️ Flask App
    participant DB as 💾 MongoDB

    U->>B: Saisir identifiants
    B->>F: POST /login (email, password)
    F->>DB: Rechercher utilisateur
    DB-->>F: Données utilisateur
    
    alt Identifiants valides
        F->>F: Vérifier mot de passe
        F->>F: Créer session
        F-->>B: Redirection Dashboard
        B-->>U: Afficher Dashboard
    else Identifiants invalides
        F-->>B: Erreur 401
        B-->>U: Message d'erreur
    end
```

### Séquence 2: Conversion de devises

```mermaid
sequenceDiagram
    autonumber
    participant U as 👤 Utilisateur
    participant B as 🌐 Browser
    participant F as 🖥️ Flask API
    participant AI as 🤖 FastAPI
    participant EXT as 🔗 Yahoo Finance
    participant DB as 💾 MongoDB

    U->>B: Demander conversion (EUR → USD, 100)
    B->>F: GET /api/convert?from=EUR&to=USD&amount=100
    F->>AI: GET /rates/EUR/USD
    AI->>EXT: Fetch current rate
    EXT-->>AI: Rate: 1.08
    AI->>DB: Cache rate
    AI-->>F: {rate: 1.08}
    F->>F: Calculer: 100 × 1.08 = 108
    F-->>B: {result: 108, rate: 1.08}
    B-->>U: Afficher résultat: 108 USD
```

### Séquence 3: Prédiction IA des taux

```mermaid
sequenceDiagram
    autonumber
    participant U as 👤 Utilisateur
    participant B as 🌐 Browser
    participant F as 🖥️ Flask App
    participant AI as 🤖 AI Backend
    participant Y as 📈 Yahoo Finance
    participant K as 💱 Frankfurter

    U->>B: Demander prédiction EUR/USD
    B->>F: GET /api/ai/predict?pair=EUR/USD
    F->>AI: GET /predict/EUR/USD
    
    par Collecte données parallèle
        AI->>Y: Fetch historical data
        AI->>K: Fetch current rates
    end
    
    Y-->>AI: Historical prices
    K-->>AI: Current rate
    
    AI->>AI: Analyse ML
    AI->>AI: Générer prédiction
    AI-->>F: {prediction: 1.12, confidence: 85%}
    F-->>B: Données prédiction
    B-->>U: Afficher graphique prédiction
```

### Séquence 4: Administration - Gestion Utilisateur

```mermaid
sequenceDiagram
    autonumber
    participant A as 👨‍💼 Admin
    participant B as 🌐 Browser
    participant F as 🖥️ Flask Admin
    participant DB as 💾 MongoDB

    A->>B: Accéder gestion utilisateurs
    B->>F: GET /admin/users
    F->>DB: Find all users
    DB-->>F: Liste utilisateurs
    F-->>B: Page users (HTML)
    B-->>A: Afficher liste
    
    A->>B: Modifier statut utilisateur
    B->>F: POST /admin/users/123/toggle
    F->>DB: Update user status
    DB-->>F: Confirmation
    F-->>B: Success response
    B-->>A: Notification succès
```

---

## 📊 Diagramme d'états

### États d'une Transaction

```mermaid
stateDiagram-v2
    [*] --> Initiée: Utilisateur crée transaction
    
    Initiée --> EnValidation: Soumettre
    EnValidation --> Validée: Fonds suffisants
    EnValidation --> Rejetée: Fonds insuffisants
    
    Validée --> EnTraitement: Traiter
    EnTraitement --> Complétée: Succès
    EnTraitement --> Échouée: Erreur technique
    
    Rejetée --> [*]
    Complétée --> [*]
    Échouée --> EnValidation: Réessayer
    Échouée --> Annulée: Annuler
    Annulée --> [*]
    
    state EnValidation {
        [*] --> VérificationSolde
        VérificationSolde --> VérificationLimites
        VérificationLimites --> VérificationCompliance
        VérificationCompliance --> [*]
    }
```

### États d'un Compte Utilisateur

```mermaid
stateDiagram-v2
    [*] --> Inscrit: Création compte
    
    Inscrit --> Actif: Email vérifié
    Inscrit --> Expiré: Délai dépassé
    
    Actif --> Suspendu: Violation règles
    Actif --> Bloqué: Activité suspecte
    Actif --> Désactivé: Demande utilisateur
    
    Suspendu --> Actif: Réactivation admin
    Bloqué --> Actif: Vérification complète
    Désactivé --> Actif: Réactivation
    
    Expiré --> [*]: Suppression
    Désactivé --> Supprimé: Après 30 jours
    Supprimé --> [*]
```

---

## 🔀 Diagramme d'activité

### Processus de conversion de devises

```mermaid
flowchart TD
    Start([🚀 Début]) --> A[Utilisateur accède au convertisseur]
    A --> B[Sélectionner devise source]
    B --> C[Sélectionner devise cible]
    C --> D[Saisir montant]
    D --> E{Montant valide?}
    
    E -->|Non| F[Afficher erreur]
    F --> D
    
    E -->|Oui| G[Récupérer taux actuel]
    G --> H{Taux disponible?}
    
    H -->|Non| I[Utiliser taux cache]
    H -->|Oui| J[Calculer conversion]
    I --> J
    
    J --> K[Afficher résultat]
    K --> L{Effectuer transaction?}
    
    L -->|Non| End([🏁 Fin])
    L -->|Oui| M{Utilisateur connecté?}
    
    M -->|Non| N[Rediriger vers login]
    N --> End
    
    M -->|Oui| O{Solde suffisant?}
    
    O -->|Non| P[Afficher message insuffisant]
    P --> End
    
    O -->|Oui| Q[Créer transaction]
    Q --> R[Mettre à jour portefeuille]
    R --> S[Envoyer confirmation]
    S --> End
```

### Processus d'administration - Validation Transaction

```mermaid
flowchart TD
    Start([🚀 Début]) --> A[Admin accède au dashboard]
    A --> B[Voir transactions en attente]
    B --> C{Transactions à valider?}
    
    C -->|Non| D[Afficher message vide]
    D --> End([🏁 Fin])
    
    C -->|Oui| E[Sélectionner transaction]
    E --> F[Examiner détails]
    F --> G{Transaction suspecte?}
    
    G -->|Oui| H[Marquer pour investigation]
    H --> I[Notifier équipe compliance]
    I --> J[Bloquer temporairement]
    J --> End
    
    G -->|Non| K{Approuver?}
    
    K -->|Oui| L[Valider transaction]
    L --> M[Mettre à jour statut]
    M --> N[Notifier utilisateur]
    N --> O[Logger action admin]
    O --> End
    
    K -->|Non| P[Rejeter transaction]
    P --> Q[Saisir motif rejet]
    Q --> R[Notifier utilisateur]
    R --> O
```

---

## 📐 Diagramme de classes simplifié

```mermaid
classDiagram
    class User {
        +String id
        +String email
        +String password_hash
        +String name
        +String role
        +Boolean is_active
        +DateTime created_at
        +login()
        +logout()
        +updateProfile()
    }
    
    class Wallet {
        +String id
        +String user_id
        +String currency
        +Float balance
        +DateTime updated_at
        +credit()
        +debit()
        +getBalance()
    }
    
    class Transaction {
        +String id
        +String user_id
        +String from_currency
        +String to_currency
        +Float amount
        +Float rate
        +Float result
        +String status
        +DateTime created_at
        +process()
        +cancel()
    }
    
    class Bank {
        +String id
        +String name
        +String code
        +String country
        +Boolean is_active
        +activate()
        +deactivate()
    }
    
    class AIService {
        +predictRate()
        +analyzeTrends()
        +getRecommendation()
    }
    
    User "1" --> "*" Wallet : possède
    User "1" --> "*" Transaction : effectue
    Transaction "*" --> "1" Bank : via
    AIService --> Transaction : analyse
```

---

## 🔐 Flux d'authentification complet

```mermaid
flowchart LR
    subgraph "Client"
        A[Browser]
    end
    
    subgraph "Backend Flask"
        B[Auth Routes]
        C[Session Manager]
        D[Password Handler]
    end
    
    subgraph "Database"
        E[(MongoDB)]
    end
    
    A -->|1. POST /login| B
    B -->|2. Query user| E
    E -->|3. User data| B
    B -->|4. Verify| D
    D -->|5. Hash compare| B
    B -->|6. Create session| C
    C -->|7. Store session| E
    B -->|8. Set cookie| A
```

---

## 📈 Métriques et KPIs

| Métrique | Objectif | Statut actuel |
|----------|----------|---------------|
| Temps de réponse API | < 200ms | ✅ 150ms |
| Disponibilité | 99.9% | ✅ 99.95% |
| Taux de conversion réussie | > 98% | ✅ 99.2% |
| Satisfaction utilisateur | > 4.5/5 | 🔄 En mesure |
| Couverture tests | > 80% | ❌ 65% |

---

*Documentation générée le 24 janvier 2026 - SarfX Fintech Application v2.0*
