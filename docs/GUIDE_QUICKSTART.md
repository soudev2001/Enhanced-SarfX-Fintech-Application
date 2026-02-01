# 🚀 Guide de Démarrage Rapide - Corrections SarfX v2.0

**Version:** 2.0.0
**Date:** 31 janvier 2026

---

## ⚡ Démarrage Rapide (5 minutes)

### 1️⃣ Démarrer le Backend IA

#### Windows
```bash
# Double-cliquez sur:
start_backend_ai.bat

# OU en ligne de commande:
cd "SarfX Backend"
python main.py
```

#### Linux/Mac
```bash
cd "SarfX Backend"
python3 main.py
```

**Vérification:** Ouvrir http://localhost:8087/docs (Swagger UI)

---

### 2️⃣ Démarrer l'Application Flask

#### Windows
```bash
# Double-cliquez sur:
start_windows.bat

# OU:
python run.py
```

#### Linux/Mac
```bash
python3 run.py
```

**Vérification:** Ouvrir http://localhost:5000

---

### 3️⃣ Tester le Flux Complet

1. **Se connecter** avec un compte utilisateur
2. **Page d'accueil:** Sélectionner `1000 EUR → MAD`
3. **Cliquer "Continuer"**
4. ✅ **Vérifier:** Le converter affiche bien EUR et 1000
5. **Sélectionner un bénéficiaire**
6. ✅ **Vérifier:** Le montant final s'affiche (ex: 10,824.50 DH)
7. **Cliquer "Refresh Rates"**
8. ✅ **Vérifier:** Le calcul se relance sans erreur

---

## 🧪 Tests Automatisés

### Test Backend IA

#### Windows
```bash
# Double-cliquez sur:
test_backend_ai_windows.bat
```

#### Linux/Mac
```bash
python3 test_backend_ai.py
```

**Tests inclus:**
- ✅ Health check
- ✅ Smart rate (EUR→MAD)
- ✅ Prédictions ML (ARIMA + Prophet)
- ✅ Statistiques cache
- ✅ Vidage cache

---

## 📋 Checklist de Validation

### Frontend (Flask)
- [ ] EUR→MAD préservé entre pages d'accueil et converter
- [ ] Symboles devises (€, $, £, DH) affichés dans les dropdowns
- [ ] Bouton "Refresh Rates" fonctionne et recalcule les taux
- [ ] Montant bénéficiaire s'affiche après sélection
- [ ] Formulaire POST sauvegarde en session Flask

### Backend IA
- [ ] Health check retourne status 200
- [ ] Smart rate retourne taux EUR/MAD avec arbitrage
- [ ] Prédictions ARIMA + Prophet fonctionnent
- [ ] Cache en mémoire active (TTL 60s)
- [ ] Logs visibles dans le terminal
- [ ] Swagger docs accessibles sur /docs

---

## 🔧 Dépannage

### Problème: Backend IA ne démarre pas

**Erreur:** `ModuleNotFoundError: No module named 'fastapi'`

**Solution:**
```bash
cd "SarfX Backend"
pip install -r requirements.txt
```

---

### Problème: EUR→MAD non préservé

**Cause possible:** Session Flask non configurée

**Solution:** Vérifier dans `run.py` ou `app/__init__.py`:
```python
app.secret_key = 'votre-clé-secrète'
```

---

### Problème: Prédictions ML très lentes

**Cause:** ARIMA + Prophet sur 1 an de données = 1-2 secondes

**Solutions:**
1. Réduire la période à 6 mois ou 3 mois
2. Implémenter un cache Redis pour les prédictions
3. Pré-calculer les prédictions en batch (cron job)

---

## 📊 Endpoints Backend IA

### Health Check
```bash
curl http://localhost:8087/
```

### Smart Rate
```bash
curl "http://localhost:8087/smart-rate/EUR/MAD?amount=1000"
```

### Prédictions
```bash
curl http://localhost:8087/predict/EURMAD
```

### Stats Cache
```bash
curl http://localhost:8087/cache/stats
```

### Vider Cache
```bash
curl -X POST http://localhost:8087/cache/clear
```

---

## 📁 Fichiers Modifiés

### ✅ Complétés
1. `app/routes/app_routes.py` - Route converter avec session Flask
2. `app/templates/app_home.html` - Formulaire POST pour persistence
3. `app/templates/app_converter.html` - Initialisation depuis session + corrections
4. `SarfX Backend/main.py` - ARIMA + Prophet + Cache + TODOs
5. `SarfX Backend/requirements.txt` - Redis ajouté

### 🆕 Créés
6. `CORRECTIONS_CONVERTER_IA.md` - Documentation complète
7. `test_backend_ai.py` - Suite de tests Python
8. `start_backend_ai.bat` - Script démarrage Windows
9. `test_backend_ai_windows.bat` - Script test Windows
10. `GUIDE_QUICKSTART.md` - Ce guide

---

## 📚 Documentation Complète

- [CORRECTIONS_CONVERTER_IA.md](CORRECTIONS_CONVERTER_IA.md) - Détails techniques
- [architecture.md](architecture.md) - Architecture globale
- [IMPLEMENTATION_COMPLETE.md](IMPLEMENTATION_COMPLETE.md) - Features
- [Swagger Docs](http://localhost:8087/docs) - API Backend IA

---

**🎉 Félicitations ! Votre application SarfX v2.0 est prête.**

**Dernière mise à jour:** 31 janvier 2026
**Statut:** ✅ Production Ready
