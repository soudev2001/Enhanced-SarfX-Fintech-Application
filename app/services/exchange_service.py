"""
Exchange Rate Service - Multi-Source Fiat Currency Rates
Sources (toutes gratuites):
1. Frankfurter API (BCE) - Principal, illimité
2. ExchangeRate-API - Backup, 1500 req/mois gratuit
3. Open Exchange Rates (historique simulé via Frankfurter)

Fonctionnalités:
- Taux en temps réel avec fallback automatique
- Conversion de devises
- Historique stocké en MongoDB pour analytics
- Cache intelligent (1-5 min selon source)
"""

import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pymongo import MongoClient, DESCENDING
from pymongo.errors import PyMongoError
import os

logger = logging.getLogger(__name__)

# ============================================================
# CONFIGURATION DES SOURCES API (GRATUITES)
# ============================================================

API_SOURCES = {
    'frankfurter': {
        'name': 'Frankfurter (BCE)',
        'base_url': 'https://api.frankfurter.app',
        'requires_key': False,
        'rate_limit': 'unlimited',
        'priority': 1,
        'supports_history': True
    },
    'exchangerate': {
        'name': 'ExchangeRate-API',
        'base_url': 'https://open.er-api.com/v6',
        'requires_key': False,
        'rate_limit': '1500/month',
        'priority': 2,
        'supports_history': False
    },
    'fixer_free': {
        'name': 'Fixer (Free)',
        'base_url': 'http://data.fixer.io/api',
        'requires_key': True,
        'rate_limit': '100/month',
        'priority': 3,
        'supports_history': True
    }
}

# Devises supportées (fiat principales)
SUPPORTED_CURRENCIES = [
    'EUR', 'USD', 'MAD', 'GBP', 'CHF', 'CAD', 'AUD', 'JPY', 
    'CNY', 'INR', 'SAR', 'AED', 'TRY', 'EGP', 'TND', 'DZD'
]

# Paires populaires pour SarfX
POPULAR_PAIRS = [
    ('EUR', 'USD'), ('USD', 'MAD'), ('EUR', 'MAD'), ('GBP', 'USD'),
    ('GBP', 'MAD'), ('CHF', 'MAD'), ('CAD', 'MAD'), ('AED', 'MAD'),
    ('SAR', 'MAD'), ('EUR', 'GBP'), ('USD', 'JPY'), ('EUR', 'CHF')
]

# ============================================================
# MONGODB CONNECTION
# ============================================================

def get_db():
    """Get MongoDB database connection"""
    try:
        mongo_uri = os.environ.get('MONGO_URI')
        if not mongo_uri:
            from app.config import Config
            mongo_uri = Config.MONGO_URI
        
        if not mongo_uri:
            logger.error("MONGO_URI not configured")
            return None
            
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        return client['SarfX_Enhanced']
    except Exception as e:
        logger.error(f"MongoDB connection error: {e}")
        return None

# ============================================================
# CACHE MANAGEMENT
# ============================================================

def get_cached_rate(base: str, quote: str, max_age_minutes: int = 5) -> Optional[Dict]:
    """Get cached exchange rate from MongoDB"""
    db = get_db()
    if db is None:
        return None
    
    try:
        cache = db['exchange_rates_cache']
        cutoff = datetime.utcnow() - timedelta(minutes=max_age_minutes)
        
        cached = cache.find_one({
            'base': base.upper(),
            'quote': quote.upper(),
            'timestamp': {'$gte': cutoff}
        }, sort=[('timestamp', DESCENDING)])
        
        if cached:
            logger.info(f"Cache hit for {base}/{quote}")
            return {
                'rate': cached['rate'],
                'source': cached['source'],
                'timestamp': cached['timestamp'].isoformat(),
                'cached': True
            }
        return None
    except PyMongoError as e:
        logger.error(f"Cache read error: {e}")
        return None

def cache_rate(base: str, quote: str, rate: float, source: str):
    """Cache exchange rate in MongoDB"""
    db = get_db()
    if db is None:
        return
    
    try:
        cache = db['exchange_rates_cache']
        cache.update_one(
            {'base': base.upper(), 'quote': quote.upper()},
            {
                '$set': {
                    'rate': rate,
                    'source': source,
                    'timestamp': datetime.utcnow()
                }
            },
            upsert=True
        )
        logger.info(f"Cached rate {base}/{quote} = {rate} from {source}")
    except PyMongoError as e:
        logger.error(f"Cache write error: {e}")

def store_rate_history(base: str, quote: str, rate: float, source: str):
    """Store rate in history collection for analytics"""
    db = get_db()
    if db is None:
        return
    
    try:
        history = db['exchange_rates_history']
        history.insert_one({
            'base': base.upper(),
            'quote': quote.upper(),
            'rate': rate,
            'source': source,
            'timestamp': datetime.utcnow(),
            'date': datetime.utcnow().strftime('%Y-%m-%d')
        })
        
        # Create index for efficient queries
        history.create_index([
            ('base', 1), ('quote', 1), ('timestamp', -1)
        ])
        history.create_index([('date', 1)])
        
    except PyMongoError as e:
        logger.error(f"History store error: {e}")

