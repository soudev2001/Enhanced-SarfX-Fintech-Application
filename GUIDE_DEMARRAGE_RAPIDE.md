# 🎬 GUIDE RAPIDE - DÉMO VIDÉO COMPLÈTE

## ✅ CE QUI A ÉTÉ IMPLÉMENTÉ

### 1. Variables Corrigées ✅
- Ajout de toutes les variables manquantes dans `variables.robot`
- `LOGOUT_LINK`, `USER_WALLETS_LINK`, `ADMIN_USERS_LINK`, etc.

### 2. Générateur de Sous-titres ✅
- **Fichier**: `SubtitlesGenerator.py`
- Génère des fichiers `.srt` synchronisés avec la vidéo
- Format standard compatible tous lecteurs

### 3. Test Vidéo Complet ✅
- **Fichier**: `test_video_demo_complete.robot`
- **18 tests** couvrant:
  - ✅ Administrateur (6 tests)
  - ✅ Utilisateur standard (7 tests)
  - ✅ Responsable banque (3 tests)
  - ✅ Récapitulatif final (1 test)

### 4. Fusion Vidéo + Sous-titres ✅
- Script automatique: `merge_video.py`
- Script Windows: `merge_video_subtitles.bat`

---

## 🚀 DÉMARRAGE EN 5 ÉTAPES

### Étape 1️⃣: Redémarrer le Terminal

**IMPORTANT** : FFmpeg a été installé mais nécessite un redémarrage

```powershell
# Fermer PowerShell
exit

# Rouvrir PowerShell et vérifier
ffmpeg -version
```

Vous devriez voir: `ffmpeg version 8.0.1 ...`

### Étape 2️⃣: Démarrer l'Application

```powershell
# Terminal 1: Lancer SarfX
.\start_windows.bat
```

Attendez que le serveur démarre sur `http://localhost:5000`

### Étape 3️⃣: Lancer la Démo Complète

```powershell
# Terminal 2: Lancer la démo vidéo
.\run_video_demo_windows.bat
```

Le navigateur Chrome va s'ouvrir en mode visible et la démo va commencer automatiquement.

### Étape 4️⃣: Attendre la Fin

La démo dure environ **5-7 minutes** :
- 📹 Vidéo enregistrée en continu
- 📸 26+ screenshots HD
- 📝 ~50+ sous-titres synchronisés

### Étape 5️⃣: Fusionner Vidéo + Sous-titres

```powershell
# Fusion automatique (dernière vidéo)
python merge_video.py

# OU manuel
python merge_video.py robot_results\video_demo\videos\demo_20260129_0700.mp4
```

---

## 📦 RÉSULTATS

### Structure des Fichiers
```
robot_results/video_demo/
├── videos/
│   ├── demo_20260129_0700.mp4          # Vidéo brute
│   ├── demo_20260129_0700.srt          # Sous-titres
│   └── demo_20260129_0700_with_subtitles.mp4  # Vidéo finale ✨
├── screenshots/
│   ├── 01_landing_page_*.png
│   ├── 02_login_page_*.png
│   ├── 03_admin_email_*.png
│   ├── ...
│   └── 26_final_recap_*.png
├── video-demo-log-*.html
└── video-demo-report-*.html
```

### Contenu de la Démo

#### 👤 Administrateur (Tests 1-7)
1. Page d'accueil
2. Connexion admin
3. Gestion utilisateurs
4. Gestion wallets
5. Transactions admin
6. Gestion banques
7. Déconnexion

#### 👥 Utilisateur (Tests 8-14)
8. Connexion utilisateur
9. Convertisseur USD→MAD
10. Mes portefeuilles
11. Mes transactions
12. Carte des ATMs
13. Mon profil
14. Déconnexion

#### 🏦 Banque (Tests 15-17)
15. Connexion banque
16. Dashboard bancaire
17. Déconnexion

#### 🎬 Récapitulatif (Test 18)
18. Vue finale et crédits

---

## 🎥 CARACTÉRISTIQUES VIDÉO

### Vidéo Brute
- **Format**: MP4 (H.264)
- **Résolution**: 1920x1080
- **Frame rate**: 30 fps
- **Durée**: 5-7 minutes
- **Taille**: ~100-150 MB

### Sous-titres
- **Format**: SRT (standard)
- **Encodage**: UTF-8
- **Nombre**: ~50+ entrées
- **Langues**: Français + Emojis
- **Style**: Police Arial 24px, fond semi-transparent

