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

# --- CONFIGURATION (PROD) ---
warnings.filterwarnings("ignore")

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

def fetch_fiat_rate(base, target):
    """Source 1 : Marché Interbancaire (Frankfurter/Yahoo)"""
    try:
        # Priorité API Rapide
        url = f"https://api.frankfurter.app/latest?from={base}&to={target}"
        resp = requests.get(url, timeout=2)
        if resp.status_code == 200:
            return resp.json()['rates'][target]
    except:
        pass
    
    # Fallback Yahoo Finance (Plus lent mais robuste)
    try:
        ticker = f"{base}{target}=X"
        df = yf.download(ticker, period="1d", interval="1m", progress=False)
        if not df.empty:
            return df['Close'].iloc[-1]
    except:
        pass
        
    return 0.0 # Echec

def fetch_crypto_implied_rate(base, target):
    """Source 2 : Marché Crypto (USDT Implied Rate)"""
    # Dans un cas réel, on appellerait Binance P2P ou CoinAPI
    # Ici, on simule la prime de risque (Spread USDT souvent positif au Maroc)
    
    fiat_rate = fetch_fiat_rate(base, target)
    if fiat_rate == 0: return 0.0
    
    # Simulation d'une prime de marché crypto (ex: +1.5% vs officiel)
    crypto_premium = 1.015 
    return fiat_rate * crypto_premium

# --- COUCHE DE TRAITEMENT (PROCESS LAYER) ---

def calculate_best_execution(base, target, amount):
    """Cœur de l'Arbitrage : Trouve le meilleur chemin pour l'argent"""
    
    # 1. Acquisition
    rate_fiat = fetch_fiat_rate(base, target)
    rate_crypto = fetch_crypto_implied_rate(base, target)
    rate_bank = rate_fiat * 0.975 # Les banques prennent ~2.5% de marge
    
    # 2. Arbitrage
    best_source_rate = max(rate_fiat, rate_crypto)
    source_name = "Marché Crypto (USDT)" if rate_crypto > rate_fiat else "Marché Interbancaire"
    
    # 3. Marge SarfX (Dynamique)
    sarfx_margin = 0.005 # 0.5% (Très compétitif)
    sarfx_rate = best_source_rate * (1 - sarfx_margin)
    
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

def generate_ai_signal(pair):
    """Analyse la tendance pour donner un conseil (Timing)"""
    # Récupération historique court terme pour tendance immédiate
    ticker = f"{pair}=X"
    try:
        df = yf.download(ticker, period="1mo", interval="1d", progress=False)
        if df.empty: return "NEUTRE"
        
        # Analyse simple : Moyenne Mobile Exponentielle (EMA)
        short_window = 5
        df['EMA'] = df['Close'].ewm(span=short_window, adjust=False).mean()
        
        last_close = df['Close'].iloc[-1]
        last_ema = df['EMA'].iloc[-1]
        
        # Logique de signal
        if last_close < last_ema * 0.995: # Prix significativement sous la moyenne -> Potentiel rebond
            return "ACHETER (Taux bas)"
        elif last_close > last_ema * 1.005: # Prix haut -> Attendre correction
            return "ATTENDRE (Taux haut)"
        else:
            return "NEUTRE"
    except:
        return "INDISPONIBLE"

# --- TÂCHES DE FOND (BACKGROUND) ---

def archive_rate(base, target, rate, source):
    """Historisation dans MongoDB pour l'apprentissage futur"""
    if rates_collection is None: return
    try:
        rates_collection.insert_one({
            "pair": f"{base}/{target}",
            "rate": float(rate),
            "source": source,
            "timestamp": datetime.utcnow()
        })
    except Exception as e:
        print(f"Erreur Archivage: {e}")

# --- API ENDPOINTS ---

@app.get("/")
def health():
    return {"system": "SarfX Core", "status": "operational", "db": "connected" if rates_collection is not None else "offline"}

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
    # Endpoint Graphique (inchangé pour la compatibilité avec le frontend existant)
    # Dans une V2, on brancherait ça sur les prédictions stockées dans MongoDB
    try:
        # ... (Logique ARIMA/Prophet/LSTM standard ici)
        # Pour simplifier ce fichier, je garde la logique YFinance directe
        df = yf.download(pair if "=" in pair else f"{pair}=X", period="1y", interval="1d", progress=False)
        current = df['Close'].iloc[-1]
        
        # Simulation Prédiction (pour l'exemple, remplacez par vos modèles lourds si serveur puissant)
        dates = [(df.index[-1] + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(1, 8)]
        trend = np.linspace(current, current * 1.01, 7) # Simulation légère hausse
        
        return {
            "pair": pair,
            "current_rate": float(current),
            "dates": dates,
            "predictions": {
                "Ensemble_Mean": trend.tolist(),
                "ARIMA": (trend * 0.998).tolist(),
                "Prophet": (trend * 1.002).tolist(),
                "LSTM": trend.tolist()
            },
            "history": df.tail(30).reset_index()[['Date', 'Close']].to_dict(orient='records')
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", AI_PORT))
    print(f"🚀 [SarfX AI] Démarrage sur le port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)