# 🎥✨ DÉMO VIDÉO + SCREENSHOTS - GUIDE COMPLET

## ✅ Installation Terminée !

J'ai créé un système complet de capture vidéo et screenshots pour votre application SarfX.

---

## 📦 Fichiers Créés

### Scripts d'exécution
- ✅ `run_video_demo_windows.bat` - Démo complète avec vidéo
- ✅ `install_ffmpeg_windows.bat` - Installation FFmpeg
- ✅ `test_video_recording.bat` - Test rapide vidéo (5 sec)

### Bibliothèques Robot Framework
- ✅ `robot_tests/resources/VideoRecorder.py` - Capture vidéo
- ✅ `robot_tests/resources/ChromeOptionsLibrary.py` - Config Chrome (mise à jour)

### Tests
- ✅ `robot_tests/tests/test_video_demo.robot` - Test complet avec vidéo
- ✅ `robot_tests/tests/test_full_demo.robot` - Test headless (existe déjà)

### Documentation
- ✅ `VIDEO_DEMO_GUIDE.md` - Guide complet

---

## 🚀 DÉMARRAGE RAPIDE

### Étape 1: Redémarrer le Terminal
**IMPORTANT** : FFmpeg vient d'être installé, mais nécessite un redémarrage du terminal pour être disponible.

```powershell
# Fermez ce terminal PowerShell et ouvrez-en un nouveau
# Ou tapez simplement:
exit
```

Puis rouvrez PowerShell dans VS Code.

### Étape 2: Vérifier FFmpeg
```powershell
ffmpeg -version
```

Si ça fonctionne, vous verrez : `ffmpeg version 8.0.1...`

### Étape 3: Lancer l'Application
```powershell
.\start_windows.bat
```

### Étape 4: Dans un NOUVEAU terminal, lancer la démo
```powershell
.\run_video_demo_windows.bat
```

---

## 🎬 Résultats

### Vidéo
📹 **Emplacement** : `robot_results/video_demo/videos/demo_YYYYMMDD_HHMMSS.mp4`

**Caractéristiques** :
- Format : MP4 (H.264)
- Résolution : 1920x1080
- Frame rate : 30 fps
- Durée : ~2-5 minutes (selon la démo)
- Taille : ~50-100 MB

### Screenshots
📸 **Emplacement** : `robot_results/video_demo/screenshots/`

**Liste des captures** :
1. `01_landing_page_*.png` - Page d'accueil
2. `02_login_page_*.png` - Écran de connexion
3. `03_email_entered_*.png` - Email saisi
4. `04_password_entered_*.png` - Mot de passe saisi
5. `05_dashboard_admin_*.png` - Dashboard admin
6. `06_admin_home_*.png` - Vue admin
7. `07_users_management_*.png` - Gestion utilisateurs
8. `08_wallets_management_*.png` - Gestion wallets
9. `09_transactions_admin_*.png` - Transactions admin
10. `10_banks_management_*.png` - Gestion banques
11. `11_logout_admin_*.png` - Déconnexion admin
12. `12_user_dashboard_*.png` - Dashboard user
13. `13_converter_page_*.png` - Convertisseur
14. `14_amount_entered_*.png` - Montant saisi
15. `15_currencies_selected_*.png` - Devises sélectionnées
16. `16_conversion_result_*.png` - Résultat conversion
17. `17_user_wallets_*.png` - Portefeuilles user
18. `18_user_transactions_*.png` - Transactions user
19. `19_atm_map_*.png` - Carte ATMs
20. `20_user_profile_*.png` - Profil user
21. `21_demo_end_*.png` - Fin de démo

---

## 🎯 Deux Modes Disponibles

### Mode 1: VIDÉO + SCREENSHOTS (Navigateur visible)
```bash
.\run_video_demo_windows.bat
```
- ✅ Enregistrement vidéo complet de l'écran
- ✅ Screenshots HD à chaque étape
- ✅ Navigateur Chrome VISIBLE pendant l'enregistrement
- ✅ Parfait pour présentation/démo client

**Résultats** : `robot_results/video_demo/`

