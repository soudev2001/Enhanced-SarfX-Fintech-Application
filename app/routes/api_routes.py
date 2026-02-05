from flask import Blueprint, jsonify, request, session
from app.services.db_service import get_db, safe_object_id
from app.decorators import login_required_api
from app.config import Config
from datetime import datetime
from bson import ObjectId
from bson.errors import InvalidId
import uuid
import requests
import time

api_bp = Blueprint('api', __name__)


# ==================== RATE CACHE ====================
_rate_cache = {}
_cache_ttl = Config.RATES_CACHE_TTL  # 30 secondes par defaut

def get_cached_rate(cache_key):
    """Recupere un taux du cache s'il est encore valide"""
    if cache_key in _rate_cache:
        cached = _rate_cache[cache_key]
        if time.time() - cached['timestamp'] < _cache_ttl:
            return cached['data']
    return None

def set_cached_rate(cache_key, data):
    """Met en cache un taux avec timestamp"""
    _rate_cache[cache_key] = {
        'data': data,
        'timestamp': time.time()
    }


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
        {"email": "bank@sarfx.io", "password": "bank123", "name": "Bank Manager", "role": "bank_respo"},
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
            {"email": "bank@sarfx.io", "password": "bank123", "role": "bank_respo"},
            {"email": "user@sarfx.io", "password": "user123", "role": "user"}
        ]
    })


# ==================== SMART RATE (IA Backend) ====================

# Fallback rates when AI backend is unavailable
FALLBACK_RATES = {
    'EURMAD': 10.82, 'USDMAD': 10.05, 'GBPMAD': 12.67, 'CHFMAD': 11.23, 'CADMAD': 7.45,
    'MADEUR': 0.092, 'MADUSD': 0.099, 'MADGBP': 0.079,
    'EURUSD': 1.08, 'USDEUR': 0.93, 'GBPUSD': 1.26, 'USDGBP': 0.79,
    'EURGBP': 0.85, 'GBPEUR': 1.17, 'CHFEUR': 1.09, 'CHFUSD': 1.17,
    'CADEUR': 0.68, 'CADUSD': 0.73, 'CADGBP': 0.58
}

@api_bp.route('/smart-rate/<base>/<target>')
def get_smart_rate(base, target):
    """
    Récupère le taux intelligent depuis le backend IA SarfX.
    Utilise un cache de 30s et un fallback si l'API est indisponible.
    """
    amount = request.args.get('amount', 1000, type=float)
    cache_key = f"{base}_{target}_{amount}"

    # Check cache first
    cached = get_cached_rate(cache_key)
    if cached:
        cached['from_cache'] = True
        return jsonify(cached)

    # Try AI Backend
    try:
        ai_url = f"{Config.AI_BACKEND_URL}/smart-rate/{base}/{target}"
        response = requests.get(
            ai_url,
            params={'amount': amount},
            timeout=Config.AI_BACKEND_TIMEOUT
        )

        if response.status_code == 200:
            data = response.json()

            # Normalize response structure
            result = {
                'success': True,
                'source': 'ai_backend',
                'base': base,
                'target': target,
                'amount': amount,
                'sarfx_offer': data.get('sarfx_offer', {
                    'rate': data.get('rate', FALLBACK_RATES.get(f"{base}{target}", 1.0)),
                    'final_amount': data.get('final_amount', amount * FALLBACK_RATES.get(f"{base}{target}", 1.0)),
                    'fees': amount * 0.005
                }),
                'market_intelligence': data.get('market_intelligence', {
                    'bank_rate': FALLBACK_RATES.get(f"{base}{target}", 1.0) * 0.975,
                    'market_rate': FALLBACK_RATES.get(f"{base}{target}", 1.0),
                    'best_liquidity_source': 'market',
                    'savings': 0
                }),
                'providers': data.get('providers', []),
                'ai_advisor': data.get('ai_advisor', {
                    'signal': 'NEUTRE',
                    'confidence': 0.7,
                    'message': 'Taux stables'
                }),
                'timestamp': datetime.utcnow().isoformat(),
                'from_cache': False
            }

            # Cache the result
            set_cached_rate(cache_key, result)
            return jsonify(result)

    except requests.exceptions.RequestException as e:
        print(f"⚠️ AI Backend unavailable: {e}")
    except Exception as e:
        print(f"❌ Error calling AI Backend: {e}")

    # Fallback to hardcoded rates
    pair = f"{base}{target}"
    fallback_rate = FALLBACK_RATES.get(pair, 1.0)
    sarfx_rate = fallback_rate * 1.005  # SarfX gets slightly better rate
    bank_rate = fallback_rate * 0.975
    fees = amount * 0.005
    final_amount = (amount - fees) * sarfx_rate

    result = {
        'success': True,
        'source': 'fallback',
        'base': base,
        'target': target,
        'amount': amount,
        'sarfx_offer': {
            'rate': sarfx_rate,
            'final_amount': final_amount,
            'fees': fees
        },
        'market_intelligence': {
            'bank_rate': bank_rate,
            'market_rate': fallback_rate,
            'best_liquidity_source': 'fallback',
            'savings': (final_amount) - ((amount - 25) * bank_rate)  # 25€ typical bank fee
        },
        'providers': [
            {'name': 'SarfX', 'rate': sarfx_rate, 'fee': fees, 'final': final_amount, 'delivery': 'instant', 'best': True},
            {'name': 'Wise', 'rate': fallback_rate * 1.002, 'fee': 4.50, 'final': (amount - 4.50) * fallback_rate * 1.002, 'delivery': 'instant'},
            {'name': 'Revolut', 'rate': fallback_rate * 0.998, 'fee': 5.00, 'final': (amount - 5.00) * fallback_rate * 0.998, 'delivery': '1-2h'},
            {'name': 'Western Union', 'rate': fallback_rate * 0.991, 'fee': 12.00, 'final': (amount - 12.00) * fallback_rate * 0.991, 'delivery': '1 day'},
            {'name': 'Bank Transfer', 'rate': bank_rate, 'fee': 25.00, 'final': (amount - 25.00) * bank_rate, 'delivery': '3-5 days'}
        ],
        'ai_advisor': {
            'signal': 'NEUTRE',
            'confidence': 0.6,
            'message': 'Service IA temporairement indisponible, taux estimés'
        },
        'timestamp': datetime.utcnow().isoformat(),
        'from_cache': False
    }

    # Cache even fallback for consistency
    set_cached_rate(cache_key, result)
    return jsonify(result)


