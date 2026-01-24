@app_bp.route('/associate-bank', methods=['GET', 'POST'])
@login_required
def associate_bank():
    """Associer un user banque à une banque et donner accès à l'API banque"""
    user = get_current_user()
    db = get_db()
    banks = list(db.banks.find({"is_active": True})) if db is not None else []
    if request.method == 'POST':
        bank_code = request.form.get('bank_code')
        if bank_code:
            db.users.update_one({"_id": user['_id']}, {"$set": {"bank_code": bank_code, "role": "bank_user"}})
            flash("Association à la banque réussie !", "success")
            return redirect(url_for('app.bank_settings'))
        else:
            flash("Veuillez sélectionner une banque.", "error")
    return render_template('app_associate_bank.html', user=user, banks=banks)
from flask import Blueprint, render_template, session, redirect, url_for, request, flash
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

def role_required(*allowed_roles):
    """Décorateur pour vérifier les rôles utilisateurs"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('auth.login'))
            
            user = get_current_user()
            if not user:
                return redirect(url_for('auth.login'))
            
            user_role = user.get('role', 'user')
            if user_role not in allowed_roles:
                flash('Accès non autorisé', 'error')
                return redirect(url_for('app.home'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

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
    try:
        user = get_current_user()
        if not user:
            return redirect(url_for('auth.login'))
            
        db = get_db()
        
        # Récupérer les bénéficiaires de l'utilisateur
        user_beneficiaries = []
        if db is not None:
            try:
                user_beneficiaries = list(db.beneficiaries.find({"user_id": str(session['user_id'])}))
                
                # Pour chaque bénéficiaire, récupérer son historique de transactions
                for benef in user_beneficiaries:
                    benef['_id'] = str(benef['_id'])
                    benef['transactions'] = list(db.transactions.find({
                        "user_id": str(session['user_id']),
                        "beneficiary_id": benef['_id']
                    }).sort("created_at", -1).limit(5))
            except Exception as e:
                print(f"Erreur lors de la récupération des bénéficiaires: {e}")
                user_beneficiaries = []
        
        return render_template('app_beneficiaries.html',
            active_tab='beneficiaries',
            user=user,
            beneficiaries=user_beneficiaries
        )
    except Exception as e:
        print(f"Erreur dans la route beneficiaries: {e}")
        from flask import flash
        flash('Erreur lors du chargement des bénéficiaires', 'error')
        return redirect(url_for('app.home'))


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


@app_bp.route('/wallets')
@login_required
def wallets():
    """Page des portefeuilles multi-devises"""
    user = get_current_user()
    total_balance = get_user_total_balance(session['user_id'])
    transactions = get_user_transactions(session['user_id'], limit=10)
    
    return render_template('app_wallets.html',
        active_tab='wallets',
        user=user,
        total_balance=total_balance,
        transactions=transactions
    )


@app_bp.route('/atms')
@login_required
def atms():
    """Page de recherche des DABs partenaires"""
    user = get_current_user()
    db = get_db()
    
    banks = []
    cities = set()
    atm_count = 0
    
    if db is not None:
        # Récupérer les banques partenaires avec leurs ATMs
        if 'banks' in db.list_collection_names():
            banks = list(db.banks.find({"is_active": True}))
            for bank in banks:
                bank['_id'] = str(bank['_id'])
                cities.add(bank.get('city', 'Unknown'))
                atm_count += bank.get('atm_count', 0)
    
    return render_template('app_atms.html',
        active_tab='atms',
        user=user,
        banks=banks,
        cities=sorted(list(cities)),
        atm_count=atm_count
    )


@app_bp.route('/faq')
@login_required
def faq():
    """Page des questions fréquentes"""
    user = get_current_user()
    
    return render_template('app_faq.html',
        active_tab='faq',
        user=user
    )


# ==================== ROUTES POUR LES RÔLES ADMINISTRATIFS ====================

@app_bp.route('/admin-sr-bank')
@role_required('admin', 'admin_sr_bank')
def admin_sr_bank():
    """Dashboard pour les administrateurs senior de banque"""
    user = get_current_user()
    db = get_db()
    
    # Statistiques bancaires
    stats = {
        'total_banks': 0,
        'total_atms': 0,
        'total_users': 0,
        'total_transactions': 0,
        'total_volume': 0
    }
    
    if db is not None:
        stats['total_banks'] = db.banks.count_documents({})
        stats['total_atms'] = db.atms.count_documents({}) if 'atms' in db.list_collection_names() else 0
        stats['total_users'] = db.users.count_documents({'role': {'$in': ['user', 'bank_user']}})
        stats['total_transactions'] = db.transactions.count_documents({})
        
        # Calculer le volume total
        transactions = db.transactions.find({'status': 'completed'})
        for tx in transactions:
            stats['total_volume'] += float(tx.get('amount', 0))
    
    return render_template('admin_sr_bank_dashboard.html',
        user=user,
        stats=stats
    )


@app_bp.route('/admin-associate-bank')
@role_required('admin', 'admin_sr_bank', 'admin_associate_bank')
def admin_associate_bank():
    """Dashboard pour les administrateurs associés de banque avec contrôle API"""
    user = get_current_user()
    db = get_db()
    
    # Récupérer la banque associée à l'utilisateur
    user_bank = None
    bank_stats = {
        'atm_count': 0,
        'user_count': 0,
        'transaction_count': 0,
        'api_calls': 0
    }
    
    if db is not None and user.get('bank_code'):
        user_bank = db.banks.find_one({'code': user['bank_code']})
        if user_bank:
            user_bank['_id'] = str(user_bank['_id'])
            bank_stats['atm_count'] = db.atms.count_documents({'bank_code': user['bank_code']}) if 'atms' in db.list_collection_names() else 0
            bank_stats['user_count'] = db.users.count_documents({'bank_code': user['bank_code']})
            bank_stats['transaction_count'] = db.transactions.count_documents({'bank_code': user['bank_code']})
            # En production, récupérer depuis une collection api_logs
            bank_stats['api_calls'] = 0
    
    return render_template('admin_associate_bank_dashboard.html',
        user=user,
        bank=user_bank,
        stats=bank_stats
    )


@app_bp.route('/admin-associate-bank/api-control')
@role_required('admin', 'admin_sr_bank', 'admin_associate_bank')
def admin_api_control():
    """Page de contrôle API pour les administrateurs associés de banque"""
    user = get_current_user()
    db = get_db()
    
    # Récupérer les informations API de la banque
    api_info = {
        'api_key': None,
        'api_secret': None,
        'webhook_url': None,
        'is_active': False,
        'rate_limit': 1000,
        'last_sync': None
    }
    
    if db is not None and user.get('bank_code'):
        bank = db.banks.find_one({'code': user['bank_code']})
        if bank:
            api_info.update({
                'api_key': bank.get('api_key'),
                'api_secret': bank.get('api_secret'),
                'webhook_url': bank.get('webhook_url'),
                'is_active': bank.get('api_active', False),
                'rate_limit': bank.get('api_rate_limit', 1000),
                'last_sync': bank.get('last_api_sync')
            })
    
    return render_template('admin_api_control.html',
        user=user,
        api_info=api_info
    )


@app_bp.route('/admin-associate-bank/atm-management')
@role_required('admin', 'admin_sr_bank', 'admin_associate_bank')
def admin_atm_management():
    """Gestion des ATMs pour les administrateurs de banque"""
    user = get_current_user()
    db = get_db()
    
    atms = []
    if db is not None and user.get('bank_code'):
        if 'atms' in db.list_collection_names():
            atms = list(db.atms.find({'bank_code': user['bank_code']}))
            for atm in atms:
                atm['_id'] = str(atm['_id'])
    
    return render_template('admin_atm_management.html',
        user=user,
        atms=atms
    )