### Mode 2: SCREENSHOTS uniquement (Headless)
```bash
.\run_demo_windows.bat
```
- ✅ Screenshots HD
- ✅ Navigateur headless (invisible)
- ✅ Plus rapide
- ✅ Parfait pour tests automatisés

**Résultats** : `robot_results/demo/`

---

## 🛠️ Dépannage

### Si FFmpeg n'est pas reconnu après installation

**Solution 1** : Redémarrer le terminal
```powershell
exit
# Puis rouvrir PowerShell
ffmpeg -version
```

**Solution 2** : Vérifier le PATH manuellement
```powershell
$env:Path -split ';' | Select-String ffmpeg
```

**Solution 3** : Réinstaller
```powershell
.\install_ffmpeg_windows.bat
```

### Si la vidéo ne démarre pas

1. Vérifier que l'application SarfX est lancée :
   ```bash
   .\start_windows.bat
   ```

2. Tester l'enregistrement vidéo seul :
   ```bash
   .\test_video_recording.bat
   ```

3. Vérifier les logs Robot Framework :
   ```
   robot_results/video_demo/video-demo-log-*.html
   ```

### Si Chrome ne s'ouvre pas

```bash
# Test du diagnostic Chrome
python test_chrome.py
```

---

## 🎨 Personnalisation

### Modifier la durée des pauses (vidéo plus lente)

Éditez `robot_tests/tests/test_video_demo.robot` :
```robot
Wait And Screenshot    step_name    5s  # Au lieu de 2s
```

### Changer la qualité vidéo

Éditez `robot_tests/resources/VideoRecorder.py` :
```python
'-crf', '18',        # Meilleure qualité (18 au lieu de 23)
'-framerate', '60',  # 60 fps au lieu de 30
```

### Ajouter des tests personnalisés

Copiez un test existant dans `test_video_demo.robot` :
```robot
DEMO_XXX - Mon Test Custom
    [Documentation]    Description
    [Tags]    custom
    Log To Console    🎯 MON TEST${\n}

    Go To    ${BASE_URL}/ma-page
    Wait And Screenshot    mon_test    3s

    Log To Console    ✅ Test terminé${\n}
```

---

## 📊 Rapport HTML

À chaque exécution, un rapport HTML est généré :
- **Emplacement** : `robot_results/video_demo/video-demo-report-*.html`
- **Contenu** :
  - ✅ Résumé des tests (PASS/FAIL)
  - 📸 Screenshots intégrés
  - ⏱️ Durée de chaque étape
  - 📝 Logs détaillés

Le rapport s'ouvre automatiquement à la fin de la démo !

---

## 💡 Conseils

### Pour une démo professionnelle :
1. Fermez les applications inutiles (notifications, etc.)
2. Utilisez un fond d'écran neutre
3. Masquez la barre des tâches Windows (auto-hide)
4. Lancez Chrome en plein écran

### Pour des screenshots de qualité :
- Utilisez `Wait And Screenshot` avec 3-5s de délai
- Vérifiez que la page est complètement chargée
- Ajoutez des `Sleep` avant les captures importantes

### Pour une vidéo fluide :
- Fermez Chrome/Edge/Firefox si déjà ouverts
- Désactivez les effets visuels Windows
- Utilisez un SSD (pas HDD) pour l'enregistrement

---

## 🎯 Checklist Avant Démo

- [ ] Application SarfX lancée (`.\start_windows.bat`)
- [ ] Base de données peuplée (`.\seed_database_windows.bat`)
- [ ] FFmpeg installé et fonctionnel (`ffmpeg -version`)
- [ ] Terminal redémarré après installation FFmpeg
- [ ] Pas d'autres Chrome ouverts
- [ ] Connexion réseau stable

---

## 🚀 Commande Finale

```powershell
# Dans terminal 1 : Démarrer l'app
.\start_windows.bat

# Dans terminal 2 : Lancer la démo vidéo
.\run_video_demo_windows.bat
```

---

## 📞 Support

Si vous avez des problèmes :
1. Consultez `VIDEO_DEMO_GUIDE.md`
2. Vérifiez les logs : `robot_results/video_demo/video-demo-log-*.html`
3. Testez FFmpeg : `.\test_video_recording.bat`

---

**🎬 Bonne démo ! 📹✨**
