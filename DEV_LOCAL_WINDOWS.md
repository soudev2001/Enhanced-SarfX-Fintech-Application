# SarfX - Développement Local (Windows)

Ce guide explique comment configurer SarfX pour le développement local sur Windows.

## 🚀 Installation Rapide

### 1. Prérequis
- **Python 3.10+** : [Télécharger Python](https://www.python.org/downloads/)
- **Git** : [Télécharger Git](https://git-scm.com/download/win)
- **Chrome** (pour les tests Selenium) : [Télécharger Chrome](https://www.google.com/chrome/)

### 2. Installation
```batch
# Cloner le projet
git clone https://github.com/soudev2001/Enhanced-SarfX-Fintech-Application.git
cd Enhanced-SarfX-Fintech-Application

# Changer vers la branche dev-local
git checkout dev-local

# Lancer l'installation automatique
setup_windows.bat
```

### 3. Configuration
Éditez le fichier `.env` créé automatiquement :
```
FLASK_ENV=development
SECRET_KEY=votre-cle-secrete
OPENAI_API_KEY=sk-...  # Optionnel
```

### 4. Initialiser la base de données
```batch
seed_database_windows.bat
```

### 5. Démarrer l'application
```batch
start_windows.bat
```
Puis ouvrez http://localhost:5000

---

## 📁 Structure des Scripts Windows

| Script | Description |
|--------|-------------|
| `setup_windows.bat` | Installation complète (venv, dépendances, .env) |
| `start_windows.bat` | Démarrage rapide du serveur Flask |
| `run_tests_windows.bat` | Exécution des tests Robot Framework |
| `run_demo_windows.bat` | Démo complète avec screenshots |
| `seed_database_windows.bat` | Initialisation de la base de données |

---

## 🧪 Tests

### Tests API uniquement (rapide)
```batch
run_tests_windows.bat
# Choisir option 1
```

### Tests Selenium (navigateur)
```batch
run_tests_windows.bat
# Choisir option 2
```

### Démo complète
```batch
run_demo_windows.bat
```

---

## 👥 Comptes de Test

| Rôle | Email | Mot de passe |
|------|-------|--------------|
| Admin | admin@sarfx.io | Admin123! |
| User | user@demo.com | Demo123! |
| Bank | bank.respo@boa.ma | Bank123! |

---

## 🔧 Configuration Avancée

### Base de données PostgreSQL
Si vous préférez PostgreSQL au lieu de SQLite :

1. Installez PostgreSQL
2. Créez une base de données `sarfx`
3. Modifiez `.env` :
```
DATABASE_URL=postgresql://user:password@localhost:5432/sarfx
```

### Installation de FFmpeg (pour vidéos)
1. Téléchargez [FFmpeg](https://ffmpeg.org/download.html)
2. Extrayez dans `C:\ffmpeg`
3. Ajoutez `C:\ffmpeg\bin` au PATH

---

## 🐛 Dépannage

### "Python n'est pas reconnu"
- Réinstallez Python en cochant "Add to PATH"

### "Robot Framework not found"
```batch
venv\Scripts\activate
pip install robotframework robotframework-seleniumlibrary
```

### "ChromeDriver error"
```batch
pip install webdriver-manager
```

### Port 5000 déjà utilisé
Modifiez `run.py` :
```python
app.run(port=5001)
```

---

## 📞 Support

- **Issues** : https://github.com/soudev2001/Enhanced-SarfX-Fintech-Application/issues
- **Documentation** : Voir `VISUAL_GUIDE.md`