# ============================================================
# API FETCHERS
# ============================================================

def fetch_from_frankfurter(base: str, quote: str) -> Optional[Tuple[float, str]]:
    """Fetch rate from Frankfurter API (BCE data, unlimited, free)"""
    try:
        url = f"https://api.frankfurter.app/latest?from={base.upper()}&to={quote.upper()}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'rates' in data and quote.upper() in data['rates']:
                rate = data['rates'][quote.upper()]
                return (rate, 'Frankfurter (BCE)')
        
        logger.warning(f"Frankfurter API returned {response.status_code}")
        return None
    except Exception as e:
        logger.warning(f"Frankfurter API error: {e}")
        return None

def fetch_from_exchangerate_api(base: str, quote: str) -> Optional[Tuple[float, str]]:
    """Fetch rate from ExchangeRate-API (free tier, 1500/month)"""
    try:
        url = f"https://open.er-api.com/v6/latest/{base.upper()}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('result') == 'success' and 'rates' in data:
                if quote.upper() in data['rates']:
                    rate = data['rates'][quote.upper()]
                    return (rate, 'ExchangeRate-API')
        
        logger.warning(f"ExchangeRate-API returned {response.status_code}")
        return None
    except Exception as e:
        logger.warning(f"ExchangeRate-API error: {e}")
        return None

