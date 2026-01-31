import os
import uvicorn
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pymongo import MongoClient
import warnings
from statsmodels.tsa.arima.model import ARIMA
from prophet import Prophet
from sklearn.metrics import mean_absolute_error
import logging

# --- CONFIGURATION (PROD) ---
warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Certificat SSL pour MongoDB Atlas (Linux servers)
try:
    import certifi
    CA_BUNDLE = certifi.where()
except ImportError:
    CA_BUNDLE = None

# Identifiants (Dans une vraie prod, utilisez des variables d'environnement)
MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://soufiane:gogo@cluster0.05omqhe.mongodb.net/SarfX_Enhanced")
SMTP_EMAIL = "starkxgroup@gmail.com"
SMTP_PASSWORD = "mpnkmpqeypjsvern"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
ADMIN_EMAIL = "starkxgroup@gmail.com"
COINAPI_KEY = os.environ.get("COINAPI_KEY", "VOTRE_API_KEY_ICI") # Placeholder
AI_PORT = int(os.environ.get("AI_PORT", 8087))

# Cache en mémoire pour les taux (évite les appels répétés)
# TODO: Remplacer par Redis pour un vrai cache distribué en production
RATE_CACHE = {}
CACHE_TTL = 60  # secondes

# --- INITIALISATION ---
app = FastAPI(title="SarfX Core Engine", description="Moteur Fintech d'Arbitrage & IA")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connexion Base de Données (Persistance)
try:
    # Configuration avec certificat SSL pour serveurs Linux
    mongo_options = {
        "serverSelectionTimeoutMS": 5000,
        "connectTimeoutMS": 10000,
        "retryWrites": True
    }
    if CA_BUNDLE:
        mongo_options["tlsCAFile"] = CA_BUNDLE

    client = MongoClient(MONGO_URI, **mongo_options)
    # Test de connexion
    client.admin.command('ping')
    db = client.get_database("SarfX_Enhanced")
    rates_collection = db.rates_history
    print("✅ [MongoDB] Connecté à SarfX_Enhanced avec succès.")
except Exception as e:
    print(f"⚠️ [MongoDB] Mode hors-ligne activé: {e}")
    rates_collection = None
    db = None

# --- COUCHE D'ACQUISITION (INPUT LAYER) ---

def get_cached_rate(cache_key):
    """Récupère un taux du cache si disponible et valide"""
    if cache_key in RATE_CACHE:
        cached_data = RATE_CACHE[cache_key]
        if (datetime.utcnow() - cached_data['timestamp']).total_seconds() < CACHE_TTL:
            logging.info(f"✓ Cache hit pour {cache_key}")
            return cached_data['rate']
    return None

def set_cached_rate(cache_key, rate):
    """Enregistre un taux dans le cache"""
    RATE_CACHE[cache_key] = {
        'rate': rate,
        'timestamp': datetime.utcnow()
    }

def fetch_fiat_rate(base, target):
    """
    Source 1 : Marché Interbancaire (Frankfurter/Yahoo)

    TODO: Ajouter support pour d'autres APIs de taux de change:
    - ExchangeRate-API.com (gratuit, 1500 req/mois)
    - Fixer.io (freemium)
    - Open Exchange Rates
    """
    cache_key = f"fiat_{base}_{target}"
    cached = get_cached_rate(cache_key)
    if cached:
        return cached

    try:
        # Priorité API Rapide
        url = f"https://api.frankfurter.app/latest?from={base}&to={target}"
        resp = requests.get(url, timeout=2)
        if resp.status_code == 200:
            rate = resp.json()['rates'][target]
            set_cached_rate(cache_key, rate)
            logging.info(f"✓ Taux {base}/{target} récupéré: {rate} (Frankfurter)")
            return rate
    except Exception as e:
        logging.warning(f"Frankfurter API échec: {e}")

    # Fallback Yahoo Finance (Plus lent mais robuste)
    try:
        ticker = f"{base}{target}=X"
        df = yf.download(ticker, period="1d", interval="1m", progress=False)
        if not df.empty:
            rate = df['Close'].iloc[-1]
            set_cached_rate(cache_key, rate)
            logging.info(f"✓ Taux {base}/{target} récupéré: {rate} (Yahoo Finance)")
            return rate
    except Exception as e:
        logging.error(f"Yahoo Finance échec: {e}")

    logging.error(f"✗ Impossible de récupérer le taux {base}/{target}")
    return 0.0 # Echec

