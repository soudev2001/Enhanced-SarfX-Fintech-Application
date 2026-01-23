from flask import Blueprint, jsonify, request, session
from functools import wraps
from app.services.db_service import get_db
from datetime import datetime
import uuid

api_bp = Blueprint('api', __name__)

def login_required_api(f):
    """Décorateur pour protéger les routes API"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"error": "Non authentifié"}), 401
        return f(*args, **kwargs)
    return decorated_function


# ==================== RATES ====================

@api_bp.route('/rates')
def get_rates():
    """Récupère les taux de change en temps réel"""
    db = get_db()
    if db is None:
        return jsonify({"error": "Database unavailable"}), 500
    
    suppliers = list(db.suppliers.find({"is_active": True}))
    rates = []
    for s in suppliers:
        rates.append({
            "id": str(s['_id']),
            "name": s['name'],
            "type": s.get('type', 'bank'),
            "rate": s.get('rate', 10.0),
            "fee": s.get('fee', 0),
            "logo": s.get('logo', '')
        })
    
    return jsonify({
        "rates": rates,
        "timestamp": datetime.utcnow().isoformat()
    })


@api_bp.route('/suppliers')
def get_suppliers():
    """Récupère la liste des fournisseurs"""
    db = get_db()
    if db is None:
        return jsonify({"error": "Database unavailable"}), 500
    
    suppliers = list(db.suppliers.find({"is_active": True}))
    result = []
    for s in suppliers:
        result.append({
            "id": str(s['_id']),
            "name": s['name'],
            "type": s.get('type', 'bank'),
            "rate": s.get('rate', 10.0),
            "fee": s.get('fee', 0),
            "logo": s.get('logo', ''),
            "is_active": s.get('is_active', True)
        })
    
    return jsonify(result)


# ==================== EXCHANGE ====================

@api_bp.route('/exchange', methods=['POST'])
@login_required_api
def create_exchange():
    """Crée une nouvelle transaction d'échange"""
    db = get_db()
    if db is None:
        return jsonify({"error": "Database unavailable"}), 500
    
    data = request.form if request.form else request.json
    
    # Validation
    required_fields = ['amount', 'from_currency', 'to_currency', 'rate', 'final_amount']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Champ manquant: {field}"}), 400
    
    try:
        amount = float(data['amount'])
        rate = float(data['rate'])
        final_amount = float(data['final_amount'])
    except ValueError:
        return jsonify({"error": "Valeurs numériques invalides"}), 400
    
    # Créer la transaction
    transaction = {
        "transaction_id": str(uuid.uuid4()),
        "user_id": session['user_id'],
        "type": "send",
        "amount": amount,
        "from_currency": data['from_currency'],
        "to_currency": data['to_currency'],
        "rate": rate,
        "final_amount": final_amount,
        "fee": amount * 0.01,  # 1% fee
        "supplier_id": data.get('supplier_id'),
        "recipient_name": data.get('recipient_name', ''),
        "recipient_account": data.get('recipient_account', ''),
        "status": "completed",
        "created_at": datetime.utcnow()
    }
    
    result = db.transactions.insert_one(transaction)
    
    # Log history
    from app.services.db_service import log_history
    log_history("EXCHANGE", f"Échange de {amount} {data['from_currency']} vers {final_amount} {data['to_currency']}", 
                user=session.get('email', 'Unknown'))
    
    # Redirect or return JSON based on request type
    if request.form:
        from flask import redirect, url_for, flash
        flash(f"Échange réussi! {final_amount:.2f} {data['to_currency']} envoyés.", "success")
        return redirect(url_for('app.profile'))
    
    return jsonify({
        "success": True,
        "transaction_id": transaction['transaction_id'],
        "message": f"Échange réussi: {final_amount:.2f} {data['to_currency']}"
    })


# ==================== WALLET ====================

