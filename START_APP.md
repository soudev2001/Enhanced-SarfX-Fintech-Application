# 🚀 Guide de Démarrage - SarfX Fintech App

## ⚡ Démarrage Rapide (3 étapes)

### Étape 1: Ouvrir le Terminal
```bash
Ctrl + ` (ou Cmd + ` sur Mac)
```

### Étape 2: Installer les dépendances (première fois uniquement)
```bash
pip install -r requirements.txt
```

### Étape 3: Démarrer l'application
```bash
python run.py
```

---

## 🌐 Accéder à l'Application dans votre Navigateur

### Méthode 1: Via le Panel PORTS (Recommandé)

1. **Regardez en bas de VS Code** → Cliquez sur l'onglet **"PORTS"**
   
   ![Ports Panel](https://docs.github.com/assets/cb-23656/images/help/codespaces/ports-tab.png)

2. **Trouvez le port 5000** dans la liste

3. **Cliquez sur l'icône globe 🌐** ou sur l'URL pour ouvrir dans le navigateur

### Méthode 2: Via le Menu Contextuel

1. Dans le panel **PORTS**, faites un **clic droit** sur le port **5000**
2. Sélectionnez **"Open in Browser"**

### Méthode 3: Copier l'URL

1. Dans le panel **PORTS**, cliquez sur l'icône **📋** pour copier l'URL
2. Collez dans votre navigateur

---

## 📍 Ports Utilisés

| Port | Service | Description |
|------|---------|-------------|
| **5000** | Flask Frontend | Interface utilisateur principale |
| **8087** | AI Backend | Service IA (optionnel) |

---

## 🔧 Rendre le Port Public

Si vous voulez partager l'URL avec quelqu'un:

1. Dans le panel **PORTS**, clic droit sur le port **5000**
2. Sélectionnez **"Port Visibility"** → **"Public"**

---

## ❓ Résolution de Problèmes

### Le port 5000 n'apparaît pas?
```bash
# Vérifier que l'app tourne
lsof -i :5000

# Redémarrer l'app
pkill -f python && python run.py
```

### Erreur de dépendances?
```bash
pip install -r requirements.txt --upgrade
```

### Erreur MongoDB?
Vérifiez que vous avez accès à Internet (MongoDB Atlas)

---

## 🎯 Commandes Utiles

```bash
# Démarrer l'application
python run.py

# Arrêter l'application
Ctrl + C

# Voir les logs
# (Les logs s'affichent directement dans le terminal)

# Vérifier les ports actifs
lsof -i -P -n | grep LISTEN
```

---

## 📱 URLs de l'Application

Une fois démarrée, votre app sera accessible à:

- **Frontend**: `https://[votre-codespace]-5000.app.github.dev`
- **API**: `https://[votre-codespace]-5000.app.github.dev/api/`

L'URL exacte sera visible dans le panel **PORTS** de VS Code.

---

## ✅ Checklist de Démarrage

- [ ] Terminal ouvert
- [ ] `pip install -r requirements.txt` exécuté
- [ ] `python run.py` exécuté
- [ ] Message "Running on http://0.0.0.0:5000" visible
- [ ] Port 5000 visible dans le panel PORTS
- [ ] Application ouverte dans le navigateur

---

**🎉 Bon développement avec SarfX!**