def fetch_crypto_implied_rate(base, target):
    """
    Source 2 : Marché Crypto (USDT Implied Rate)

    TODO: Intégrer vraies APIs crypto au lieu de simulation:
    - Binance P2P API pour les taux USDT/MAD réels
    - CoinGecko API pour les prix crypto
    - Kraken API pour volumes et liquidité

    NOTE: Actuellement simule une prime crypto de +1.5% sur le taux fiat
    """

    fiat_rate = fetch_fiat_rate(base, target)
    if fiat_rate == 0:
        return 0.0

    # TODO: Remplacer par appel API Binance P2P réel
    # Exemple: GET https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search
    # Params: fiat=MAD, tradeType=BUY, asset=USDT

    # Simulation d'une prime de marché crypto (ex: +1.5% vs officiel)
    crypto_premium = 1.015
    rate = fiat_rate * crypto_premium
    logging.info(f"✓ Taux crypto simulé {base}/{target}: {rate} (Premium: +1.5%)")
    return rate

# --- COUCHE DE TRAITEMENT (PROCESS LAYER) ---

def calculate_best_execution(base, target, amount):
    """
    Cœur de l'Arbitrage : Trouve le meilleur chemin pour l'argent

    TODO: Améliorer l'arbitrage avec:
    - Calcul des frais réels par provider (bank, wise, western union, etc.)
    - Prise en compte des délais de livraison
    - Score de fiabilité des providers (basé sur historique)
    - Optimisation multi-routes (ex: EUR->USD->MAD si meilleur)
    """

    # 1. Acquisition
    rate_fiat = fetch_fiat_rate(base, target)
    rate_crypto = fetch_crypto_implied_rate(base, target)
    rate_bank = rate_fiat * 0.975 # Les banques prennent ~2.5% de marge

    # 2. Arbitrage
    best_source_rate = max(rate_fiat, rate_crypto)
    source_name = "Marché Crypto (USDT)" if rate_crypto > rate_fiat else "Marché Interbancaire"

    # 3. Marge SarfX (Dynamique)
    # TODO: Rendre la marge dynamique selon:
    # - Volume de la transaction (plus le volume est gros, plus la marge baisse)
    # - Volatilité du marché (augmenter en période instable)
    # - Fidélité client (récompenser les utilisateurs réguliers)
    sarfx_margin = 0.005 # 0.5% (Très compétitif)
    sarfx_rate = best_source_rate * (1 - sarfx_margin)

    logging.info(f"✓ Arbitrage {base}/{target}: Meilleur taux = {sarfx_rate:.4f} ({source_name})")

    return {
        "rates": {
            "bank": rate_bank,
            "market": rate_fiat,
            "crypto": rate_crypto,
            "sarfx": sarfx_rate
        },
        "best_source": source_name,
        "savings": (amount * sarfx_rate) - (amount * rate_bank)
    }

# --- MOTEUR IA (PREDICTION LAYER) ---

def train_arima_model(df, order=(5, 1, 0)):
    """
    Entraîne un modèle ARIMA sur les données historiques

    ARIMA (AutoRegressive Integrated Moving Average):
    - AR(p): régression sur p valeurs passées
    - I(d): différenciation d'ordre d pour stationnarité
    - MA(q): moyenne mobile sur q erreurs passées

    TODO: Optimiser les hyperparamètres (p,d,q) avec auto_arima ou grid search
    """
    try:
        model = ARIMA(df['Close'], order=order)
        fitted = model.fit()
        return fitted
    except Exception as e:
        logging.error(f"ARIMA training failed: {e}")
        return None