### Vidéo Finale (avec sous-titres)
- **Format**: MP4 (H.264)
- **Sous-titres**: Incrustés (hardcoded)
- **Compatible**: Tous lecteurs (VLC, Windows Media, etc.)
- **Taille**: ~110-170 MB

---

## 🛠️ DÉPANNAGE

### ❌ FFmpeg non trouvé après installation

```powershell
# Solution 1: Redémarrer le terminal
exit
# Rouvrir PowerShell

# Solution 2: Vérifier le PATH
$env:Path -split ';' | Select-String ffmpeg

# Solution 3: Réinstaller
.\install_ffmpeg_windows.bat
```

### ❌ Variables non trouvées

✅ **RÉSOLU** : Toutes les variables ont été ajoutées dans `variables.robot`

Si le problème persiste:
```powershell
# Vérifier les variables
cat robot_tests\resources\variables.robot | Select-String "LOGOUT_LINK"
```

### ❌ Application non démarrée

```powershell
# Vérifier si le serveur tourne
curl http://localhost:5000

# Si non, démarrer
.\start_windows.bat
```

### ❌ Test échoue sur un élément

Les tests utilisent maintenant des sélecteurs multiples:
```robot
${LOGOUT_LINK}    css:a[href*="logout"]
```

Si un élément n'est pas trouvé, vérifiez que la page est chargée:
```robot
Wait Until Page Contains Element    css:body    timeout=10s
```

---

## 📝 PERSONNALISATION

### Modifier les Sous-titres

Éditez `test_video_demo_complete.robot`:
```robot
Add Subtitle    Votre texte ici    durée_en_secondes
```

### Changer le Style des Sous-titres

Éditez `merge_video.py`, ligne 45:
```python
'force_style='FontName=Arial,FontSize=28,PrimaryColour=&HFFFF00&'
```

Couleurs (format BGR en hexadécimal):
- Blanc: `&HFFFFFF&`
- Jaune: `&H00FFFF&`
- Rouge: `&H0000FF&`
- Vert: `&H00FF00&`

### Ajouter des Tests

```robot
DEMO_XXX - Mon Test
    [Documentation]    Description
    [Tags]    custom
    Log To Console    🎯 MON TEST${\n}

    Add Subtitle    🎯 Mon étape personnalisée    3
    # Votre code ici
    Take High Quality Screenshot With Subtitle    custom_step    Mon sous-titre

    Log To Console    ✅ Test terminé${\n}
```

---

## 🎯 COMMANDES UTILES

```powershell
# Lancer la démo complète
.\run_video_demo_windows.bat

# Test sans vidéo (screenshots seulement)
.\run_demo_windows.bat

# Fusionner automatiquement
python merge_video.py

# Fusionner manuellement
python merge_video.py chemin/video.mp4 chemin/subtitles.srt

# Tester FFmpeg
.\test_video_recording.bat

# Ouvrir le dossier résultats
explorer robot_results\video_demo
```

---

## 📊 STATISTIQUES DÉMO COMPLÈTE

| Métrique | Valeur |
|----------|--------|
| **Tests** | 18 |
| **Screenshots** | 26+ |
| **Sous-titres** | 50+ |
| **Utilisateurs** | 3 (Admin, User, Bank) |
| **Durée** | 5-7 min |
| **Pages visitées** | 15+ |
| **Fonctionnalités** | 10+ |

---

## ✅ CHECKLIST AVANT DÉMO

- [ ] FFmpeg installé et fonctionnel
- [ ] Terminal redémarré après install FFmpeg
- [ ] Application SarfX lancée (port 5000)
- [ ] Base de données peuplée
- [ ] Pas d'autre Chrome ouvert
- [ ] Connexion réseau stable
- [ ] Espace disque suffisant (~500 MB)

---

## 🎬 COMMANDE FINALE

```powershell
# Terminal 1
.\start_windows.bat

# Terminal 2 (après démarrage app)
.\run_video_demo_windows.bat

# Après la démo
python merge_video.py
```

**🎉 C'est tout ! Votre vidéo professionnelle avec sous-titres est prête !**

---

## 📞 SUPPORT

**Fichiers importants:**
- Tests: `robot_tests/tests/test_video_demo_complete.robot`
- Variables: `robot_tests/resources/variables.robot`
- Sous-titres: `robot_tests/resources/SubtitlesGenerator.py`
- Fusion: `merge_video.py`

**Logs:**
- Robot: `robot_results/video_demo/video-demo-log-*.html`
- Rapport: `robot_results/video_demo/video-demo-report-*.html`
