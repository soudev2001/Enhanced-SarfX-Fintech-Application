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
    """Proxy vers le backend IA pour les prévisions"""
    db = get_db()
    settings = db.settings.find_one({"type": "app"}) if db else {}
    ai_url = settings.get('ai_backend_url', 'https://sarfx-backend-ai-618432953337.europe-west1.run.app')
    
    import requests
    try:
        headers = {
            'ngrok-skip-browser-warning': 'true',
            'Bypass-Tunnel-Reminder': 'true'
        }
        response = requests.get(f"{ai_url}/predict/{pair}", headers=headers, timeout=30)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500
