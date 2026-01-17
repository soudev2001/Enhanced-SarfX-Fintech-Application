"""
Service pour l'intégration de l'IA de prévision
"""
import os
import requests
from datetime import datetime
from app.services.db_service import get_db

# URL par défaut: Cloud Run (production externe) ou localhost (si sur même serveur)
DEFAULT_AI_URL = os.environ.get(
    "AI_BACKEND_URL", 
    "http://127.0.0.1:8087"  # Backend local sur le même serveur (port 8087)
)
CLOUD_AI_URL = "https://sarfx-backend-ai-618432953337.europe-west1.run.app"  # Fallback Cloud Run


def get_ai_backend_url():
    """Récupère l'URL du backend IA depuis les paramètres"""
    db = get_db()
    if db is None:
        return DEFAULT_AI_URL
    
    settings = db.settings.find_one({"type": "app"})
    if settings:
        return settings.get('ai_backend_url', DEFAULT_AI_URL)
    return DEFAULT_AI_URL


def fetch_prediction(pair='EURUSD=X', timeout=30):
    """
    Récupère les prévisions IA pour une paire de devises
    Essaie d'abord le backend local, puis Cloud Run en fallback.
    
    Args:
        pair: Paire de devises (ex: 'EURUSD=X', 'USDMAD=X')
        timeout: Timeout en secondes
    
    Returns:
        dict avec les prévisions ou None si erreur
    """
    urls_to_try = [get_ai_backend_url(), CLOUD_AI_URL]
    
    for url in urls_to_try:
        try:
            headers = {
                'ngrok-skip-browser-warning': 'true',
                'Bypass-Tunnel-Reminder': 'true',
                'User-Agent': 'SarfX-App/1.0'
            }
            
            response = requests.get(
                f"{url}/predict/{pair}",
                headers=headers,
                timeout=timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Cache the result
                cache_prediction(pair, data)
                
                return {
                    'success': True,
                    'data': data,
                    'cached': False,
                    'timestamp': datetime.utcnow().isoformat(),
                    'source': url
                }
        except requests.exceptions.Timeout:
            continue  # Try next URL
        except requests.exceptions.ConnectionError:
            continue  # Try next URL
        except Exception:
            continue  # Try next URL
    
    # All URLs failed, try cache
    cached = get_cached_prediction(pair)
    if cached:
        return {
            'success': True,
            'data': cached['data'],
            'cached': True,
            'timestamp': cached['timestamp']
        }
    
    return {
        'success': False,
        'error': "All AI backends unavailable",
        'cached': False
    }


def cache_prediction(pair, data):
    """Cache les prévisions dans MongoDB"""
    db = get_db()
    if db is None:
        return
    
    cache_entry = {
        "pair": pair,
        "data": data,
        "timestamp": datetime.utcnow()
    }
    
    db.ai_cache.update_one(
        {"pair": pair},
        {"$set": cache_entry},
        upsert=True
    )


def get_cached_prediction(pair):
    """Récupère les prévisions en cache"""
    db = get_db()
    if db is None:
        return None
    
    cached = db.ai_cache.find_one({"pair": pair})
    if cached:
        # Vérifier si le cache n'est pas trop vieux (1 heure max)
        cache_age = (datetime.utcnow() - cached['timestamp']).total_seconds()
        if cache_age < 3600:  # 1 heure
            return cached
    return None


def analyze_prediction(prediction_data):
    """
    Analyse les données de prévision et génère des insights
    
    Args:
        prediction_data: Données brutes de l'API IA
    
    Returns:
        dict avec analyse et recommandations
    """
    if not prediction_data or 'predictions' not in prediction_data:
        return None
    
    predictions = prediction_data['predictions']
    history = prediction_data.get('history', [])
    
    # Récupérer la dernière valeur historique
    last_value = history[-1]['Close'] if history else 0
    
    # Prévisions à J+7
    ensemble_pred = predictions.get('Ensemble_Mean', [])
    j7_pred = ensemble_pred[-1] if ensemble_pred else 0
    
    # Calculer la variation
    change_pct = ((j7_pred - last_value) / last_value * 100) if last_value else 0
    
    # Générer l'analyse
    if change_pct > 2:
        trend = "bullish"
        recommendation = "Attendre avant d'acheter - le taux devrait augmenter"
        confidence = "high"
    elif change_pct > 0.5:
        trend = "slightly_bullish"
        recommendation = "Légère hausse prévue - achat possible"
        confidence = "medium"
    elif change_pct < -2:
        trend = "bearish"
        recommendation = "Bon moment pour acheter - le taux devrait baisser"
        confidence = "high"
    elif change_pct < -0.5:
        trend = "slightly_bearish"
        recommendation = "Légère baisse prévue - achat favorable"
        confidence = "medium"
    else:
        trend = "neutral"
        recommendation = "Marché stable - pas de changement significatif attendu"
        confidence = "low"
    
    # Comparer les modèles
    arima = predictions.get('ARIMA', [])[-1] if predictions.get('ARIMA') else 0
    prophet = predictions.get('Prophet', [])[-1] if predictions.get('Prophet') else 0
    lstm = predictions.get('LSTM', [])[-1] if predictions.get('LSTM') else 0
    
    model_agreement = abs(arima - prophet) < 0.01 and abs(prophet - lstm) < 0.01
    
    return {
        "current_rate": last_value,
        "predicted_rate": j7_pred,
        "change_pct": round(change_pct, 2),
        "trend": trend,
        "recommendation": recommendation,
        "confidence": confidence,
        "model_agreement": model_agreement,
        "models": {
            "arima": arima,
            "prophet": prophet,
            "lstm": lstm,
            "ensemble": j7_pred
        }
    }


def get_supported_pairs():
    """Retourne la liste des paires de devises supportées"""
    return [
        {"code": "EURUSD=X", "name": "EUR/USD", "base": "EUR", "quote": "USD"},
        {"code": "USDMAD=X", "name": "USD/MAD", "base": "USD", "quote": "MAD"},
        {"code": "EURMAD=X", "name": "EUR/MAD", "base": "EUR", "quote": "MAD"},
        {"code": "GBPUSD=X", "name": "GBP/USD", "base": "GBP", "quote": "USD"},
        {"code": "GBPMAD=X", "name": "GBP/MAD", "base": "GBP", "quote": "MAD"},
    ]
