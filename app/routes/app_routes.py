from flask import Blueprint, render_template, session, redirect, url_for
from functools import wraps
from app.services.db_service import get_db

app_bp = Blueprint('app', __name__)

def login_required(f):
    """Décorateur pour protéger les routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    """Récupère l'utilisateur connecté"""
    if 'user_id' not in session:
        return None
    db = get_db()
    if db is None:
        return None
    from bson import ObjectId
    return db.users.find_one({"_id": ObjectId(session['user_id'])})

def get_user_wallet(user_id):
    """Récupère le portefeuille de l'utilisateur"""
    db = get_db()
    if db is None:
        return None
    return db.wallets.find_one({"user_id": str(user_id)})

def get_user_total_balance(user_id):
    """Récupère le solde total de tous les wallets de l'utilisateur (converti en USD)"""
    db = get_db()
    if db is None:
        return {"total_usd": 0, "wallets": []}
    
    # Récupérer le wallet de l'utilisateur (format: {balances: {USD: x, EUR: y, ...}})
    wallet = db.wallets.find_one({"user_id": str(user_id)})
    
    if not wallet:
        return {"total_usd": 0, "wallets": []}
    
    # Taux de change approximatifs (devrait venir de l'API en production)
    exchange_rates = {
        "USD": 1.0,
        "EUR": 1.08,
        "MAD": 0.10,
        "GBP": 1.27,
        "CHF": 1.13
    }
    
    total_usd = 0
    wallet_details = []
    
    # Le wallet contient un dict 'balances' avec les devises comme clés
    balances = wallet.get('balances', {})
    
    for currency, balance in balances.items():
        balance = float(balance or 0)
        rate = exchange_rates.get(currency, 1.0)
        usd_value = balance * rate
        total_usd += usd_value
        
        wallet_details.append({
            "currency": currency,
            "balance": balance,
            "usd_value": usd_value
        })
    
    return {
        "total_usd": round(total_usd, 2),
        "wallets": wallet_details
    }

def get_user_transactions(user_id, limit=10):
    """Récupère les transactions de l'utilisateur"""
    db = get_db()
    if db is None:
        return []
    return list(db.transactions.find({"user_id": str(user_id)}).sort("created_at", -1).limit(limit))

def get_suppliers():
    """Récupère tous les fournisseurs actifs"""
    db = get_db()
    if db is None:
        return []
    suppliers = list(db.suppliers.find({"is_active": True}))
    # Convert ObjectId to string for JSON serialization
    for s in suppliers:
        s['_id'] = str(s['_id'])
    return suppliers

def get_settings():
    """Récupère les paramètres de l'application"""
    db = get_db()
    if db is None:
        return {}
    settings = db.settings.find_one({"type": "app"})
    return settings or {}


@app_bp.route('/')
@login_required
def home():
    """Page d'accueil de l'application"""
    user = get_current_user()
    wallet = get_user_wallet(session['user_id'])
    transactions = get_user_transactions(session['user_id'], limit=3)
    
    # Calculer le solde total de tous les wallets
    total_balance = get_user_total_balance(session['user_id'])
    
    db = get_db()
    suppliers_count = db.suppliers.count_documents({"is_active": True}) if db is not None else 0
    
    # Récupérer les banques partenaires actives
    banks = []
    if db is not None and 'banks' in db.list_collection_names():
        banks = list(db.banks.find({"is_active": True}).limit(10))
    
    return render_template('app_home.html', 
        active_tab='home',
        user=user,
        wallet=wallet,
        total_balance=total_balance,
        transactions=transactions,
        suppliers_count=suppliers_count,
        banks=banks
    )