@api_bp.route('/smart-rate/status')
def smart_rate_status():
    """Vérifie le statut du backend IA"""
    try:
        response = requests.get(
            f"{Config.AI_BACKEND_URL}/",
            timeout=2
        )
        if response.status_code == 200:
            return jsonify({
                'status': 'online',
                'backend_url': Config.AI_BACKEND_URL,
                'cache_ttl': _cache_ttl,
                'cached_pairs': len(_rate_cache)
            })
    except:
        pass

    return jsonify({
        'status': 'offline',
        'backend_url': Config.AI_BACKEND_URL,
        'fallback_active': True,
        'cached_pairs': len(_rate_cache)
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
        alerts = list(db.rate_alerts.find({"user_id": user_id})) if db is not None else []
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

        if db is not None:
            result = db.rate_alerts.insert_one(alert)
            alert['_id'] = str(result.inserted_id)

        return jsonify({'success': True, 'alert': alert})

    elif request.method == 'DELETE':
        alert_id = request.args.get('id')
        if db is not None and alert_id:
            from bson import ObjectId
            db.rate_alerts.delete_one({"_id": ObjectId(alert_id), "user_id": user_id})
        return jsonify({'success': True})


# ==================== EXCHANGE ====================

@api_bp.route('/exchange', methods=['POST'])
@login_required_api
def create_exchange():
    """Crée une nouvelle transaction d'échange - AVEC VÉRIFICATION DU SOLDE"""
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

    from_currency = data['from_currency']
    to_currency = data['to_currency']
    user_id = session['user_id']

    # ========== VÉRIFICATION DU SOLDE ==========
    from app.services.wallet_service import get_wallet_by_user_id, withdraw_from_wallet

    wallet, wallet_error = get_wallet_by_user_id(user_id)
    if not wallet or wallet_error:
        error_msg = wallet_error or "Vous n'avez pas de portefeuille. Veuillez en créer un d'abord."
        if request.form:
            from flask import redirect, url_for, flash
            flash(error_msg, "error")
            return redirect(url_for('app.converter'))
        return jsonify({"error": error_msg}), 400

    # Vérifier le solde disponible
    balances = wallet.get('balances', {})
    current_balance = float(balances.get(from_currency, 0))

    if current_balance < amount:
        error_msg = f"Solde insuffisant! Vous avez {current_balance:.2f} {from_currency} mais vous essayez d'envoyer {amount:.2f} {from_currency}."
        if request.form:
            from flask import redirect, url_for, flash
            flash(error_msg, "error")
            return redirect(url_for('app.converter'))
        return jsonify({"error": error_msg}), 400

    # ========== DÉBITER LE WALLET ==========
    recipient_name = data.get('recipient_name', 'Inconnu')
    success, message = withdraw_from_wallet(
        user_id=user_id,
        currency=from_currency,
        amount=amount,
        destination=f"Échange vers {to_currency} - {recipient_name}"
    )

    if not success:
        error_msg = f"Erreur lors du débit: {message}"
        if request.form:
            from flask import redirect, url_for, flash
            flash(error_msg, "error")
            return redirect(url_for('app.converter'))
        return jsonify({"error": error_msg}), 400

    # Créer la transaction
    transaction = {
        "transaction_id": str(uuid.uuid4()),
        "user_id": user_id,
        "type": "send",
        "amount": amount,
        "from_currency": from_currency,
        "to_currency": to_currency,
        "rate": rate,
        "final_amount": final_amount,
        "fee": amount * 0.01,  # 1% fee
        "supplier_id": data.get('supplier_id'),
        "recipient_name": recipient_name,
        "recipient_account": data.get('recipient_account', ''),
        "status": "completed",
        "wallet_debited": True,
        "previous_balance": current_balance,
        "new_balance": current_balance - amount,
        "created_at": datetime.utcnow()
    }

    result = db.transactions.insert_one(transaction)

    # Log history
    from app.services.db_service import log_history
    log_history("EXCHANGE", f"Échange de {amount} {from_currency} vers {final_amount} {to_currency} (wallet débité)",
                user=session.get('email', 'Unknown'))

    # Redirect or return JSON based on request type
    if request.form:
        from flask import redirect, url_for, flash
        flash(f"Échange réussi! {amount:.2f} {from_currency} débité de votre wallet. {final_amount:.2f} {to_currency} envoyés.", "success")
        return redirect(url_for('app.profile'))

    return jsonify({
        "success": True,
        "transaction_id": transaction['transaction_id'],
        "message": f"Échange réussi: {final_amount:.2f} {to_currency}",
        "wallet_debited": amount,
        "new_balance": current_balance - amount
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


# ==================== WALLET SWAP ====================

@api_bp.route('/wallet/swap/preview', methods=['POST'])
@login_required_api
def swap_preview():
    """Preview a currency swap without executing it"""
    from app.services.wallet_service import calculate_swap_preview

    data = request.json or {}
    from_currency = data.get('from_currency', '').upper()
    to_currency = data.get('to_currency', '').upper()
    amount = float(data.get('amount', 0))

    if not from_currency or not to_currency:
        return jsonify({"error": "from_currency and to_currency are required"}), 400

    if amount <= 0:
        return jsonify({"error": "Amount must be positive"}), 400

    preview, error = calculate_swap_preview(from_currency, to_currency, amount)

    if error:
        return jsonify({"error": error}), 400

    return jsonify({
        "success": True,
        **preview
    })


@api_bp.route('/wallet/swap', methods=['POST'])
@login_required_api
def execute_wallet_swap():
    """Execute a currency swap in the user's wallet"""
    from app.services.wallet_service import execute_swap

    data = request.json or {}
    from_currency = data.get('from_currency', '').upper()
    to_currency = data.get('to_currency', '').upper()
    amount = float(data.get('amount', 0))

    if not from_currency or not to_currency:
        return jsonify({"error": "from_currency and to_currency are required"}), 400

    if amount <= 0:
        return jsonify({"error": "Amount must be positive"}), 400

    result, error = execute_swap(session['user_id'], from_currency, to_currency, amount)

    if error:
        return jsonify({"error": error}), 400

    return jsonify(result)


@api_bp.route('/wallet/swap/rates')
@login_required_api
def get_swap_rates():
    """Get all available swap rates for user's wallet currencies"""
    from app.services.wallet_service import get_wallet_swap_rates

    rates, error = get_wallet_swap_rates(session['user_id'])

    if error:
        return jsonify({"error": error}), 400

    return jsonify({
        "success": True,
        "rates": rates,
        "timestamp": datetime.utcnow().isoformat()
    })


@api_bp.route('/wallet/deposit', methods=['POST'])
@login_required_api
def wallet_deposit():
    """Deposit funds to wallet (for testing/admin)"""
    from app.services.wallet_service import deposit_to_wallet

    # Check if admin or demo mode
    db = get_db()
    user = db.users.find_one({"_id": safe_object_id(session['user_id'])}) if db is not None else None
    is_admin = user and user.get('role') in ['admin', 'superadmin']

    # In production, this would be triggered by payment webhook
    # For now, allow for testing
    data = request.json or {}
    currency = data.get('currency', '').upper()
    amount = float(data.get('amount', 0))

    if not currency:
        return jsonify({"error": "Currency is required"}), 400

    if amount <= 0:
        return jsonify({"error": "Amount must be positive"}), 400

    # Limit non-admin deposits for security
    if not is_admin and amount > 1000:
        return jsonify({"error": "Maximum deposit amount is 1000 for non-admin users"}), 400

    success, message = deposit_to_wallet(session['user_id'], currency, amount, source="api")

    if success:
        return jsonify({"success": True, "message": message})
    else:
        return jsonify({"error": message}), 400


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
            if db is not None:
                from app.services.db_service import safe_object_id
                user_id = safe_object_id(session['user_id'])
                if user_id:
                    db.users.update_one(
                        {"_id": user_id},
                        {"$set": {"theme": theme}}
                    )

        return jsonify({"success": True, "theme": theme})
    except Exception as e:
        print(f"Theme error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route('/user/preferences', methods=['GET', 'POST'])
@login_required_api
def user_preferences():
    """Gère les préférences utilisateur (thème, couleur d'accent, etc.)"""
    db = get_db()
    if db is None:
        return jsonify({"success": False, "error": "Database unavailable"}), 500

    from app.services.db_service import safe_object_id
    user_id = safe_object_id(session.get('user_id'))
    if not user_id:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    if request.method == 'GET':
        # Récupérer les préférences
        user = db.users.find_one({"_id": user_id}, {
            "theme": 1,
            "accent_color": 1,
            "notification_preferences": 1,
            "language": 1
        })
        if not user:
            return jsonify({"success": False, "error": "User not found"}), 404

        return jsonify({
            "success": True,
            "preferences": {
                "theme": user.get("theme", "light"),
                "accent_color": user.get("accent_color", "orange"),
                "notifications": user.get("notification_preferences", {}),
                "language": user.get("language", "fr")
            }
        })

    # POST - Sauvegarder les préférences
    try:
        data = request.json or {}

        update_fields = {}

        # Couleur d'accent
        if 'accent_color' in data:
            valid_colors = ['orange', 'blue', 'green', 'purple', 'pink', 'red', 'teal', 'amber', 'cyan', 'indigo', 'lime', 'rose']
            if data['accent_color'] in valid_colors:
                update_fields['accent_color'] = data['accent_color']
                session['accent_color'] = data['accent_color']

        # Thème
        if 'theme' in data:
            if data['theme'] in ['light', 'dark', 'system']:
                update_fields['theme'] = data['theme']
                session['theme'] = data['theme']

        # Préférences de notifications
        if 'notifications' in data:
            update_fields['notification_preferences'] = data['notifications']

        # Langue
        if 'language' in data:
            valid_langs = ['fr', 'en', 'ar', 'es']
            if data['language'] in valid_langs:
                update_fields['language'] = data['language']
                session['lang'] = data['language']

        if update_fields:
            update_fields['preferences_updated_at'] = datetime.utcnow()
            db.users.update_one(
                {"_id": user_id},
                {"$set": update_fields}
            )

        return jsonify({
            "success": True,
            "message": "Préférences sauvegardées",
            "updated": list(update_fields.keys())
        })

    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"User preferences error: {e}")
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
    from app.services.db_service import safe_object_id
    user_id = safe_object_id(session['user_id'])
    user = db.users.find_one({"_id": user_id}) if user_id else db.users.find_one({"email": session.get('email')})
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


# ==================== BANK CARDS ====================

@api_bp.route('/cards', methods=['GET'])
@login_required_api
def get_user_cards():
    """Récupère les cartes bancaires de l'utilisateur"""
    try:
        db = get_db()
        if db is None:
            return jsonify({"error": "Database unavailable"}), 500

        user_id = session.get('user_id')
        cards = list(db.user_cards.find({"user_id": str(user_id)}).sort("created_at", -1))

        # Convertir ObjectId en string
        for card in cards:
            card['_id'] = str(card['_id'])

        return jsonify({
            "success": True,
            "cards": cards
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route('/cards', methods=['POST'])
@login_required_api
def add_user_card():
    """Ajoute une carte bancaire (stocke uniquement les 4 derniers chiffres)"""
    try:
        db = get_db()
        if db is None:
            return jsonify({"error": "Database unavailable"}), 500

        user_id = session.get('user_id')
        data = request.json

        last_four = data.get('last_four', '')
        expiry = data.get('expiry', '')
        holder_name = data.get('holder_name', '')

        # Validation
        if not last_four or len(last_four) != 4 or not last_four.isdigit():
            return jsonify({"success": False, "error": "4 derniers chiffres invalides"}), 400

        if not expiry or len(expiry) != 5 or '/' not in expiry:
            return jsonify({"success": False, "error": "Date d'expiration invalide (format MM/AA)"}), 400

        if not holder_name or len(holder_name) < 2:
            return jsonify({"success": False, "error": "Nom du titulaire requis"}), 400

        # Vérifier si la carte existe déjà
        existing = db.user_cards.find_one({
            "user_id": str(user_id),
            "last_four": last_four,
            "expiry": expiry
        })

        if existing:
            return jsonify({"success": False, "error": "Cette carte existe déjà"}), 400

        # Créer la carte (JAMAIS stocker le numéro complet ou le CVV)
        card = {
            "user_id": str(user_id),
            "last_four": last_four,
            "expiry": expiry,
            "holder_name": holder_name.upper(),
            "created_at": datetime.utcnow()
        }

        result = db.user_cards.insert_one(card)
        card['_id'] = str(result.inserted_id)

        return jsonify({
            "success": True,
            "card": card,
            "message": "Carte ajoutée avec succès"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route('/cards/<card_id>', methods=['DELETE'])
@login_required_api
def delete_user_card(card_id):
    """Supprime une carte bancaire"""
    try:
        from bson import ObjectId
        db = get_db()
        if db is None:
            return jsonify({"error": "Database unavailable"}), 500

        user_id = session.get('user_id')

        # Vérifier que la carte appartient à l'utilisateur
        card = db.user_cards.find_one({
            "_id": ObjectId(card_id),
            "user_id": str(user_id)
        })

        if not card:
            return jsonify({"success": False, "error": "Carte non trouvée"}), 404

        db.user_cards.delete_one({"_id": ObjectId(card_id)})

        return jsonify({
            "success": True,
            "message": "Carte supprimée avec succès"
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


# ==================== CHATBOT ====================

@api_bp.route('/chatbot/message', methods=['POST'])
def chatbot_message():
    """
    Envoie un message au chatbot et reçoit une réponse

    Features:
    - RBAC: Réponses adaptées au rôle utilisateur
    - Function Calling: Exécution de tools (solde, taux, ATMs, stats...)
    - Rate Limiting: 5 req/min anonymes, 30 req/min authentifiés
    - Mémoire: Historique de conversation en MongoDB
    - Fallback gracieux: Messages d'erreur spécifiques
    """
    try:
        from app.services.chatbot_service import chatbot_service
        from bson import ObjectId
        import uuid

        db = get_db()
        data = request.get_json()
        message = data.get('message', '')
        context_type = data.get('context', 'app')  # 'landing', 'app', 'backoffice'

        if not message:
            return jsonify({"success": False, "error": "Message vide"}), 400

        # Récupérer le contexte utilisateur
        user_context = {'role': 'anonymous'}
        user = None

        if 'user_id' in session and db:
            try:
                from app.services.db_service import safe_object_id
                user_id = safe_object_id(session['user_id'])
                user = db.users.find_one({"_id": user_id}) if user_id else db.users.find_one({"email": session.get('email')})
                if user:
                    user_context = {
                        'user_id': str(user['_id']),
                        'role': user.get('role', 'user'),
                        'email': user.get('email', ''),
                        'bank_code': user.get('bank_code', ''),
                        'is_authenticated': True
                    }
            except Exception as e:
                print(f"Error fetching user context: {e}")

        # Récupérer ou créer l'ID de session pour la mémoire de conversation
        session_id = data.get('session_id') or session.get('chat_session_id')
        if not session_id:
            session_id = str(uuid.uuid4())
            session['chat_session_id'] = session_id

        # Récupérer l'adresse IP pour rate limiting
        ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
        if ip_address and ',' in ip_address:
            ip_address = ip_address.split(',')[0].strip()

        # Générer la réponse avec toutes les fonctionnalités
        result = chatbot_service.generate_response(
            message=message,
            user_context=user_context,
            db=db,
            session_id=session_id,
            ip_address=ip_address
        )

        # Gérer le rate limiting
        if result.get('error') == 'rate_limited':
            return jsonify({
                "success": False,
                "error": "rate_limited",
                "response": result['response'],
                "retry_after": result.get('retry_after', 60)
            }), 429

        if result.get('success'):
            response_data = {
                "success": True,
                "response": result['response'],
                "session_id": session_id
            }

            # Ajouter les métadonnées optionnelles
            if result.get('tool_used'):
                response_data['tool_used'] = result['tool_used']
            if result.get('data'):
                response_data['data'] = result['data']
            if result.get('remaining_requests') is not None:
                response_data['remaining_requests'] = result['remaining_requests']

            return jsonify(response_data)
        else:
            return jsonify({
                "success": False,
                "error": result.get('error', 'Erreur inconnue'),
                "response": result.get('response', "Désolé, une erreur est survenue.")
            }), 500

    except Exception as e:
        print(f"Chatbot error: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "response": "Une erreur technique est survenue. Veuillez réessayer dans quelques instants."
        }), 500


@api_bp.route('/chatbot/suggestions', methods=['GET'])
def chatbot_suggestions():
    """
    Retourne les suggestions de questions pour le chatbot
    Adaptées au contexte (landing/app/backoffice) et au rôle utilisateur
    """
    try:
        from app.services.chatbot_service import chatbot_service
        from app.services.db_service import safe_object_id

        db = get_db()
        user = None
        context_type = request.args.get('context', 'landing')  # 'landing', 'app', 'backoffice'

        if 'user_id' in session and db:
            try:
                user_id = safe_object_id(session['user_id'])
                user = db.users.find_one({"_id": user_id}) if user_id else db.users.find_one({"email": session.get('email')})
            except Exception:
                pass

        suggestions = chatbot_service.get_suggestions(db, user, context_type)

        return jsonify({
            "success": True,
            "suggestions": suggestions,
            "context": context_type,
            "user_role": user.get('role', 'anonymous') if user else 'anonymous'
        })
    except Exception as e:
        print(f"Suggestions error: {e}")
        return jsonify({
            "success": True,
            "suggestions": [
                "C'est quoi SarfX ?",
                "Taux de change actuel",
                "Où trouver un ATM ?"
            ],
            "context": "landing"
        })


@api_bp.route('/chatbot/history', methods=['GET', 'DELETE'])
def chatbot_history():
    """
    Gestion de l'historique de conversation
    GET: Récupère l'historique
    DELETE: Efface l'historique
    """
    try:
        from app.services.chatbot_service import chatbot_service

        db = get_db()
        session_id = request.args.get('session_id') or session.get('chat_session_id')

        if not session_id:
            return jsonify({
                "success": True,
                "history": [],
                "message": "Pas de session de conversation active"
            })

        if request.method == 'DELETE':
            # Effacer l'historique
            success = chatbot_service.clear_conversation_history(db, session_id)
            if 'chat_session_id' in session:
                del session['chat_session_id']

            return jsonify({
                "success": success,
                "message": "Historique de conversation effacé" if success else "Erreur lors de l'effacement"
            })

        # GET: Récupérer l'historique
        history = chatbot_service.get_conversation_history(db, session_id, limit=20)

        # Formater pour l'affichage
        formatted_history = []
        for msg in history:
            formatted_history.append({
                'role': msg['role'],
                'content': msg['content'],
                'timestamp': msg['timestamp'].isoformat() if msg.get('timestamp') else None
            })

        return jsonify({
            "success": True,
            "history": formatted_history,
            "session_id": session_id,
            "count": len(formatted_history)
        })

    except Exception as e:
        print(f"History error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


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

        if user.get('role') not in ['admin', 'admin_sr_bank', 'admin_associate_bank', 'bank_respo']:
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

    if user.get('role') not in ['admin', 'admin_sr_bank', 'admin_associate_bank', 'bank_respo']:
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


# ==================== ADMIN WALLET STATS ====================
@api_bp.route('/admin/wallet-stats', methods=['GET'])
@login_required_api
def admin_wallet_stats():
    """Retourne les statistiques des portefeuilles pour l'admin"""
    db = get_db()
    if db is None:
        return jsonify({"error": "Database unavailable"}), 500

    # Vérifier que l'utilisateur est admin
    user_id = session.get('user_id')
    user = db.users.find_one({"_id": safe_object_id(user_id)})

    if not user or user.get('role') != 'admin':
        return jsonify({"error": "Non autorisé"}), 403

    try:
        # Calculer les soldes totaux par devise
        total_balances = {}
        total_wallets = 0
        active_wallets = 0

        wallets = list(db.wallets.find({}))
        total_wallets = len(wallets)

        for wallet in wallets:
            if wallet.get('is_active', True):
                active_wallets += 1

            balances = wallet.get('balances', {})
            for currency, balance in balances.items():
                if currency not in total_balances:
                    total_balances[currency] = 0
                total_balances[currency] += balance

        # Compter les ajustements
        total_adjustments = db.wallet_adjustments.count_documents({}) if 'wallet_adjustments' in db.list_collection_names() else 0

        return jsonify({
            "success": True,
            "total_wallets": total_wallets,
            "active_wallets": active_wallets,
            "total_adjustments": total_adjustments,
            "total_balances": total_balances,
            "currencies_count": len(total_balances)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==================== GLOBAL SEARCH API ====================

@api_bp.route('/search')
@login_required_api
def global_search():
    """Recherche globale dans l'application"""
    db = get_db()
    if db is None:
        return jsonify({"error": "Database unavailable", "results": []}), 500

    query = request.args.get('q', '').strip()
    if len(query) < 2:
        return jsonify({"results": []})

    user_id = session.get('user_id')
    results = []

    try:
        # Regex pour recherche insensible à la casse
        import re
        regex_pattern = re.compile(query, re.IGNORECASE)

        # 1. Recherche dans les transactions de l'utilisateur
        transactions = list(db.transactions.find({
            "user_id": user_id,
            "$or": [
                {"reference": {"$regex": regex_pattern}},
                {"from_currency": {"$regex": regex_pattern}},
                {"to_currency": {"$regex": regex_pattern}},
                {"type": {"$regex": regex_pattern}},
                {"description": {"$regex": regex_pattern}}
            ]
        }).limit(5))

        for tx in transactions:
            results.append({
                "type": "transaction",
                "title": f"{tx.get('from_currency', '')} → {tx.get('to_currency', '')}",
                "subtitle": f"Réf: {tx.get('reference', 'N/A')} | {tx.get('amount', 0)} {tx.get('from_currency', '')}",
                "url": f"/app/transactions?highlight={str(tx.get('_id', ''))}"
            })

        # 2. Recherche dans les bénéficiaires de l'utilisateur
        beneficiaries = list(db.beneficiaries.find({
            "user_id": user_id,
            "$or": [
                {"name": {"$regex": regex_pattern}},
                {"email": {"$regex": regex_pattern}},
                {"iban": {"$regex": regex_pattern}},
                {"bank_name": {"$regex": regex_pattern}}
            ]
        }).limit(5))

        for ben in beneficiaries:
            results.append({
                "type": "beneficiary",
                "title": ben.get('name', 'Sans nom'),
                "subtitle": ben.get('email', '') or ben.get('iban', '')[:20] + '...' if ben.get('iban') else '',
                "url": f"/app/beneficiaries?highlight={str(ben.get('_id', ''))}"
            })

        # 3. Recherche dans les ATMs
        atms = list(db.atms.find({
            "$or": [
                {"name": {"$regex": regex_pattern}},
                {"city": {"$regex": regex_pattern}},
                {"address": {"$regex": regex_pattern}},
                {"bank_name": {"$regex": regex_pattern}}
            ]
        }).limit(5))

        for atm in atms:
            results.append({
                "type": "atm",
                "title": atm.get('name', 'ATM'),
                "subtitle": f"{atm.get('city', '')} - {atm.get('bank_name', '')}",
                "url": f"/app/atms?highlight={str(atm.get('_id', ''))}"
            })

        # 4. Recherche dans les pages de navigation
        pages = [
            {"name": "Accueil", "url": "/app/home", "keywords": ["accueil", "home", "dashboard", "tableau de bord"]},
            {"name": "Wallets", "url": "/app/wallets", "keywords": ["wallets", "portefeuilles", "soldes", "balances"]},
            {"name": "Convertir", "url": "/app/converter", "keywords": ["convertir", "converter", "exchange", "change", "taux"]},
            {"name": "Transactions", "url": "/app/transactions", "keywords": ["transactions", "historique", "history", "paiements"]},
            {"name": "Bénéficiaires", "url": "/app/beneficiaries", "keywords": ["bénéficiaires", "beneficiaries", "contacts"]},
            {"name": "ATMs", "url": "/app/atms", "keywords": ["atm", "distributeur", "cash", "retrait"]},
            {"name": "Profil", "url": "/app/profile", "keywords": ["profil", "profile", "compte", "account"]},
            {"name": "Réglages", "url": "/app/settings", "keywords": ["réglages", "settings", "paramètres", "preferences"]},
            {"name": "FAQ", "url": "/app/faq", "keywords": ["faq", "aide", "help", "questions"]},
            {"name": "IA Prédictions", "url": "/app/ai-forecast", "keywords": ["ia", "ai", "prédictions", "forecast", "machine learning"]}
        ]

        query_lower = query.lower()
        for page in pages:
            if query_lower in page["name"].lower() or any(query_lower in kw for kw in page["keywords"]):
                results.append({
                    "type": "page",
                    "title": page["name"],
                    "subtitle": "Page de navigation",
                    "url": page["url"]
                })

        # Limiter le nombre total de résultats
        results = results[:15]

        return jsonify({
            "success": True,
            "query": query,
            "results": results,
            "count": len(results)
        })

    except Exception as e:
        print(f"Search error: {e}")
        return jsonify({"error": str(e), "results": []}), 500


# ==================== KYC SERVICE API ====================

@api_bp.route('/kyc/status')
@login_required_api
def get_kyc_status():
    """Récupère le statut KYC de l'utilisateur connecté"""
    from app.services.kyc_service import get_kyc_service

    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Non authentifié"}), 401

    kyc_service = get_kyc_service()
    status = kyc_service.get_user_kyc_status(user_id)

    return jsonify(status)


@api_bp.route('/kyc/upload', methods=['POST'])
@login_required_api
def upload_kyc_document():
    """Upload un document KYC"""
    from app.services.kyc_service import get_kyc_service
    import hashlib
    import os

    db = get_db()
    if db is None:
        return jsonify({"success": False, "error": "Database unavailable"}), 500

    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "error": "Non authentifié"}), 401

    # Vérifier le fichier
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "Aucun fichier fourni"}), 400

    file = request.files['file']
    document_type = request.form.get('document_type', 'id_card')

    if file.filename == '':
        return jsonify({"success": False, "error": "Nom de fichier vide"}), 400

    # Vérifier l'extension
    allowed_extensions = {'pdf', 'jpg', 'jpeg', 'png', 'webp'}
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in allowed_extensions:
        return jsonify({"success": False, "error": f"Extension non autorisée. Utilisez: {', '.join(allowed_extensions)}"}), 400

    # Vérifier la taille (max 10MB)
    file.seek(0, 2)
    file_size = file.tell()
    file.seek(0)

    if file_size > 10 * 1024 * 1024:
        return jsonify({"success": False, "error": "Fichier trop volumineux (max 10MB)"}), 400

    try:
        # Créer le dossier uploads si nécessaire
        upload_folder = os.path.join(os.getcwd(), 'uploads', 'kyc', user_id)
        os.makedirs(upload_folder, exist_ok=True)

        # Générer un nom de fichier unique
        file_hash = hashlib.md5(file.read()).hexdigest()[:12]
        file.seek(0)

        filename = f"{document_type}_{file_hash}.{ext}"
        file_path = os.path.join(upload_folder, filename)

        # Sauvegarder le fichier
        file.save(file_path)

        # Enregistrer dans le service KYC
        kyc_service = get_kyc_service()
        result = kyc_service.upload_document(user_id, document_type, {
            "filename": filename,
            "content_type": file.content_type,
            "file_path": file_path,
            "file_hash": file_hash,
            "file_size": file_size,
        })

        return jsonify(result)

    except Exception as e:
        print(f"KYC upload error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route('/kyc/documents/<document_id>/verify', methods=['POST'])
@login_required_api
def verify_kyc_document(document_id):
    """Vérifie/Rejette un document KYC (admin uniquement)"""
    from app.services.kyc_service import get_kyc_service

    db = get_db()
    if db is None:
        return jsonify({"success": False, "error": "Database unavailable"}), 500

    user_id = session.get('user_id')
    user = db.users.find_one({"_id": safe_object_id(user_id)})

    if not user or user.get('role') != 'admin':
        return jsonify({"success": False, "error": "Non autorisé"}), 403

    data = request.get_json() or {}
    approved = data.get('approved', False)
    reason = data.get('reason')

    kyc_service = get_kyc_service()
    result = kyc_service.verify_document(document_id, user_id, approved, reason)

    return jsonify(result)


@api_bp.route('/kyc/pending')
@login_required_api
def get_pending_kyc_documents():
    """Récupère les documents KYC en attente (admin uniquement)"""
    from app.services.kyc_service import get_kyc_service

    db = get_db()
    if db is None:
        return jsonify({"error": "Database unavailable"}), 500

    user_id = session.get('user_id')
    user = db.users.find_one({"_id": safe_object_id(user_id)})

    if not user or user.get('role') != 'admin':
        return jsonify({"error": "Non autorisé"}), 403

    kyc_service = get_kyc_service()
    documents = kyc_service.get_pending_documents()

    return jsonify({
        "success": True,
        "documents": documents,
        "count": len(documents)
    })


@api_bp.route('/kyc/statistics')
@login_required_api
def get_kyc_statistics():
    """Récupère les statistiques KYC (admin uniquement)"""
    from app.services.kyc_service import get_kyc_service

    db = get_db()
    if db is None:
        return jsonify({"error": "Database unavailable"}), 500

    user_id = session.get('user_id')
    user = db.users.find_one({"_id": safe_object_id(user_id)})

    if not user or user.get('role') != 'admin':
        return jsonify({"error": "Non autorisé"}), 403

    kyc_service = get_kyc_service()
    stats = kyc_service.get_kyc_statistics()

    return jsonify({
        "success": True,
        **stats
    })


# ==================== NOTIFICATIONS PUSH SERVICE ====================

@api_bp.route('/notifications/check')
@login_required_api
def check_new_notifications():
    """Vérifie s'il y a de nouvelles notifications non lues"""
    from app.services.db_service import get_db
    from datetime import datetime, timedelta

    user_id = session.get('user_id')
    db = get_db()

    if db is None:
        return jsonify({
            "success": True,
            "hasNew": False,
            "unread_count": 0
        })

    # Compter les notifications non lues
    unread_count = db.notifications.count_documents({
        "user_id": user_id,
        "read": False
    })

    # Récupérer la dernière notification (pour affichage push)
    latest = None
    has_new = False

    if unread_count > 0:
        latest_doc = db.notifications.find_one(
            {"user_id": user_id, "read": False},
            sort=[("created_at", -1)]
        )
        if latest_doc:
            has_new = True
            latest = {
                "id": str(latest_doc.get("_id")),
                "title": latest_doc.get("title", "Notification"),
                "message": latest_doc.get("message", ""),
                "type": latest_doc.get("type", "info"),
                "created_at": latest_doc.get("created_at", datetime.utcnow()).isoformat()
            }

    return jsonify({
        "success": True,
        "hasNew": has_new,
        "unread_count": unread_count,
        "latest": latest
    })


@api_bp.route('/notifications')
@login_required_api
def get_user_notifications():
    """Récupère les notifications de l'utilisateur avec pagination"""
    from app.services.notification_service import get_notification_service

    user_id = session.get('user_id')
    limit = int(request.args.get('limit', 20))
    offset = int(request.args.get('offset', 0))
    unread_only = request.args.get('unread_only', 'false').lower() == 'true'

    notif_service = get_notification_service()
    notifications = notif_service.get_user_notifications(
        user_id,
        limit=limit,
        offset=offset,
        unread_only=unread_only
    )

    # Compter les non-lues
    db = get_db()
    unread_count = 0
    if db is not None:
        unread_count = db.notifications.count_documents({
            "user_id": user_id,
            "read": False
        })

    return jsonify({
        "success": True,
        "notifications": notifications,
        "unread_count": unread_count,
        "limit": limit,
        "offset": offset
    })


@api_bp.route('/notifications/<notification_id>/read', methods=['POST'])
@login_required_api
def mark_notification_as_read(notification_id):
    """Marque une notification comme lue"""
    from app.services.notification_service import get_notification_service

    user_id = session.get('user_id')
    notif_service = get_notification_service()
    result = notif_service.mark_as_read(notification_id, user_id)

    return jsonify(result)


@api_bp.route('/notifications/read-all', methods=['POST'])
@login_required_api
def mark_all_notifications_read():
    """Marque toutes les notifications comme lues"""
    from app.services.notification_service import get_notification_service

    user_id = session.get('user_id')
    notif_service = get_notification_service()
    result = notif_service.mark_all_as_read(user_id)

    return jsonify(result)


@api_bp.route('/notifications/subscribe', methods=['POST'])
@login_required_api
def subscribe_push_notifications():
    """Enregistre un abonnement aux notifications push"""
    from app.services.notification_service import get_notification_service

    user_id = session.get('user_id')
    data = request.get_json() or {}
    subscription = data.get('subscription')

    if not subscription:
        return jsonify({"success": False, "error": "Subscription data required"}), 400

    notif_service = get_notification_service()
    result = notif_service.register_push_subscription(user_id, subscription)

    return jsonify(result)


@api_bp.route('/notifications/unsubscribe', methods=['POST'])
@login_required_api
def unsubscribe_push_notifications():
    """Supprime un abonnement aux notifications push"""
    from app.services.notification_service import get_notification_service

    user_id = session.get('user_id')
    data = request.get_json() or {}
    endpoint = data.get('endpoint')

    if not endpoint:
        return jsonify({"success": False, "error": "Endpoint required"}), 400

    notif_service = get_notification_service()
    result = notif_service.unsubscribe_push(user_id, endpoint)

    return jsonify(result)


@api_bp.route('/notifications/preferences', methods=['GET', 'POST'])
@login_required_api
def notification_preferences():
    """Gère les préférences de notifications de l'utilisateur"""
    from app.services.notification_service import get_notification_service

    user_id = session.get('user_id')
    notif_service = get_notification_service()

    if request.method == 'GET':
        preferences = notif_service.get_user_preferences(user_id)
        return jsonify({
            "success": True,
            "preferences": preferences
        })

    # POST - Mise à jour des préférences
    data = request.get_json() or {}
    result = notif_service.update_user_preferences(user_id, data)

    return jsonify(result)


@api_bp.route('/notifications/test', methods=['POST'])
@login_required_api
def test_push_notification():
    """Envoie une notification de test (pour debug)"""
    from app.services.notification_service import get_notification_service

    user_id = session.get('user_id')
    notif_service = get_notification_service()

    # Créer une notification de test
    result = notif_service.create_notification(
        user_id=user_id,
        notification_type='system',
        title='🔔 Test de notification',
        message='Vos notifications push fonctionnent correctement!',
        icon='bell',
        color='#10B981',
        channels=['in_app', 'push']
    )

    return jsonify(result)


@api_bp.route('/notifications/stats')
@login_required_api
def get_notification_stats():
    """Statistiques des notifications (admin uniquement)"""
    db = get_db()
    if db is None:
        return jsonify({"error": "Database unavailable"}), 500

    user_id = session.get('user_id')
    user = db.users.find_one({"_id": safe_object_id(user_id)})

    if not user or user.get('role') != 'admin':
        return jsonify({"error": "Non autorisé"}), 403

    try:
        # Statistiques globales
        total_notifications = db.notifications.count_documents({})
        unread_notifications = db.notifications.count_documents({"read": False})
        push_subscriptions = db.push_subscriptions.count_documents({}) if 'push_subscriptions' in db.list_collection_names() else 0

        # Par type
        type_stats = list(db.notifications.aggregate([
            {"$group": {"_id": "$type", "count": {"$sum": 1}}}
        ]))

        # Par jour (7 derniers jours)
        from datetime import timedelta
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        daily_stats = list(db.notifications.aggregate([
            {"$match": {"created_at": {"$gte": seven_days_ago}}},
            {"$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}}
        ]))

        return jsonify({
            "success": True,
            "stats": {
                "total": total_notifications,
                "unread": unread_notifications,
                "push_subscriptions": push_subscriptions,
                "by_type": {item['_id']: item['count'] for item in type_stats},
                "daily": {item['_id']: item['count'] for item in daily_stats}
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ==================== EXPORT SERVICE API ====================

@api_bp.route('/export/transactions.csv')
@login_required_api
def export_transactions_csv():
    """Exporte les transactions au format CSV"""
    from flask import Response
    from app.services.export_service import get_export_service
    from datetime import timedelta

    db = get_db()
    user_id = session.get('user_id')
    user = db.users.find_one({"_id": safe_object_id(user_id)}) if db is not None else None

    # Paramètres
    is_admin = user and user.get('role') == 'admin'
    filter_user_id = None if is_admin else user_id

    # Dates optionnelles
    start_date = None
    end_date = None
    days = request.args.get('days')
    if days:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=int(days))

    export_service = get_export_service()
    csv_data = export_service.export_transactions_csv(
        user_id=filter_user_id,
        start_date=start_date,
        end_date=end_date,
        status=request.args.get('status'),
        currency=request.args.get('currency')
    )

    filename = f"sarfx_transactions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    return Response(
        csv_data.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )


@api_bp.route('/export/users.csv')
@login_required_api
def export_users_csv():
    """Exporte les utilisateurs au format CSV (admin uniquement)"""
    from flask import Response
    from app.services.export_service import get_export_service

    db = get_db()
    user_id = session.get('user_id')
    user = db.users.find_one({"_id": safe_object_id(user_id)}) if db is not None else None

    if not user or user.get('role') != 'admin':
        return jsonify({"error": "Non autorisé"}), 403

    export_service = get_export_service()
    csv_data = export_service.export_users_csv(
        role=request.args.get('role'),
        kyc_status=request.args.get('kyc_status')
    )

    filename = f"sarfx_users_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    return Response(
        csv_data.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )


@api_bp.route('/export/wallets.csv')
@login_required_api
def export_wallets_csv():
    """Exporte les wallets au format CSV"""
    from flask import Response
    from app.services.export_service import get_export_service

    db = get_db()
    user_id = session.get('user_id')
    user = db.users.find_one({"_id": safe_object_id(user_id)}) if db is not None else None

    is_admin = user and user.get('role') == 'admin'
    filter_user_id = None if is_admin else user_id

    export_service = get_export_service()
    csv_data = export_service.export_wallets_csv(user_id=filter_user_id)

    filename = f"sarfx_wallets_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    return Response(
        csv_data.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )


@api_bp.route('/export/beneficiaries.csv')
@login_required_api
def export_beneficiaries_csv():
    """Exporte les bénéficiaires au format CSV"""
    from flask import Response
    from app.services.export_service import get_export_service

    user_id = session.get('user_id')

    export_service = get_export_service()
    csv_data = export_service.export_beneficiaries_csv(user_id=user_id)

    filename = f"sarfx_beneficiaries_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    return Response(
        csv_data.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )


@api_bp.route('/export/transactions.pdf')
@login_required_api
def export_transactions_pdf():
    """Génère un rapport PDF des transactions (retourne HTML pour impression)"""
    from flask import Response
    from app.services.export_service import get_export_service
    from datetime import timedelta

    db = get_db()
    user_id = session.get('user_id')
    user = db.users.find_one({"_id": safe_object_id(user_id)}) if db is not None else None

    is_admin = user and user.get('role') == 'admin'
    filter_user_id = None if is_admin else user_id

    # Dates
    start_date = None
    end_date = None
    days = request.args.get('days', 30)
    if days:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=int(days))

    export_service = get_export_service()
    html_content = export_service.generate_transaction_report_html(
        user_id=filter_user_id,
        start_date=start_date,
        end_date=end_date
    )

    return Response(
        html_content,
        mimetype='text/html',
        headers={'Content-Type': 'text/html; charset=utf-8'}
    )


@api_bp.route('/export/wallet-statement.pdf')
@login_required_api
def export_wallet_statement():
    """Génère un relevé de compte (retourne HTML pour impression)"""
    from flask import Response
    from app.services.export_service import get_export_service

    user_id = session.get('user_id')
    period_days = int(request.args.get('days', 30))

    export_service = get_export_service()
    html_content = export_service.generate_wallet_statement_html(
        user_id=user_id,
        period_days=period_days
    )

    return Response(
        html_content,
        mimetype='text/html',
        headers={'Content-Type': 'text/html; charset=utf-8'}
    )


# ==================== TWO-FACTOR AUTHENTICATION (2FA) API ====================

def get_two_factor_service():
    """Helper pour obtenir le service 2FA"""
    from app.services.two_factor_service import TwoFactorService
    return TwoFactorService()


@api_bp.route('/2fa/status')
@login_required_api
def get_2fa_status():
    """Récupère le statut 2FA de l'utilisateur"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    try:
        service = get_two_factor_service()
        status = service.get_2fa_status(user_id)
        return jsonify({"success": True, "status": status})
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"2FA status error: {e}")
        return jsonify({
            "success": True,
            "status": {
                "enabled": False,
                "backup_codes_remaining": 0,
                "trusted_devices_count": 0
            }
        })


@api_bp.route('/2fa/setup', methods=['POST'])
@login_required_api
def setup_2fa():
    """Démarre le processus de configuration 2FA"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    try:
        service = get_two_factor_service()
        result = service.setup_2fa(user_id)

        if result.get('success'):
            return jsonify({
                "success": True,
                "qr_code": result.get('qr_code'),
                "secret": result.get('manual_entry_key'),
                "uri": result.get('uri')
            })

        return jsonify(result), 400
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"2FA setup error: {e}")
        return jsonify({"success": False, "error": "Erreur lors de la configuration 2FA. Veuillez réessayer."}), 500


@api_bp.route('/2fa/enable', methods=['POST'])
@login_required_api
def enable_2fa():
    """Active le 2FA après vérification du code"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    data = request.get_json() or {}
    code = data.get('code', '').strip()

    if not code:
        return jsonify({"success": False, "error": "Verification code required"}), 400

    service = get_two_factor_service()
    result = service.verify_and_enable_2fa(user_id, code)

    if result.get('success'):
        return jsonify({
            "success": True,
            "message": result.get('message'),
            "backup_codes": result.get('backup_codes')
        })

    return jsonify(result), 400


@api_bp.route('/2fa/disable', methods=['POST'])
@login_required_api
def disable_2fa():
    """Désactive le 2FA"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    data = request.get_json() or {}
    code = data.get('code', '').strip()

    if not code:
        return jsonify({"success": False, "error": "Verification code required"}), 400

    service = get_two_factor_service()
    result = service.disable_2fa(user_id, code)

    if result.get('success'):
        return jsonify(result)

    return jsonify(result), 400


@api_bp.route('/2fa/verify', methods=['POST'])
def verify_2fa_login():
    """Vérifie le code 2FA lors de la connexion"""
    data = request.get_json() or {}

    # L'utilisateur doit avoir passé la première étape d'auth
    pending_user_id = session.get('pending_2fa_user_id')
    if not pending_user_id:
        return jsonify({"success": False, "error": "No pending 2FA verification"}), 400

    code = data.get('code', '').strip()
    remember_device = data.get('remember_device', False)

    if not code:
        return jsonify({"success": False, "error": "Verification code required"}), 400

    # Récupérer les infos de l'appareil
    device_info = {
        'user_agent': request.headers.get('User-Agent', ''),
        'browser': request.headers.get('Sec-CH-UA', ''),
        'os': request.headers.get('Sec-CH-UA-Platform', ''),
        'device_type': 'mobile' if 'Mobile' in request.headers.get('User-Agent', '') else 'desktop'
    }
    ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)

    service = get_two_factor_service()
    result = service.verify_login_2fa(
        pending_user_id,
        code,
        remember_device=remember_device,
        device_info=device_info,
        ip_address=ip_address
    )

    if result.get('success'):
        # Finaliser la connexion
        session['user_id'] = pending_user_id
        session.pop('pending_2fa_user_id', None)

        response_data = {
            "success": True,
            "message": "Login successful",
            "used_backup_code": result.get('used_backup_code', False)
        }

        if result.get('device_token'):
            response_data['device_token'] = result['device_token']

        return jsonify(response_data)

    return jsonify(result), 400


@api_bp.route('/2fa/backup-codes/regenerate', methods=['POST'])
@login_required_api
def regenerate_backup_codes():
    """Régénère les codes de secours"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    data = request.get_json() or {}
    code = data.get('code', '').strip()

    if not code:
        return jsonify({"success": False, "error": "Verification code required"}), 400

    service = get_two_factor_service()
    result = service.regenerate_backup_codes(user_id, code)

    if result.get('success'):
        return jsonify({
            "success": True,
            "backup_codes": result.get('backup_codes'),
            "message": result.get('message')
        })

    return jsonify(result), 400


@api_bp.route('/2fa/devices')
@login_required_api
def get_trusted_devices():
    """Liste les appareils de confiance"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    # Token de l'appareil actuel (depuis cookie)
    current_device_token = request.cookies.get('sarfx_device_token')

    service = get_two_factor_service()
    devices = service.get_trusted_devices(user_id)

    # Marquer l'appareil actuel
    for device in devices:
        if current_device_token and device.get('id'):
            # Comparer les tokens (simplification)
            device['is_current'] = False

    return jsonify({
        "success": True,
        "devices": devices
    })


@api_bp.route('/2fa/devices/<device_id>', methods=['DELETE'])
@login_required_api
def remove_trusted_device(device_id):
    """Supprime un appareil de confiance"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    service = get_two_factor_service()
    result = service.remove_trusted_device(user_id, device_id)

    if result.get('success'):
        return jsonify(result)

    return jsonify(result), 400


@api_bp.route('/2fa/devices', methods=['DELETE'])
@login_required_api
def remove_all_trusted_devices():
    """Supprime tous les appareils de confiance"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    service = get_two_factor_service()
    result = service.remove_all_trusted_devices(user_id)

    if result.get('success'):
        return jsonify(result)

    return jsonify(result), 400


@api_bp.route('/2fa/logs')
@login_required_api
def get_2fa_logs():
    """Récupère les logs 2FA de l'utilisateur"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    limit = request.args.get('limit', 20, type=int)

    service = get_two_factor_service()
    logs = service.get_2fa_logs(user_id, limit)

    return jsonify({
        "success": True,
        "logs": logs
    })


# ==================== LANGUAGE / I18N ====================

def get_i18n_service():
    """Lazy import du service i18n pour éviter les imports circulaires"""
    from app.services.i18n_service import I18nService
    return I18nService()


@api_bp.route('/language')
def get_current_language():
    """Récupère la langue courante de l'utilisateur"""
    i18n = get_i18n_service()
    lang = i18n.get_current_language()
    languages = i18n.get_available_languages()

    return jsonify({
        "success": True,
        "language": lang,
        "languages": languages,
        "is_rtl": i18n.is_rtl(lang)
    })


@api_bp.route('/language/set', methods=['POST'])
def set_language():
    """Change la langue de l'interface"""
    data = request.get_json() or {}
    lang = data.get('language', 'fr')

    i18n = get_i18n_service()

    if not i18n.is_supported_language(lang):
        return jsonify({
            "success": False,
            "error": f"Langue '{lang}' non supportée",
            "supported": list(i18n.get_available_languages().keys())
        }), 400

    # Sauvegarder en session
    i18n.set_language(lang)

    # Sauvegarder en base si utilisateur connecté
    user_id = session.get('user_id')
    if user_id:
        db = get_db()
        if db is not None:
            db.users.update_one(
                {"_id": safe_object_id(user_id)},
                {"$set": {"language": lang}}
            )

    return jsonify({
        "success": True,
        "language": lang,
        "is_rtl": i18n.is_rtl(lang),
        "message": f"Langue changée en {i18n.get_available_languages()[lang]['name']}"
    })


@api_bp.route('/language/translations')
def get_translations():
    """Récupère les traductions pour la langue courante (pour usage JS)"""
    i18n = get_i18n_service()
    lang = request.args.get('lang', i18n.get_current_language())

    translations = i18n.get_translations(lang)

    return jsonify({
        "success": True,
        "language": lang,
        "is_rtl": i18n.is_rtl(lang),
        "translations": translations
    })

# ==================== RATE ALERTS ====================

def get_rate_alert_service():
    """Lazy import du service d'alertes de taux"""
    from app.services.rate_alert_service import RateAlertService
    return RateAlertService()


@api_bp.route('/rate-alerts')
@login_required_api
def get_rate_alerts():
    """Récupère les alertes de taux de l'utilisateur"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    status = request.args.get('status')
    pair = request.args.get('pair')
    limit = request.args.get('limit', 50, type=int)

    service = get_rate_alert_service()
    alerts = service.get_user_alerts(user_id, status=status, pair=pair, limit=limit)

    return jsonify({
        "success": True,
        "alerts": alerts,
        "count": len(alerts)
    })


@api_bp.route('/rate-alerts/<alert_id>')
@login_required_api
def get_rate_alert(alert_id):
    """Récupère une alerte spécifique"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    service = get_rate_alert_service()
    alert = service.get_alert_by_id(user_id, alert_id)

    if alert:
        return jsonify({"success": True, "alert": alert})

    return jsonify({"success": False, "error": "Alerte non trouvée"}), 404


@api_bp.route('/rate-alerts', methods=['POST'])
@login_required_api
def create_rate_alert():
    """Crée une nouvelle alerte de taux"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    data = request.get_json() or {}

    # Validation des champs requis
    required = ['from_currency', 'to_currency', 'alert_type', 'target_rate']
    missing = [f for f in required if not data.get(f)]

    if missing:
        return jsonify({
            "success": False,
            "error": f"Champs requis manquants: {', '.join(missing)}"
        }), 400

    # Parser la date d'expiration si fournie
    expiry_date = None
    if data.get('expiry_date'):
        try:
            expiry_date = datetime.fromisoformat(data['expiry_date'].replace('Z', '+00:00'))
        except:
            pass

    service = get_rate_alert_service()
    result = service.create_alert(
        user_id=user_id,
        from_currency=data['from_currency'],
        to_currency=data['to_currency'],
        alert_type=data['alert_type'],
        target_rate=float(data['target_rate']),
        notification_channels=data.get('notification_channels'),
        expiry_date=expiry_date,
        name=data.get('name'),
        notes=data.get('notes')
    )

    if result.get('success'):
        return jsonify(result), 201

    return jsonify(result), 400


@api_bp.route('/rate-alerts/<alert_id>', methods=['PUT', 'PATCH'])
@login_required_api
def update_rate_alert(alert_id):
    """Met à jour une alerte"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    data = request.get_json() or {}

    service = get_rate_alert_service()
    result = service.update_alert(user_id, alert_id, data)

    if result.get('success'):
        return jsonify(result)

    return jsonify(result), 400


@api_bp.route('/rate-alerts/<alert_id>', methods=['DELETE'])
@login_required_api
def delete_rate_alert(alert_id):
    """Supprime une alerte"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    service = get_rate_alert_service()
    result = service.delete_alert(user_id, alert_id)

    if result.get('success'):
        return jsonify(result)

    return jsonify(result), 404


@api_bp.route('/rate-alerts/<alert_id>/pause', methods=['POST'])
@login_required_api
def pause_rate_alert(alert_id):
    """Met en pause une alerte"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    service = get_rate_alert_service()
    result = service.pause_alert(user_id, alert_id)

    if result.get('success'):
        return jsonify(result)

    return jsonify(result), 400


@api_bp.route('/rate-alerts/<alert_id>/resume', methods=['POST'])
@login_required_api
def resume_rate_alert(alert_id):
    """Réactive une alerte"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    service = get_rate_alert_service()
    result = service.resume_alert(user_id, alert_id)

    if result.get('success'):
        return jsonify(result)

    return jsonify(result), 400


@api_bp.route('/rate-alerts/statistics')
@login_required_api
def get_rate_alert_statistics():
    """Récupère les statistiques des alertes"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    service = get_rate_alert_service()
    stats = service.get_alert_statistics(user_id)

    return jsonify({
        "success": True,
        "statistics": stats
    })


@api_bp.route('/rate-alerts/history')
@login_required_api
def get_rate_alert_history():
    """Récupère l'historique des déclenchements"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    alert_id = request.args.get('alert_id')
    limit = request.args.get('limit', 50, type=int)

    service = get_rate_alert_service()
    history = service.get_trigger_history(user_id, alert_id=alert_id, limit=limit)

    return jsonify({
        "success": True,
        "history": history
    })


@api_bp.route('/rate-alerts/popular-pairs')
def get_popular_pairs():
    """Récupère les paires populaires avec leurs taux"""
    service = get_rate_alert_service()
    pairs = service.get_popular_pairs()

    return jsonify({
        "success": True,
        "pairs": pairs
    })


@api_bp.route('/rate-alerts/suggestions')
@login_required_api
def get_rate_alert_suggestions():
    """Récupère des suggestions d'alertes"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    service = get_rate_alert_service()
    suggestions = service.get_suggested_alerts(user_id)

    return jsonify({
        "success": True,
        "suggestions": suggestions
    })


# ==================== STATS API (PUBLIC) ====================

# Cache pour les stats (5 minutes)
_stats_cache = {}
_stats_cache_ttl = 300  # 5 minutes

@api_bp.route('/stats/counts')
def get_stats_counts():
    """
    Récupère les compteurs dynamiques pour la landing page et dashboards
    Retourne: bank_count, atm_count, user_count, transaction_count
    Mis en cache pour 5 minutes
    """
    cache_key = "stats_counts"

    # Vérifier le cache
    if cache_key in _stats_cache:
        cached = _stats_cache[cache_key]
        if time.time() - cached['timestamp'] < _stats_cache_ttl:
            return jsonify(cached['data'])

    db = get_db()
    if db is None:
        return jsonify({
            "success": False,
            "error": "Database unavailable",
            "bank_count": 6,
            "atm_count": 250
        }), 503

    try:
        # Compter les banques actives
        bank_count = 6  # Valeur par défaut
        if 'banks' in db.list_collection_names():
            bank_count = db.banks.count_documents({"is_active": True})
            if bank_count == 0:
                bank_count = 6  # Fallback si pas de données

        # Compter les ATMs
        atm_count = 0
        if 'atm_locations' in db.list_collection_names():
            atm_count = db.atm_locations.count_documents({})

        # Compter les utilisateurs actifs (optionnel)
        user_count = 0
        if 'users' in db.list_collection_names():
            user_count = db.users.count_documents({"is_active": True})

        # Compter les transactions (optionnel)
        transaction_count = 0
        if 'transactions' in db.list_collection_names():
            transaction_count = db.transactions.count_documents({})

        result = {
            "success": True,
            "bank_count": bank_count,
            "atm_count": atm_count,
            "user_count": user_count,
            "transaction_count": transaction_count,
            "cached_at": datetime.utcnow().isoformat()
        }

        # Mettre en cache
        _stats_cache[cache_key] = {
            'data': result,
            'timestamp': time.time()
        }

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "bank_count": 6,
            "atm_count": 250
        }), 500