def fetch_historical_frankfurter(base: str, quote: str, days: int = 30) -> Optional[List[Dict]]:
    """Fetch historical rates from Frankfurter API"""
    try:
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        url = f"https://api.frankfurter.app/{start_date}..{end_date}?from={base.upper()}&to={quote.upper()}"
        response = requests.get(url, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            if 'rates' in data:
                history = []
                for date_str, rates in sorted(data['rates'].items()):
                    if quote.upper() in rates:
                        history.append({
                            'date': date_str,
                            'rate': rates[quote.upper()],
                            'source': 'Frankfurter (BCE)'
                        })
                return history
        
        logger.warning(f"Frankfurter historical API returned {response.status_code}")
        return None
    except Exception as e:
        logger.warning(f"Frankfurter historical error: {e}")
        return None

# ============================================================
# MAIN FUNCTIONS
# ============================================================

def get_live_rate(base: str, quote: str, use_cache: bool = True) -> Dict:
    """
    Get live exchange rate with automatic fallback between sources.
    Returns rate with 4+ decimals precision.
    """
    base = base.upper()
    quote = quote.upper()
    
    # Validate currencies
    if base not in SUPPORTED_CURRENCIES or quote not in SUPPORTED_CURRENCIES:
        return {
            'success': False,
            'error': f"Currency not supported. Supported: {', '.join(SUPPORTED_CURRENCIES)}"
        }
    
    # Same currency
    if base == quote:
        return {
            'success': True,
            'base': base,
            'quote': quote,
            'rate': 1.0,
            'rate_formatted': '1.0000',
            'source': 'identity',
            'timestamp': datetime.utcnow().isoformat(),
            'cached': False
        }
    
    # Check cache first
    if use_cache:
        cached = get_cached_rate(base, quote, max_age_minutes=1)
        if cached:
            return {
                'success': True,
                'base': base,
                'quote': quote,
                'rate': cached['rate'],
                'rate_formatted': f"{cached['rate']:.4f}",
                'source': cached['source'],
                'timestamp': cached['timestamp'],
                'cached': True
            }
    
    # Try sources in priority order
    sources = [
        fetch_from_frankfurter,
        fetch_from_exchangerate_api
    ]
    
    for fetch_func in sources:
        result = fetch_func(base, quote)
        if result:
            rate, source = result
            
            # Cache and store history
            cache_rate(base, quote, rate, source)
            store_rate_history(base, quote, rate, source)
            
            return {
                'success': True,
                'base': base,
                'quote': quote,
                'rate': rate,
                'rate_formatted': f"{rate:.4f}",
                'source': source,
                'timestamp': datetime.utcnow().isoformat(),
                'cached': False
            }
    
    # All sources failed - try cache with longer TTL
    cached = get_cached_rate(base, quote, max_age_minutes=60)
    if cached:
        return {
            'success': True,
            'base': base,
            'quote': quote,
            'rate': cached['rate'],
            'rate_formatted': f"{cached['rate']:.4f}",
            'source': f"{cached['source']} (stale)",
            'timestamp': cached['timestamp'],
            'cached': True,
            'stale': True
        }
    
    return {
        'success': False,
        'error': 'All exchange rate sources unavailable',
        'base': base,
        'quote': quote
    }

def convert_currency(amount: float, from_currency: str, to_currency: str) -> Dict:
    """
    Convert amount from one currency to another.
    Returns result with 4 decimals precision.
    """
    # Validation du montant
    if amount is None or not isinstance(amount, (int, float)):
        return {'success': False, 'error': 'Invalid amount: must be a number'}
    if amount <= 0:
        return {'success': False, 'error': 'Invalid amount: must be positive'}
    
    # Validation des devises
    valid_currencies = ['USD', 'EUR', 'MAD', 'GBP', 'CAD', 'CHF', 'AED']
    if from_currency.upper() not in valid_currencies:
        return {'success': False, 'error': f'Invalid source currency: {from_currency}'}
    if to_currency.upper() not in valid_currencies:
        return {'success': False, 'error': f'Invalid target currency: {to_currency}'}
    
    rate_result = get_live_rate(from_currency, to_currency)
    
    if not rate_result.get('success'):
        return rate_result
    
    rate = rate_result['rate']
    
    # Protection contre division par zéro (rate = 0)
    if not rate or rate == 0:
        return {'success': False, 'error': 'Invalid exchange rate received'}
    
    converted = amount * rate
    
    return {
        'success': True,
        'amount': amount,
        'from': from_currency.upper(),
        'to': to_currency.upper(),
        'rate': rate,
        'rate_formatted': f"{rate:.4f}",
        'result': converted,
        'result_formatted': f"{converted:.4f}",
        'source': rate_result['source'],
        'timestamp': rate_result['timestamp'],
        'cached': rate_result.get('cached', False)
    }

def get_rate_history(base: str, quote: str, days: int = 30) -> Dict:
    """
    Get historical rates - combines API data with MongoDB stored history.
    Prioritizes API for accuracy, MongoDB for analytics continuity.
    """
    base = base.upper()
    quote = quote.upper()
    
    # Try API historical first
    api_history = fetch_historical_frankfurter(base, quote, days)
    
    if api_history and len(api_history) > 0:
        # Store in MongoDB for future analytics
        db = get_db()
        if db is not None:
            try:
                history_col = db['exchange_rates_history']
                for item in api_history:
                    history_col.update_one(
                        {
                            'base': base,
                            'quote': quote,
                            'date': item['date']
                        },
                        {
                            '$set': {
                                'rate': item['rate'],
                                'source': item['source'],
                                'timestamp': datetime.strptime(item['date'], '%Y-%m-%d')
                            }
                        },
                        upsert=True
                    )
            except Exception as e:
                logger.error(f"Error storing historical data: {e}")
        
        # Calculate stats
        rates = [h['rate'] for h in api_history]
        
        return {
            'success': True,
            'base': base,
            'quote': quote,
            'days': days,
            'data': api_history,
            'stats': {
                'min': min(rates),
                'max': max(rates),
                'avg': sum(rates) / len(rates),
                'current': rates[-1] if rates else None,
                'change': ((rates[-1] - rates[0]) / rates[0] * 100) if len(rates) > 1 else 0,
                'volatility': max(rates) - min(rates)
            },
            'source': 'Frankfurter (BCE)',
            'count': len(api_history)
        }
    
    # Fallback to MongoDB stored history
    db = get_db()
    if db is not None:
        try:
            history_col = db['exchange_rates_history']
            cutoff = datetime.utcnow() - timedelta(days=days)
            
            cursor = history_col.find({
                'base': base,
                'quote': quote,
                'timestamp': {'$gte': cutoff}
            }).sort('timestamp', 1)
            
            mongo_history = []
            for doc in cursor:
                mongo_history.append({
                    'date': doc.get('date', doc['timestamp'].strftime('%Y-%m-%d')),
                    'rate': doc['rate'],
                    'source': doc.get('source', 'MongoDB')
                })
            
            if mongo_history:
                rates = [h['rate'] for h in mongo_history]
                return {
                    'success': True,
                    'base': base,
                    'quote': quote,
                    'days': days,
                    'data': mongo_history,
                    'stats': {
                        'min': min(rates),
                        'max': max(rates),
                        'avg': sum(rates) / len(rates),
                        'current': rates[-1],
                        'change': ((rates[-1] - rates[0]) / rates[0] * 100) if len(rates) > 1 else 0,
                        'volatility': max(rates) - min(rates)
                    },
                    'source': 'MongoDB Analytics',
                    'count': len(mongo_history)
                }
        except Exception as e:
            logger.error(f"Error fetching MongoDB history: {e}")
    
    return {
        'success': False,
        'error': 'Historical data unavailable',
        'base': base,
        'quote': quote
    }

def get_all_rates(base: str = 'EUR') -> Dict:
    """Get rates for all supported currencies from a base currency"""
    base = base.upper()
    
    try:
        # Use Frankfurter for efficiency (single request)
        url = f"https://api.frankfurter.app/latest?from={base}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            rates = {}
            
            for currency in SUPPORTED_CURRENCIES:
                if currency == base:
                    rates[currency] = 1.0
                elif currency in data.get('rates', {}):
                    rates[currency] = data['rates'][currency]
            
            return {
                'success': True,
                'base': base,
                'rates': rates,
                'timestamp': datetime.utcnow().isoformat(),
                'source': 'Frankfurter (BCE)'
            }
    except Exception as e:
        logger.error(f"Error fetching all rates: {e}")
    
    return {
        'success': False,
        'error': 'Could not fetch rates'
    }

def get_analytics_summary(base: str, quote: str, days: int = 30) -> Dict:
    """Get analytics summary for a currency pair from stored MongoDB data"""
    db = get_db()
    if db is None:
        return {'success': False, 'error': 'Database unavailable'}
    
    try:
        history_col = db['exchange_rates_history']
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        # Aggregation pipeline for analytics
        pipeline = [
            {
                '$match': {
                    'base': base.upper(),
                    'quote': quote.upper(),
                    'timestamp': {'$gte': cutoff}
                }
            },
            {
                '$group': {
                    '_id': '$date',
                    'avg_rate': {'$avg': '$rate'},
                    'min_rate': {'$min': '$rate'},
                    'max_rate': {'$max': '$rate'},
                    'count': {'$sum': 1}
                }
            },
            {'$sort': {'_id': 1}}
        ]
        
        result = list(history_col.aggregate(pipeline))
        
        if result:
            daily_rates = [r['avg_rate'] for r in result]
            return {
                'success': True,
                'base': base.upper(),
                'quote': quote.upper(),
                'period_days': days,
                'data_points': len(result),
                'daily_data': result,
                'summary': {
                    'period_min': min(daily_rates),
                    'period_max': max(daily_rates),
                    'period_avg': sum(daily_rates) / len(daily_rates),
                    'trend': 'up' if daily_rates[-1] > daily_rates[0] else 'down',
                    'change_percent': ((daily_rates[-1] - daily_rates[0]) / daily_rates[0] * 100)
                }
            }
        
        return {
            'success': False,
            'error': 'No analytics data available',
            'suggestion': 'Historical data will accumulate over time'
        }
        
    except Exception as e:
        logger.error(f"Analytics error: {e}")
        return {'success': False, 'error': str(e)}

def get_supported_currencies() -> Dict:
    """Get list of supported currencies with metadata"""
    currency_info = {
        'EUR': {'name': 'Euro', 'symbol': '€', 'flag': '🇪🇺'},
        'USD': {'name': 'US Dollar', 'symbol': '$', 'flag': '🇺🇸'},
        'MAD': {'name': 'Dirham Marocain', 'symbol': 'د.م.', 'flag': '🇲🇦'},
        'GBP': {'name': 'British Pound', 'symbol': '£', 'flag': '🇬🇧'},
        'CHF': {'name': 'Swiss Franc', 'symbol': 'CHF', 'flag': '🇨🇭'},
        'CAD': {'name': 'Canadian Dollar', 'symbol': 'C$', 'flag': '🇨🇦'},
        'AUD': {'name': 'Australian Dollar', 'symbol': 'A$', 'flag': '🇦🇺'},
        'JPY': {'name': 'Japanese Yen', 'symbol': '¥', 'flag': '🇯🇵'},
        'CNY': {'name': 'Chinese Yuan', 'symbol': '¥', 'flag': '🇨🇳'},
        'INR': {'name': 'Indian Rupee', 'symbol': '₹', 'flag': '🇮🇳'},
        'SAR': {'name': 'Saudi Riyal', 'symbol': '﷼', 'flag': '🇸🇦'},
        'AED': {'name': 'UAE Dirham', 'symbol': 'د.إ', 'flag': '🇦🇪'},
        'TRY': {'name': 'Turkish Lira', 'symbol': '₺', 'flag': '🇹🇷'},
        'EGP': {'name': 'Egyptian Pound', 'symbol': 'E£', 'flag': '🇪🇬'},
        'TND': {'name': 'Tunisian Dinar', 'symbol': 'د.ت', 'flag': '🇹🇳'},
        'DZD': {'name': 'Algerian Dinar', 'symbol': 'د.ج', 'flag': '🇩🇿'}
    }
    
    return {
        'success': True,
        'currencies': [
            {
                'code': code,
                **currency_info.get(code, {'name': code, 'symbol': code, 'flag': '🏳️'})
            }
            for code in SUPPORTED_CURRENCIES
        ],
        'popular_pairs': [
            {'from': p[0], 'to': p[1], 'code': f"{p[0]}/{p[1]}"} 
            for p in POPULAR_PAIRS
        ]
    }
