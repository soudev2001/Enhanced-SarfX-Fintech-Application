# 🎥 Guide Démo Vidéo SarfX

## 📋 Prérequis

✅ Chrome installé
✅ Python + venv activé
✅ Application SarfX lancée (port 5000)
⚠️ FFmpeg requis pour la vidéo

---

## 🚀 Installation Rapide FFmpeg

### Option 1: Script automatique (Recommandé)
```bash
.\install_ffmpeg_windows.bat
```

### Option 2: Winget (manuel)
```powershell
winget install --id Gyan.FFmpeg -e
```

### Option 3: Chocolatey (manuel)
```powershell
choco install ffmpeg -y
```

---

## 🎬 Lancer la Démo avec Vidéo

### Mode Complet (Vidéo + Screenshots)
```bash
.\run_video_demo_windows.bat
```

**Résultats** :
- 📹 Vidéo complète : `robot_results/video_demo/videos/demo_YYYYMMDD_HHMMSS.mp4`
- 📸 Screenshots HD : `robot_results/video_demo/screenshots/`
- 📊 Rapport HTML : `robot_results/video_demo/video-demo-report-*.html`

### Mode Screenshots uniquement (sans FFmpeg)
```bash
.\run_demo_windows.bat
```

**Résultats** :
- 📸 Screenshots : `robot_results/demo/screenshots/`
- 📊 Rapport HTML : `robot_results/demo/demo-report-*.html`

---

## 🎯 Fonctionnalités

### Vidéo
- ✅ Enregistrement écran complet en MP4
- ✅ Qualité 1920x1080 @ 30fps
- ✅ Codec H.264 (compatible tous lecteurs)
- ✅ Navigateur Chrome visible pendant l'enregistrement

### Screenshots
- ✅ Capture à chaque étape importante
- ✅ Résolution haute définition
- ✅ Noms descriptifs avec timestamp
- ✅ Format PNG

### Tests inclus
1. 🏠 Landing page
2. 👤 Connexion Admin
3. 📊 Dashboard Admin (users, wallets, transactions, banques)
4. 🔄 Changement de session
5. 💱 Convertisseur de devises
6. 💰 Portefeuilles utilisateur
7. 📜 Historique transactions
8. 🏧 Carte des ATMs
9. ⚙️ Profil utilisateur

---

## 🛠️ Dépannage

### FFmpeg non trouvé
```bash
# Vérifier l'installation
ffmpeg -version

# Si non trouvé, installer avec:
.\install_ffmpeg_windows.bat
```

### Application non démarrée
```bash
# Démarrer l'application d'abord
.\start_windows.bat

# Puis dans un autre terminal:
.\run_video_demo_windows.bat
```

### Erreur d'import VideoRecorder
```bash
# Réactiver l'environnement virtuel
.\venv\Scripts\activate

# Relancer la démo
.\run_video_demo_windows.bat
```

---

## 📦 Structure des Résultats

```
robot_results/
├── video_demo/                    # Démo avec vidéo
│   ├── videos/
│   │   └── demo_20260129_0630.mp4
│   ├── screenshots/
│   │   ├── 01_landing_page_*.png
│   │   ├── 02_login_page_*.png
│   │   └── ...
│   ├── video-demo-report-*.html
│   └── video-demo-log-*.html
│
└── demo/                          # Démo headless (sans vidéo)
    ├── screenshots/
    ├── demo-report-*.html
    └── demo-log-*.html
```

---

## 🎨 Personnalisation

### Modifier la résolution vidéo
Éditez `robot_tests/resources/VideoRecorder.py` :
```python
'-framerate', '60',        # 60 fps au lieu de 30
'-video_size', '2560x1440' # 2K au lieu de 1080p
```

### Ajouter des tests
Éditez `robot_tests/tests/test_video_demo.robot` :
```robot
DEMO_XXX - Mon Test
    [Documentation]    Description
    [Tags]    custom
    Log To Console    🎯 MON TEST${\n}

    # Votre code ici
    Wait And Screenshot    custom_step    3s
```

---

## 💡 Astuces

### Vidéo plus fluide
- Fermez les applications gourmandes
- Augmentez le délai entre actions : `Sleep 3s`

### Screenshots haute qualité
- Utilisez `Wait And Screenshot` au lieu de `Take High Quality Screenshot`
- Ajustez le délai : `Wait And Screenshot step_name 5s`

### Plusieurs vidéos
- Chaque exécution crée une nouvelle vidéo avec timestamp
- Les anciennes vidéos ne sont pas écrasées

---

## ❓ Support

- 📖 Documentation Robot Framework : https://robotframework.org
- 🎥 Documentation FFmpeg : https://ffmpeg.org/documentation.html
- 🐛 Issues : Vérifiez les logs dans `robot_results/video_demo/`