def train_prophet_model(df):
    """
    Entraîne un modèle Prophet (Meta/Facebook) sur les données historiques

    Prophet est spécialisé dans les séries temporelles avec:
    - Tendances non-linéaires
    - Saisonnalité multiple (jour/semaine/année)
    - Gestion des jours fériés
    - Robuste aux données manquantes

    TODO: Ajouter des régresseurs externes (événements économiques, news, etc.)
    """
    try:
        # Prophet nécessite colonnes 'ds' (date) et 'y' (valeur)
        prophet_df = pd.DataFrame({
            'ds': df.index,
            'y': df['Close']
        })

        model = Prophet(
            daily_seasonality=True,
            weekly_seasonality=True,
            yearly_seasonality=False,  # Pas assez de données historiques généralement
            changepoint_prior_scale=0.05  # Flexibilité des tendances
        )
        model.fit(prophet_df)
        return model
    except Exception as e:
        logging.error(f"Prophet training failed: {e}")
        return None

def predict_with_arima(model, steps=7):
    """Prédiction ARIMA pour N jours"""
    try:
        forecast = model.forecast(steps=steps)
        return forecast.tolist()
    except Exception as e:
        logging.error(f"ARIMA prediction failed: {e}")
        return None

def predict_with_prophet(model, steps=7):
    """Prédiction Prophet pour N jours"""
    try:
        future = model.make_future_dataframe(periods=steps)
        forecast = model.predict(future)
        # Retourner seulement les prédictions futures
        return forecast['yhat'].tail(steps).tolist()
    except Exception as e:
        logging.error(f"Prophet prediction failed: {e}")
        return None

def generate_ai_signal(pair):
    """
    Analyse la tendance pour donner un conseil (Timing)

    TODO: Enrichir l'analyse avec:
    - Indicateurs techniques (RSI, MACD, Bollinger Bands)
    - Analyse de sentiment (Twitter, news financières)
    - Détection d'anomalies (spikes inhabituels)
    - Scoring de confiance basé sur plusieurs indicateurs
    """
    ticker = f"{pair}=X"
    try:
        df = yf.download(ticker, period="1mo", interval="1d", progress=False)
        if df.empty:
            return "NEUTRE"

        # Analyse simple : Moyenne Mobile Exponentielle (EMA)
        short_window = 5
        df['EMA'] = df['Close'].ewm(span=short_window, adjust=False).mean()

        last_close = df['Close'].iloc[-1]
        last_ema = df['EMA'].iloc[-1]

        # Logique de signal
        if last_close < last_ema * 0.995: # Prix significativement sous la moyenne -> Potentiel rebond
            signal = "ACHETER (Taux bas)"
        elif last_close > last_ema * 1.005: # Prix haut -> Attendre correction
            signal = "ATTENDRE (Taux haut)"
        else:
            signal = "NEUTRE"

        logging.info(f"✓ Signal IA pour {pair}: {signal}")
        return signal
    except Exception as e:
        logging.error(f"AI signal generation failed: {e}")
        return "INDISPONIBLE"

# --- TÂCHES DE FOND (BACKGROUND) ---

def archive_rate(base, target, rate, source):
    """
    Historisation dans MongoDB pour l'apprentissage futur

    TODO: Utiliser ces données pour:
    - Entraîner des modèles ML périodiquement (batch nightly)
    - Calculer des statistiques de performance (accuracy vs reality)
    - Détecter des patterns d'arbitrage récurrents
    - Dashboard analytics pour admin
    """
    if rates_collection is None:
        return
    try:
        rates_collection.insert_one({
            "pair": f"{base}/{target}",
            "rate": float(rate),
            "source": source,
            "timestamp": datetime.utcnow()
        })
        logging.info(f"✓ Taux archivé: {base}/{target} = {rate}")
    except Exception as e:
        logging.error(f"Erreur Archivage: {e}")

# --- API ENDPOINTS ---

