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


# ==================== SEED DEMO USERS ====================

@api_bp.route('/seed-demo-users')
def seed_demo_users():
    """Crée les utilisateurs de démonstration"""
    from werkzeug.security import generate_password_hash
    
    db = get_db()
    if db is None:
        return jsonify({"error": "Database unavailable"}), 500
    
    demo_users = [
        {"email": "admin@sarfx.io", "password": "admin123", "name": "Admin SarfX", "role": "admin"},
        {"email": "bank@sarfx.io", "password": "bank123", "name": "Bank Manager", "role": "bank_admin"},
        {"email": "user@sarfx.io", "password": "user123", "name": "Demo User", "role": "user"}
    ]
    
    created = []
    updated = []
    
    for user_data in demo_users:
        existing = db.users.find_one({"email": user_data["email"]})
        
        if existing:
            db.users.update_one(
                {"email": user_data["email"]},
                {"$set": {
                    "password": generate_password_hash(user_data["password"]),
                    "role": user_data["role"],
                    "is_active": True,
                    "is_verified": True
                }}
            )
            updated.append(user_data["email"])
        else:
            new_user = {
                "email": user_data["email"],
                "password": generate_password_hash(user_data["password"]),
                "name": user_data["name"],
                "role": user_data["role"],
                "is_active": True,
                "is_verified": True,
                "created_at": datetime.utcnow()
            }
            result = db.users.insert_one(new_user)
            
            # Create wallet
            db.wallets.insert_one({
                "user_id": str(result.inserted_id),
                "balances": {"USD": 1000.0, "EUR": 500.0, "MAD": 5000.0},
                "created_at": datetime.utcnow()
            })
            created.append(user_data["email"])
    
    return jsonify({
        "success": True,
        "created": created,
        "updated": updated,
        "message": "Demo users seeded successfully",
        "accounts": [
            {"email": "admin@sarfx.io", "password": "admin123", "role": "admin"},
            {"email": "bank@sarfx.io", "password": "bank123", "role": "bank_admin"},
            {"email": "user@sarfx.io", "password": "user123", "role": "user"}
        ]
    })


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


# ==================== RATE HISTORY ====================

@api_bp.route('/rates/history')
def get_rate_history_chart():
    """Récupère l'historique des taux de change pour les graphiques"""
    import random
    from datetime import timedelta
    
    pair = request.args.get('pair', 'USD-MAD')
    time_range = request.args.get('range', '24h')
    
    # Déterminer le nombre de points de données
    ranges = {
        '24h': (48, 30),     # 48 points, 30 min each
        '7d': (168, 60),     # 168 points, 1 hour each
        '30d': (120, 360),   # 120 points, 6 hours each
        '90d': (90, 1440)    # 90 points, 1 day each
    }
    
    points, interval = ranges.get(time_range, (48, 30))
    
    # Base rates par paire
    base_rates = {
        'USD-MAD': 10.05,
        'EUR-MAD': 10.85,
        'GBP-MAD': 12.65,
        'USD-EUR': 0.92
    }
    
    base_rate = base_rates.get(pair, 10.0)
    
    # Générer l'historique simulé
    history = []
    now = datetime.utcnow()
    rate = base_rate
    min_rate = rate
    max_rate = rate
    first_rate = None
    
    for i in range(points, -1, -1):
        timestamp = now - timedelta(minutes=i * interval)
        # Variation aléatoire réaliste
        change = (random.random() - 0.5) * 0.03 * base_rate
        rate = max(base_rate * 0.95, min(base_rate * 1.05, rate + change))
        
        if first_rate is None:
            first_rate = rate
        
        min_rate = min(min_rate, rate)
        max_rate = max(max_rate, rate)
        
        history.append({
            'timestamp': timestamp.isoformat(),
            'rate': round(rate, 4)
        })
    
    current_rate = history[-1]['rate'] if history else base_rate
    change_pct = ((current_rate - first_rate) / first_rate * 100) if first_rate else 0
    
    return jsonify({
        'success': True,
        'pair': pair,
        'range': time_range,
        'history': history,
        'stats': {
            'current': round(current_rate, 4),
            'high': round(max_rate, 4),
            'low': round(min_rate, 4),
            'change': round(change_pct, 2)
        }
    })