@api_bp.route('/wallet', methods=['POST'])
@login_required_api
def create_wallet():
    """Crée un nouveau portefeuille pour l'utilisateur"""
    db = get_db()
    if db is None:
        return jsonify({"error": "Database unavailable"}), 500
    
    # Vérifier si l'utilisateur a déjà un wallet
    existing = db.wallets.find_one({"user_id": session['user_id']})
    if existing:
        if request.form:
            from flask import redirect, url_for, flash
            flash("Vous avez déjà un portefeuille", "error")
            return redirect(url_for('app.profile'))
        return jsonify({"error": "Wallet already exists"}), 400
    
    wallet = {
        "wallet_id": str(uuid.uuid4()),
        "user_id": session['user_id'],
        "balances": {
            "USD": 0.0,
            "EUR": 0.0,
            "MAD": 0.0,
            "GBP": 0.0
        },
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    db.wallets.insert_one(wallet)
    
    from app.services.db_service import log_history
    log_history("WALLET_CREATE", f"Nouveau portefeuille créé: {wallet['wallet_id']}", 
                user=session.get('email', 'Unknown'))
    
    if request.form:
        from flask import redirect, url_for, flash
        flash("Portefeuille créé avec succès!", "success")
        return redirect(url_for('app.profile'))
    
    return jsonify({
        "success": True,
        "wallet_id": wallet['wallet_id']
    })


@api_bp.route('/wallet/balance')
@login_required_api
def get_wallet_balance():
    """Récupère le solde du portefeuille"""
    db = get_db()
    if db is None:
        return jsonify({"error": "Database unavailable"}), 500
    
    wallet = db.wallets.find_one({"user_id": session['user_id']})
    if not wallet:
        return jsonify({"error": "Wallet not found"}), 404
    
    return jsonify({
        "wallet_id": wallet['wallet_id'],
        "balances": wallet['balances']
    })


# ==================== THEME ====================

@api_bp.route('/theme', methods=['POST'])
def set_theme():
    """Enregistre la préférence de thème"""
    data = request.json
    theme = data.get('theme', 'dark')
    
    session['theme'] = theme
    
    # Si l'utilisateur est connecté, sauvegarder dans la DB
    if 'user_id' in session:
        db = get_db()
        if db:
            from bson import ObjectId
            db.users.update_one(
                {"_id": ObjectId(session['user_id'])},
                {"$set": {"theme": theme}}
            )
    
    return jsonify({"success": True, "theme": theme})


# ==================== SETTINGS ====================

@api_bp.route('/settings', methods=['POST'])
@login_required_api
def save_settings():
    """Sauvegarde les paramètres de l'application (admin only)"""
    db = get_db()
    if db is None:
        return jsonify({"error": "Database unavailable"}), 500
    
    # Vérifier si admin
    from bson import ObjectId
    user = db.users.find_one({"_id": ObjectId(session['user_id'])})
    if not user or user.get('role') != 'admin':
        if request.form:
            from flask import redirect, url_for, flash
            flash("Accès non autorisé", "error")
            return redirect(url_for('app.settings'))
        return jsonify({"error": "Unauthorized"}), 403
    
    data = request.form if request.form else request.json
    
    # Mise à jour des paramètres
    settings_update = {
        "type": "app",
        "ai_backend_url": data.get('ai_backend_url', ''),
        "updated_at": datetime.utcnow(),
        "updated_by": session['user_id']
    }
    
    db.settings.update_one(
        {"type": "app"},
        {"$set": settings_update},
        upsert=True
    )
    
    from app.services.db_service import log_history
    log_history("SETTINGS_UPDATE", "Paramètres mis à jour", user=session.get('email', 'Unknown'))
    
    if request.form:
        from flask import redirect, url_for, flash
        flash("Paramètres sauvegardés!", "success")
        return redirect(url_for('app.settings'))
    
    return jsonify({"success": True})


# ==================== FORECAST (Proxy) ====================

@api_bp.route('/forecast/<pair>')
def get_forecast(pair):
    """Proxy vers le backend IA pour les prévisions - utilise le service ai_service avec fallback"""
    from app.services.ai_service import fetch_prediction
    
    result = fetch_prediction(pair)
    return jsonify(result)


# ==================== EXCHANGE RATES (Multi-Source) ====================

@api_bp.route('/rates/live')
def get_live_rate():
    """
    Get live exchange rate between two currencies.
    Query params: from (base currency), to (quote currency)
    Returns rate with 4 decimals precision.
    """
    from app.services.exchange_service import get_live_rate as fetch_live_rate
    
    base = request.args.get('from', 'EUR').upper()
    quote = request.args.get('to', 'USD').upper()
    use_cache = request.args.get('cache', 'true').lower() == 'true'
    
    result = fetch_live_rate(base, quote, use_cache=use_cache)
    return jsonify(result)


@api_bp.route('/rates/all')
def get_all_rates():
    """
    Get all exchange rates from a base currency.
    Query params: base (default EUR)
    """
    from app.services.exchange_service import get_all_rates as fetch_all_rates
    
    base = request.args.get('base', 'EUR').upper()
    result = fetch_all_rates(base)
    return jsonify(result)


@api_bp.route('/convert')
def convert_currency():
    """
    Convert amount between currencies.
    Query params: amount, from, to
    Returns result with 4 decimals.
    """
    from app.services.exchange_service import convert_currency as do_convert
    
    try:
        amount = float(request.args.get('amount', 1))
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid amount'}), 400
    
    from_currency = request.args.get('from', 'EUR').upper()
    to_currency = request.args.get('to', 'USD').upper()
    
    result = do_convert(amount, from_currency, to_currency)
    return jsonify(result)


@api_bp.route('/rates/history/<base>/<quote>')
def get_rate_history(base, quote):
    """
    Get historical rates for a currency pair.
    Query params: days (default 30)
    Data stored in MongoDB for analytics.
    """
    from app.services.exchange_service import get_rate_history as fetch_history
    
    try:
        days = int(request.args.get('days', 30))
        days = min(days, 365)  # Max 1 year
    except ValueError:
        days = 30
    
    result = fetch_history(base.upper(), quote.upper(), days)
    return jsonify(result)


@api_bp.route('/rates/analytics/<base>/<quote>')
def get_rate_analytics(base, quote):
    """
    Get analytics summary for a currency pair from MongoDB stored data.
    Query params: days (default 30)
    """
    from app.services.exchange_service import get_analytics_summary
    
    try:
        days = int(request.args.get('days', 30))
    except ValueError:
        days = 30
    
    result = get_analytics_summary(base.upper(), quote.upper(), days)
    return jsonify(result)


@api_bp.route('/currencies')
def get_currencies():
    """Get list of supported currencies with metadata"""
    from app.services.exchange_service import get_supported_currencies
    
    result = get_supported_currencies()
    return jsonify(result)


# ==================== ATM & BANKS ====================

@api_bp.route('/banks')
def get_banks():
    """Récupère la liste de toutes les banques partenaires avec le nombre d'ATM"""
    try:
        db = get_db()
        if db is None:
            return jsonify({"error": "Database unavailable"}), 500
        
        # Récupérer toutes les banques actives depuis la collection banks
        banks_data = list(db.banks.find({"is_active": True}))
        
        banks = []
        for bank in banks_data:
            # Compter les ATM pour cette banque
            atm_count = db.atm_locations.count_documents({"bank_code": bank['code']})
            
            banks.append({
                "code": bank['code'],
                "name": bank['name'],
                "logo": bank.get('logo', ''),
                "website": bank.get('website', ''),
                "description": bank.get('description', ''),
                "atm_count": atm_count
            })
        
        return jsonify({
            "success": True,
            "banks": banks,
            "total": len(banks)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route('/banks/<bank_code>')
def get_bank_details(bank_code):
    """Récupère les détails d'une banque spécifique"""
    try:
        from app.services.atm_service import ATMService
        db = get_db()
        if db is None:
            return jsonify({"error": "Database unavailable"}), 500
        
        atm_service = ATMService(db)
        bank = atm_service.get_bank_by_code(bank_code)
        
        if not bank:
            return jsonify({"success": False, "error": "Banque non trouvée"}), 404
        
        return jsonify({
            "success": True,
            "bank": bank
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route('/atms')
def get_atms():
    """
    Récupère les ATM avec filtres optionnels
    Query params: bank_code, city, limit
    """
    try:
        from app.services.atm_service import ATMService
        db = get_db()
        if db is None:
            return jsonify({"error": "Database unavailable"}), 500
        
        atm_service = ATMService(db)
        
        bank_code = request.args.get('bank_code')
        city = request.args.get('city')
        limit = int(request.args.get('limit', 50))
        
        if city:
            atms = atm_service.get_atms_by_city(city, bank_code)
        elif bank_code:
            atms = atm_service.get_atms_by_bank(bank_code, limit)
        else:
            # Retourner tous les ATM (limité)
            atms = list(db.atm_locations.find({"status": "active"}, {"_id": 0}).limit(limit))
        
        return jsonify({
            "success": True,
            "atms": atms,
            "total": len(atms)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route('/atms/nearest', methods=['POST'])
def get_nearest_atms():
    """
    Trouve les ATM les plus proches d'une position GPS
    Body: { "latitude": float, "longitude": float, "bank_code": str (optional), "max_distance_km": int (optional), "limit": int (optional) }
    """
    try:
        from app.services.atm_service import ATMService
        db = get_db()
        if db is None:
            return jsonify({"error": "Database unavailable"}), 500
        
        data = request.get_json()
        
        if not data or 'latitude' not in data or 'longitude' not in data:
            return jsonify({
                "success": False,
                "error": "Latitude et longitude requis"
            }), 400
        
        latitude = float(data['latitude'])
        longitude = float(data['longitude'])
        bank_code = data.get('bank_code')
        max_distance_km = int(data.get('max_distance_km', 10))
        limit = int(data.get('limit', 10))
        
        atm_service = ATMService(db)
        atms = atm_service.get_nearest_atms(
            latitude, longitude, bank_code, max_distance_km, limit
        )
        
        return jsonify({
            "success": True,
            "atms": atms,
            "total": len(atms),
            "user_location": {
                "latitude": latitude,
                "longitude": longitude
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route('/atms/search')
def search_atms():
    """
    Recherche d'ATM par terme de recherche
    Query params: q (search term), bank_code (optional)
    """
    try:
        from app.services.atm_service import ATMService
        db = get_db()
        if db is None:
            return jsonify({"error": "Database unavailable"}), 500
        
        search_term = request.args.get('q', '')
        bank_code = request.args.get('bank_code')
        
        if not search_term:
            return jsonify({
                "success": False,
                "error": "Terme de recherche requis"
            }), 400
        
        atm_service = ATMService(db)
        atms = atm_service.search_atms(search_term, bank_code)
        
        return jsonify({
            "success": True,
            "atms": atms,
            "total": len(atms),
            "search_term": search_term
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route('/atms/<atm_id>')
def get_atm_details(atm_id):
    """Récupère les détails d'un ATM spécifique"""
    try:
        from app.services.atm_service import ATMService
        db = get_db()
        if db is None:
            return jsonify({"error": "Database unavailable"}), 500
        
        atm_service = ATMService(db)
        atm = atm_service.get_atm_by_id(atm_id)
        
        if not atm:
            return jsonify({"success": False, "error": "ATM non trouvé"}), 404
        
        return jsonify({
            "success": True,
            "atm": atm
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route('/cities')
def get_cities():
    """Récupère la liste des villes avec des ATM"""
    try:
        from app.services.atm_service import ATMService
        db = get_db()
        if db is None:
            return jsonify({"error": "Database unavailable"}), 500
        
        bank_code = request.args.get('bank_code')
        
        atm_service = ATMService(db)
        cities = atm_service.get_cities_with_atms(bank_code)
        
        return jsonify({
            "success": True,
            "cities": cities,
            "total": len(cities)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