@app_bp.route('/converter')
@login_required
def converter():
    """Page du convertisseur"""
    user = get_current_user()
    suppliers = get_suppliers()
    
    # S'il n'y a pas de fournisseurs, en créer quelques-uns par défaut
    if not suppliers:
        db = get_db()
        if db is not None:
            default_suppliers = [
                {
                    "name": "Binance P2P",
                    "type": "crypto",
                    "rate": 10.12,
                    "fee": 0,
                    "logo": "https://cryptologos.cc/logos/binance-coin-bnb-logo.png?v=026",
                    "is_active": True
                },
                {
                    "name": "Banque Populaire",
                    "type": "bank",
                    "rate": 9.85,
                    "fee": 20,
                    "logo": "https://upload.wikimedia.org/wikipedia/fr/2/22/Logo_Banque_Populaire.png",
                    "is_active": True
                },
                {
                    "name": "Western Union",
                    "type": "transfer",
                    "rate": 9.95,
                    "fee": 15,
                    "logo": "https://www.westernunion.com/content/dam/wu/jm/logos/wu_logo.svg",
                    "is_active": True
                }
            ]
            db.suppliers.insert_many(default_suppliers)
            suppliers = get_suppliers()
    
    return render_template('app_converter.html',
        active_tab='converter',
        user=user,
        suppliers=suppliers
    )


@app_bp.route('/ai')
@login_required
def ai_forecast():
    """Page des prévisions IA"""
    user = get_current_user()
    settings = get_settings()
    
    return render_template('app_ai.html',
        active_tab='ai',
        user=user,
        ai_backend_url=settings.get('ai_backend_url', 'https://sarfx-backend-ai-618432953337.europe-west1.run.app')
    )


@app_bp.route('/profile')
@login_required
def profile():
    """Page du profil utilisateur"""
    user = get_current_user()
    wallet = get_user_wallet(session['user_id'])
    transactions = get_user_transactions(session['user_id'], limit=5)
    
    return render_template('app_profile.html',
        active_tab='profile',
        user=user,
        wallet=wallet,
        transactions=transactions
    )


@app_bp.route('/settings')
@login_required
def settings():
    """Page des réglages"""
    user = get_current_user()
    app_settings = get_settings()
    
    return render_template('app_settings.html',
        active_tab='settings',
        user=user,
        settings=app_settings
    )


@app_bp.route('/transactions')
@login_required
def transactions():
    """Page de l'historique des transactions"""
    user = get_current_user()
    all_transactions = get_user_transactions(session['user_id'], limit=50)
    
    return render_template('app_transactions.html',
        active_tab='transactions',
        user=user,
        transactions=all_transactions
    )


@app_bp.route('/beneficiaries')
@login_required
def beneficiaries():
    """Page des bénéficiaires et leur historique"""
    user = get_current_user()
    db = get_db()
    
    # Récupérer les bénéficiaires de l'utilisateur
    user_beneficiaries = []
    if db is not None:
        user_beneficiaries = list(db.beneficiaries.find({"user_id": str(session['user_id'])}))
        
        # Pour chaque bénéficiaire, récupérer son historique de transactions
        for benef in user_beneficiaries:
            benef['_id'] = str(benef['_id'])
            benef['transactions'] = list(db.transactions.find({
                "user_id": str(session['user_id']),
                "beneficiary_id": benef['_id']
            }).sort("created_at", -1).limit(5))
    
    return render_template('app_beneficiaries.html',
        active_tab='beneficiaries',
        user=user,
        beneficiaries=user_beneficiaries
    )


@app_bp.route('/bank-settings')
@login_required
def bank_settings():
    """Page de configuration API pour les responsables banque"""
    user = get_current_user()
    
    # Vérifier que l'utilisateur est bank_respo
    if user.get('role') != 'bank_respo':
        return redirect(url_for('app.home'))
    
    db = get_db()
    bank = None
    if db is not None:
        # Récupérer la banque associée à ce responsable
        bank_code = user.get('bank_code')
        if bank_code:
            bank = db.banks.find_one({"code": bank_code})
    
    return render_template('app_bank_settings.html',
        active_tab='bank_settings',
        user=user,
        bank=bank
    )