@app.get("/")
def health():
    """
    Health check endpoint avec statistiques système

    TODO: Ajouter monitoring plus avancé:
    - Métriques Prometheus
    - Tracing distribué (Jaeger)
    - Alerting (PagerDuty, Slack)
    - Uptime Robot
    """
    cache_stats = {
        "entries": len(RATE_CACHE),
        "ttl_seconds": CACHE_TTL,
        "type": "in-memory (TODO: migrer vers Redis)"
    }

    db_status = "connected" if rates_collection is not None else "offline"
    if rates_collection is not None:
        try:
            # Compter le nombre de taux archivés
            total_rates = rates_collection.count_documents({})
            cache_stats["archived_rates"] = total_rates
        except:
            pass

    return {
        "system": "SarfX Core AI Engine",
        "version": "2.0.0",
        "status": "operational",
        "database": db_status,
        "cache": cache_stats,
        "features": {
            "ml_models": ["ARIMA", "Prophet"],
            "rate_sources": ["Frankfurter", "Yahoo Finance"],
            "arbitrage": True,
            "real_time_cache": True
        },
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/smart-rate/{base}/{target}")
def smart_rate_endpoint(base: str, target: str, amount: float = 1000, background_tasks: BackgroundTasks = None):
    try:
        # 1. Calcul Arbitrage
        arb = calculate_best_execution(base, target, amount)

        # 2. Analyse IA (Timing)
        signal = generate_ai_signal(f"{base}{target}")

        # 3. Archivage asynchrone
        if background_tasks:
            background_tasks.add_task(archive_rate, base, target, arb['rates']['sarfx'], "sarfx_engine")

        return {
            "meta": {
                "pair": f"{base}/{target}",
                "timestamp": datetime.utcnow().isoformat()
            },
            "sarfx_offer": {
                "rate": round(arb['rates']['sarfx'], 4),
                "final_amount": round(amount * arb['rates']['sarfx'], 2),
                "fees": "Inclus (0.5%)"
            },
            "market_intelligence": {
                "bank_rate": round(arb['rates']['bank'], 4),
                "market_rate": round(arb['rates']['market'], 4),
                "best_liquidity_source": arb['best_source'],
                "savings": round(arb['savings'], 2)
            },
            "ai_advisor": {
                "signal": signal,
                "confidence": "Haut" if signal != "NEUTRE" else "Moyen"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/predict/{pair}")
def predict_endpoint(pair: str):
    """
    Endpoint de prédiction ML avec ARIMA + Prophet

    Retourne les prédictions pour les 7 prochains jours avec:
    - ARIMA: Modèle classique statistique
    - Prophet: Modèle moderne de Meta/Facebook
    - Ensemble: Moyenne des deux pour plus de robustesse

    TODO: Ajouter:
    - LSTM (Deep Learning) pour captures patterns complexes
    - XGBoost avec features engineering (volumes, volatilité, etc.)
    - Intervalles de confiance (95%) pour chaque prédiction
    - Backtesting automatique pour validation
    """
    try:
        # Télécharger l'historique (1 an pour meilleur entraînement)
        ticker = pair if "=" in pair else f"{pair}=X"
        logging.info(f"📊 Téléchargement données pour {ticker}...")
        df = yf.download(ticker, period="1y", interval="1d", progress=False)

        if df.empty:
            raise HTTPException(status_code=404, detail=f"Aucune donnée disponible pour {pair}")

        current = df['Close'].iloc[-1]
        logging.info(f"✓ Taux actuel {pair}: {current:.4f}")

        # Entraîner les modèles
        logging.info("🤖 Entraînement ARIMA...")
        arima_model = train_arima_model(df)

        logging.info("🤖 Entraînement Prophet...")
        prophet_model = train_prophet_model(df)

        # Prédictions
        steps = 7
        dates = [(df.index[-1] + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(1, steps + 1)]

        # ARIMA
        arima_predictions = None
        if arima_model:
            arima_predictions = predict_with_arima(arima_model, steps)
            logging.info(f"✓ Prédictions ARIMA générées: {len(arima_predictions)} jours")

        # Prophet
        prophet_predictions = None
        if prophet_model:
            prophet_predictions = predict_with_prophet(prophet_model, steps)
            logging.info(f"✓ Prédictions Prophet générées: {len(prophet_predictions)} jours")

        # Ensemble (moyenne des deux modèles)
        ensemble_predictions = []
        if arima_predictions and prophet_predictions:
            ensemble_predictions = [
                (a + p) / 2 for a, p in zip(arima_predictions, prophet_predictions)
            ]
            logging.info("✓ Ensemble créé (moyenne ARIMA + Prophet)")
        elif arima_predictions:
            ensemble_predictions = arima_predictions
            logging.warning("Prophet échec, utilisation ARIMA seul")
        elif prophet_predictions:
            ensemble_predictions = prophet_predictions
            logging.warning("ARIMA échec, utilisation Prophet seul")
        else:
            # Fallback: prédiction naïve (tendance linéaire simple)
            logging.warning("Tous les modèles ont échoué, fallback sur tendance linéaire")
            ensemble_predictions = np.linspace(current, current * 1.01, steps).tolist()

        # Historique récent (30 derniers jours)
        history = df.tail(30).reset_index()
        history_data = [
            {
                'Date': row['Date'].strftime('%Y-%m-%d'),
                'Close': float(row['Close'])
            }
            for _, row in history.iterrows()
        ]

        return {
            "meta": {
                "pair": pair,
                "current_rate": float(current),
                "prediction_days": steps,
                "models_used": ["ARIMA", "Prophet"],
                "timestamp": datetime.utcnow().isoformat()
            },
            "predictions": {
                "dates": dates,
                "Ensemble_Mean": ensemble_predictions,
                "ARIMA": arima_predictions if arima_predictions else ensemble_predictions,
                "Prophet": prophet_predictions if prophet_predictions else ensemble_predictions
            },
            "history": history_data,
            "confidence": "High" if (arima_predictions and prophet_predictions) else "Medium"
        }
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Erreur prédiction pour {pair}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/cache/clear")
def clear_cache():
    """
    Endpoint pour vider le cache manuellement

    Utile pour:
    - Forcer le rafraîchissement des taux
    - Debug/troubleshooting
    - Maintenance

    TODO: Ajouter authentification (API key) pour sécuriser cet endpoint
    """
    global RATE_CACHE
    old_size = len(RATE_CACHE)
    RATE_CACHE = {}
    logging.info(f"🧹 Cache vidé: {old_size} entrées supprimées")
    return {
        "success": True,
        "message": f"Cache cleared ({old_size} entries removed)",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/cache/stats")
def cache_statistics():
    """
    Statistiques détaillées du cache

    TODO: Ajouter métriques:
    - Hit rate (% de requêtes servies par cache)
    - Temps moyen de réponse (cache vs API)
    - Taux de rafraîchissement
    """
    stats = []
    for key, data in RATE_CACHE.items():
        age = (datetime.utcnow() - data['timestamp']).total_seconds()
        stats.append({
            "key": key,
            "rate": data['rate'],
            "age_seconds": round(age, 2),
            "expires_in": round(CACHE_TTL - age, 2) if age < CACHE_TTL else 0,
            "is_valid": age < CACHE_TTL
        })

    return {
        "total_entries": len(RATE_CACHE),
        "ttl_seconds": CACHE_TTL,
        "entries": stats,
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", AI_PORT))
    logging.info(f"🚀 [SarfX AI Backend] Démarrage sur le port {port}...")
    logging.info(f"📊 Modèles ML disponibles: ARIMA, Prophet")
    logging.info(f"💾 Base de données: {'✓ Connectée' if db is not None else '✗ Hors ligne'}")
    logging.info(f"⚡ Cache en mémoire activé (TTL: {CACHE_TTL}s)")
    print(f"\n{'='*60}")
    print(f"  SarfX AI Backend v2.0 - Ready!")
    print(f"  Swagger Docs: http://localhost:{port}/docs")
    print(f"{'='*60}\n")
    uvicorn.run(app, host="0.0.0.0", port=port)