@api_bp.route('/rates/best')
def get_best_rates():
    """Récupère les meilleurs taux de change"""
    db = get_db()
    amount = float(request.args.get('amount', 1000))
    
    if db is None:
        # Données mock
        return jsonify({
            'success': True,
            'rates': [
                {'supplier': 'Binance P2P', 'type': 'Crypto', 'rate': 10.12, 'fee': 0},
                {'supplier': 'Marché Parallèle', 'type': 'Cash', 'rate': 10.05, 'fee': 0},
                {'supplier': 'Western Union', 'type': 'Transfer', 'rate': 9.95, 'fee': 15},
                {'supplier': 'MoneyGram', 'type': 'Transfer', 'rate': 9.90, 'fee': 12},
                {'supplier': 'Banque Populaire', 'type': 'Bank', 'rate': 9.85, 'fee': 20}
            ]
        })
    
    suppliers = list(db.suppliers.find({"is_active": True}).sort("rate", -1))
    
    rates = []
    for s in suppliers:
        rates.append({
            'supplier': s['name'],
            'type': s.get('type', 'bank').capitalize(),
            'rate': s.get('rate', 10.0),
            'fee': s.get('fee', 0)
        })
    
    return jsonify({
        'success': True,
        'rates': rates
    })


@api_bp.route('/rates/alerts', methods=['GET', 'POST', 'DELETE'])
@login_required_api
def rate_alerts():
    """Gestion des alertes de taux"""
    db = get_db()
    user_id = session['user_id']
    
    if request.method == 'GET':
        alerts = list(db.rate_alerts.find({"user_id": user_id})) if db else []
        for a in alerts:
            a['_id'] = str(a['_id'])
        return jsonify({'success': True, 'alerts': alerts})
    
    elif request.method == 'POST':
        data = request.get_json()
        alert = {
            'user_id': user_id,
            'pair': data.get('pair', 'USD-MAD'),
            'condition': data.get('condition', 'above'),
            'target': float(data.get('target', 10.0)),
            'email_notify': data.get('email_notify', True),
            'created_at': datetime.utcnow(),
            'triggered': False
        }
        
        if db:
            result = db.rate_alerts.insert_one(alert)
            alert['_id'] = str(result.inserted_id)
        
        return jsonify({'success': True, 'alert': alert})
    
    elif request.method == 'DELETE':
        alert_id = request.args.get('id')
        if db and alert_id:
            from bson import ObjectId
            db.rate_alerts.delete_one({"_id": ObjectId(alert_id), "user_id": user_id})
        return jsonify({'success': True})


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
    try:
        data = request.json or {}
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
    except Exception as e:
        print(f"Theme error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


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


# ==================== BENEFICIARIES ====================

@api_bp.route('/beneficiaries')
@login_required_api
def get_beneficiaries():
    """Récupère les bénéficiaires de l'utilisateur connecté"""
    try:
        db = get_db()
        if db is None:
            return jsonify({"error": "Database unavailable"}), 500
        
        user_id = session.get('user_id')
        
        # Récupérer les bénéficiaires de l'utilisateur
        beneficiaries = list(db.beneficiaries.find({"user_id": str(user_id)}).sort([
            ("is_favorite", -1),
            ("transfer_count", -1),
            ("name", 1)
        ]))
        
        # Convertir ObjectId en string
        for b in beneficiaries:
            b['_id'] = str(b['_id'])
        
        return jsonify({
            "success": True,
            "beneficiaries": beneficiaries,
            "total": len(beneficiaries)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route('/beneficiaries', methods=['POST'])
@login_required_api
def create_beneficiary():
    """Crée un nouveau bénéficiaire"""
    try:
        db = get_db()
        if db is None:
            return jsonify({"error": "Database unavailable"}), 500
        
        data = request.get_json()
        user_id = session.get('user_id')
        user_email = session.get('email', '')
        
        # Validation
        required_fields = ['name', 'bank_code', 'iban']
        for field in required_fields:
            if not data.get(field):
                return jsonify({"success": False, "error": f"Champ requis: {field}"}), 400
        
        # Créer le bénéficiaire
        beneficiary = {
            "beneficiary_id": str(uuid.uuid4())[:12].upper(),
            "user_id": str(user_id),
            "user_email": user_email,
            "name": data['name'],
            "first_name": data.get('first_name', ''),
            "last_name": data.get('last_name', ''),
            "bank_code": data['bank_code'],
            "bank_name": data.get('bank_name', ''),
            "swift_code": data.get('swift_code', ''),
            "iban": data['iban'],
            "rib": data.get('rib', ''),
            "phone": data.get('phone', ''),
            "email": data.get('email', ''),
            "city": data.get('city', ''),
            "country": data.get('country', 'Maroc'),
            "currency": "MAD",
            "is_favorite": data.get('is_favorite', False),
            "is_verified": False,
            "transfer_count": 0,
            "notes": data.get('notes', ''),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = db.beneficiaries.insert_one(beneficiary)
        beneficiary['_id'] = str(result.inserted_id)
        
        return jsonify({
            "success": True,
            "message": "Bénéficiaire créé",
            "beneficiary": beneficiary
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route('/beneficiaries/<beneficiary_id>', methods=['DELETE'])
@login_required_api
def delete_beneficiary(beneficiary_id):
    """Supprime un bénéficiaire"""
    try:
        from bson import ObjectId
        db = get_db()
        if db is None:
            return jsonify({"error": "Database unavailable"}), 500
        
        user_id = session.get('user_id')
        
        # Vérifier que le bénéficiaire appartient à l'utilisateur
        result = db.beneficiaries.delete_one({
            "_id": ObjectId(beneficiary_id),
            "user_id": str(user_id)
        })
        
        if result.deleted_count == 0:
            return jsonify({"success": False, "error": "Bénéficiaire non trouvé"}), 404
        
        return jsonify({
            "success": True,
            "message": "Bénéficiaire supprimé"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route('/beneficiaries/<beneficiary_id>/favorite', methods=['POST'])
@login_required_api
def toggle_favorite_beneficiary(beneficiary_id):
    """Toggle le statut favori d'un bénéficiaire"""
    try:
        from bson import ObjectId
        db = get_db()
        if db is None:
            return jsonify({"error": "Database unavailable"}), 500
        
        user_id = session.get('user_id')
        
        # Récupérer le bénéficiaire
        beneficiary = db.beneficiaries.find_one({
            "_id": ObjectId(beneficiary_id),
            "user_id": str(user_id)
        })
        
        if not beneficiary:
            return jsonify({"success": False, "error": "Bénéficiaire non trouvé"}), 404
        
        # Toggle favorite
        new_favorite = not beneficiary.get('is_favorite', False)
        db.beneficiaries.update_one(
            {"_id": ObjectId(beneficiary_id)},
            {"$set": {"is_favorite": new_favorite, "updated_at": datetime.utcnow()}}
        )
        
        return jsonify({
            "success": True,
            "is_favorite": new_favorite
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ==================== BANK SETTINGS (for bank_respo) ====================

@api_bp.route('/bank-settings', methods=['POST'])
@login_required_api
def update_bank_settings():
    """Met à jour les paramètres API de la banque (bank_respo uniquement)"""
    try:
        from bson import ObjectId
        db = get_db()
        if db is None:
            return jsonify({"error": "Database unavailable"}), 500
        
        user_id = session.get('user_id')
        user = db.users.find_one({"_id": ObjectId(user_id)})
        
        if not user or user.get('role') != 'bank_respo':
            return jsonify({"success": False, "error": "Accès non autorisé"}), 403
        
        bank_code = user.get('bank_code')
        if not bank_code:
            return jsonify({"success": False, "error": "Aucune banque associée"}), 400
        
        data = request.json
        
        # Champs autorisés à mettre à jour
        allowed_fields = [
            'api_key', 'api_secret', 'api_base_url', 'webhook_url', 'callback_url',
            'atm_api_endpoint', 'withdrawal_limit', 'cardless_enabled',
            'exchange_rate_margin', 'rate_refresh_interval',
            'ip_whitelist', 'two_factor_required', 'ssl_verification'
        ]
        
        update_data = {k: v for k, v in data.items() if k in allowed_fields}
        update_data['updated_at'] = datetime.utcnow()
        update_data['updated_by'] = str(user_id)
        
        db.banks.update_one(
            {"code": bank_code},
            {"$set": update_data}
        )
        
        return jsonify({
            "success": True,
            "message": "Paramètres mis à jour"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route('/bank-settings/test', methods=['POST'])
@login_required_api
def test_bank_connection():
    """Teste la connexion API de la banque"""
    try:
        from bson import ObjectId
        db = get_db()
        if db is None:
            return jsonify({"error": "Database unavailable"}), 500
        
        user_id = session.get('user_id')
        user = db.users.find_one({"_id": ObjectId(user_id)})
        
        if not user or user.get('role') != 'bank_respo':
            return jsonify({"success": False, "error": "Accès non autorisé"}), 403
        
        # Simulation d'un test de connexion
        # En production, faire un vrai appel à l'API de la banque
        return jsonify({
            "success": True,
            "message": "Connexion API réussie",
            "latency": "42ms"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ==================== NOTIFICATIONS ====================

@api_bp.route('/notifications')
@login_required_api
def get_notifications():
    """Récupère les notifications de l'utilisateur"""
    db = get_db()
    user_id = session['user_id']
    
    if db is None:
        return jsonify({"success": True, "notifications": []})
    
    notifications = list(db.notifications.find(
        {"user_id": user_id}
    ).sort("created_at", -1).limit(20))
    
    for n in notifications:
        n['_id'] = str(n['_id'])
        n['id'] = n['_id']
        n['time'] = n.get('created_at', datetime.utcnow()).isoformat()
    
    return jsonify({
        "success": True,
        "notifications": notifications
    })


@api_bp.route('/notifications/<notif_id>/read', methods=['POST'])
@login_required_api
def mark_notification_read(notif_id):
    """Marque une notification comme lue"""
    db = get_db()
    user_id = session['user_id']
    
    if db:
        from bson import ObjectId
        db.notifications.update_one(
            {"_id": ObjectId(notif_id), "user_id": user_id},
            {"$set": {"read": True}}
        )
    
    return jsonify({"success": True})


@api_bp.route('/notifications/read-all', methods=['POST'])
@login_required_api
def mark_all_notifications_read():
    """Marque toutes les notifications comme lues"""
    db = get_db()
    user_id = session['user_id']
    
    if db:
        db.notifications.update_many(
            {"user_id": user_id},
            {"$set": {"read": True}}
        )
    
    return jsonify({"success": True})


@api_bp.route('/notifications/check')
@login_required_api
def check_new_notifications():
    """Vérifie s'il y a de nouvelles notifications"""
    db = get_db()
    user_id = session['user_id']
    
    if db is None:
        return jsonify({"hasNew": False})
    
    unread_count = db.notifications.count_documents({
        "user_id": user_id,
        "read": False
    })
    
    latest = None
    if unread_count > 0:
        latest_doc = db.notifications.find_one(
            {"user_id": user_id, "read": False},
            sort=[("created_at", -1)]
        )
        if latest_doc:
            latest = {
                "title": latest_doc.get('title', ''),
                "message": latest_doc.get('message', '')
            }
    
    return jsonify({
        "hasNew": unread_count > 0,
        "unreadCount": unread_count,
        "latest": latest
    })


def create_notification(user_id, notif_type, title, message):
    """Helper pour créer une notification (utilisable depuis d'autres modules)"""
    db = get_db()
    if db is None:
        return None
    
    notification = {
        "user_id": user_id,
        "type": notif_type,
        "title": title,
        "message": message,
        "read": False,
        "created_at": datetime.utcnow()
    }
    
    result = db.notifications.insert_one(notification)
    return str(result.inserted_id)


# ==================== CHATBOT ====================

@api_bp.route('/chatbot/message', methods=['POST'])
def chatbot_message():
    """Envoie un message au chatbot et reçoit une réponse"""
    try:
        from app.services.chatbot_service import chatbot_service
        
        data = request.get_json()
        message = data.get('message', '')
        
        if not message:
            return jsonify({"success": False, "error": "Message vide"}), 400
        
        # Ajouter le contexte SarfX
        context = chatbot_service.get_sarfx_context()
        
        # Générer la réponse
        result = chatbot_service.generate_response(message, context)
        
        if result['success']:
            return jsonify({
                "success": True,
                "response": result['response']
            })
        else:
            return jsonify({
                "success": False,
                "error": result.get('error', 'Erreur inconnue')
            }), 500
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route('/chatbot/suggestions', methods=['GET'])
def chatbot_suggestions():
    """Retourne les suggestions de questions pour le chatbot"""
    try:
        from app.services.chatbot_service import chatbot_service
        from bson import ObjectId
        
        db = get_db()
        user = None
        
        if 'user_id' in session and db:
            user = db.users.find_one({"_id": ObjectId(session['user_id'])})
        
        suggestions = chatbot_service.get_suggestions(db, user)
        
        return jsonify({
            "success": True,
            "suggestions": suggestions
        })
    except Exception as e:
        return jsonify({
            "success": True,
            "suggestions": [
                "Quels sont les taux de change actuels ?",
                "Comment créer un wallet ?",
                "Où trouver un ATM près de moi ?"
            ]
        })


# ==================== ATMS ====================

@api_bp.route('/atms', methods=['GET', 'POST'])
@login_required_api
def manage_atms():
    """Gestion des ATMs (liste et ajout)"""
    db = get_db()
    if db is None:
        return jsonify({"error": "Database unavailable"}), 500
    
    if request.method == 'GET':
        # Liste des ATMs
        from bson import ObjectId
        user_id = session.get('user_id')
        user = db.users.find_one({"_id": ObjectId(user_id)})
        
        # Filtrer par banque si l'utilisateur est associé à une banque
        query = {}
        if user.get('bank_code') and user.get('role') in ['admin_associate_bank', 'bank_user']:
            query['bank_code'] = user['bank_code']
        
        atms = list(db.atms.find(query)) if 'atms' in db.list_collection_names() else []
        for atm in atms:
            atm['_id'] = str(atm['_id'])
        
        return jsonify({"success": True, "atms": atms})
    
    elif request.method == 'POST':
        # Ajouter un ATM
        from bson import ObjectId
        user_id = session.get('user_id')
        user = db.users.find_one({"_id": ObjectId(user_id)})
        
        if user.get('role') not in ['admin', 'admin_sr_bank', 'admin_associate_bank']:
            return jsonify({"success": False, "error": "Non autorisé"}), 403
        
        data = request.get_json()
        atm_data = {
            'name': data.get('name'),
            'address': data.get('address'),
            'city': data.get('city'),
            'latitude': float(data.get('latitude')) if data.get('latitude') else None,
            'longitude': float(data.get('longitude')) if data.get('longitude') else None,
            'bank_code': user.get('bank_code'),
            'is_active': True,
            'created_at': datetime.utcnow()
        }
        
        result = db.atms.insert_one(atm_data)
        return jsonify({"success": True, "atm_id": str(result.inserted_id)})


@api_bp.route('/atms/<atm_id>', methods=['DELETE', 'PUT'])
@login_required_api
def manage_atm(atm_id):
    """Gestion d'un ATM spécifique (suppression, modification)"""
    from bson import ObjectId
    db = get_db()
    if db is None:
        return jsonify({"error": "Database unavailable"}), 500
    
    user_id = session.get('user_id')
    user = db.users.find_one({"_id": ObjectId(user_id)})
    
    if user.get('role') not in ['admin', 'admin_sr_bank', 'admin_associate_bank']:
        return jsonify({"success": False, "error": "Non autorisé"}), 403
    
    if request.method == 'DELETE':
        result = db.atms.delete_one({"_id": ObjectId(atm_id)})
        return jsonify({"success": result.deleted_count > 0})
    
    elif request.method == 'PUT':
        data = request.get_json()
        update_data = {
            'name': data.get('name'),
            'address': data.get('address'),
            'city': data.get('city'),
            'latitude': float(data.get('latitude')) if data.get('latitude') else None,
            'longitude': float(data.get('longitude')) if data.get('longitude') else None,
            'is_active': data.get('is_active', True)
        }
        
        result = db.atms.update_one({"_id": ObjectId(atm_id)}, {"$set": update_data})
        return jsonify({"success": result.modified_count > 0})


# ==================== BANK API CONTROL ====================

@api_bp.route('/bank-settings/regenerate-keys', methods=['POST'])
@login_required_api
def regenerate_api_keys():
    """Régénère les clés API pour une banque"""
    import secrets
    from bson import ObjectId
    
    db = get_db()
    if db is None:
        return jsonify({"error": "Database unavailable"}), 500
    
    user_id = session.get('user_id')
    user = db.users.find_one({"_id": ObjectId(user_id)})
    
    if user.get('role') not in ['admin', 'admin_sr_bank', 'admin_associate_bank']:
        return jsonify({"success": False, "error": "Non autorisé"}), 403
    
    if not user.get('bank_code'):
        return jsonify({"success": False, "error": "Aucune banque associée"}), 400
    
    # Générer de nouvelles clés
    api_key = 'sk_' + secrets.token_urlsafe(32)
    api_secret = secrets.token_urlsafe(48)
    
    # Mettre à jour la banque
    result = db.banks.update_one(
        {'code': user['bank_code']},
        {
            '$set': {
                'api_key': api_key,
                'api_secret': api_secret,
                'api_keys_regenerated_at': datetime.utcnow()
            }
        }
    )
    
    return jsonify({
        "success": result.modified_count > 0,
        "api_key": api_key,
        "api_secret": api_secret
    })


@api_bp.route('/bank-settings/sync', methods=['POST'])
@login_required_api
def sync_bank_data():
    """Synchronise les données bancaires"""
    from bson import ObjectId
    
    db = get_db()
    if db is None:
        return jsonify({"error": "Database unavailable"}), 500
    
    user_id = session.get('user_id')
    user = db.users.find_one({"_id": ObjectId(user_id)})
    
    if user.get('role') not in ['admin', 'admin_sr_bank', 'admin_associate_bank']:
        return jsonify({"success": False, "error": "Non autorisé"}), 403
    
    if not user.get('bank_code'):
        return jsonify({"success": False, "error": "Aucune banque associée"}), 400
    
    # Mettre à jour la date de dernière synchronisation
    result = db.banks.update_one(
        {'code': user['bank_code']},
        {
            '$set': {
                'last_api_sync': datetime.utcnow().isoformat()
            }
        }
    )
    
    return jsonify({
        "success": result.modified_count > 0,
        "message": "Synchronisation réussie",
        "timestamp": datetime.utcnow().isoformat()
    })
