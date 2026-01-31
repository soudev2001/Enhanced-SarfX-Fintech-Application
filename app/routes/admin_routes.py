from flask import Blueprint, render_template, session, redirect, url_for, request, flash, jsonify, Response
from app.services.db_service import get_db, log_history
from app.services.atm_service import ATMService
from functools import wraps
from bson import ObjectId
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import csv
import io
import os
import json

admin_bp = Blueprint('admin', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        db = get_db()
        from app.services.db_service import safe_object_id
        user_id = safe_object_id(session['user_id'])
        user = db.users.find_one({"_id": user_id}) if user_id else db.users.find_one({"email": session.get('email')})
        if not user or user.get('role') != 'admin':
            flash("Accès non autorisé", "error")
            return redirect(url_for('app.home'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
@admin_required
def dashboard():
    db = get_db()

    # Basic Stats
    user_count = db.users.count_documents({})
    supplier_count = db.suppliers.count_documents({})
    wallet_count = db.wallets.count_documents({})
    transaction_count = db.transactions.count_documents({})
    beneficiary_count = db.beneficiaries.count_documents({}) if 'beneficiaries' in db.list_collection_names() else 0

    # Today's stats
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    new_users_today = db.users.count_documents({"created_at": {"$gte": today}})
    today_transactions = db.transactions.count_documents({"created_at": {"$gte": today}})

    # Calculate total volume
    pipeline = [
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]
    total_volume = list(db.transactions.aggregate(pipeline))
    volume = total_volume[0]['total'] if total_volume else 0

    # Volume data for chart (last 7 days)
    volume_data = []
    volume_labels = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        next_day = day + timedelta(days=1)
        day_volume = list(db.transactions.aggregate([
            {"$match": {"created_at": {"$gte": day, "$lt": next_day}}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]))
        volume_data.append(day_volume[0]['total'] if day_volume else 0)
        volume_labels.append(day.strftime('%d/%m'))

    # Currency distribution
    currency_pipeline = [
        {"$group": {"_id": "$from_currency", "count": {"$sum": 1}}}
    ]
    currency_stats = list(db.transactions.aggregate(currency_pipeline))
    currency_data = {item['_id']: item['count'] for item in currency_stats if item['_id']}

    # Recent data
    recent_history = list(db.history.find().sort("timestamp", -1).limit(10))
    recent_transactions = list(db.transactions.find().sort("created_at", -1).limit(5))
    recent_users = list(db.users.find().sort("created_at", -1).limit(5))

    # Enrich transactions with user email
    for tx in recent_transactions:
        user = db.users.find_one({"_id": ObjectId(tx['user_id'])}) if tx.get('user_id') else None
        tx['user_email'] = user['email'] if user else 'Unknown'

    return render_template('admin_dashboard.html',
                         user_count=user_count,
                         supplier_count=supplier_count,
                         wallet_count=wallet_count,
                         transaction_count=transaction_count,
                         beneficiary_count=beneficiary_count,
                         total_volume=volume,
                         new_users_today=new_users_today,
                         today_transactions=today_transactions,
                         volume_data=volume_data,
                         volume_labels=volume_labels,
                         currency_data=currency_data,
                         history=recent_history,
                         recent_transactions=recent_transactions,
                         recent_users=recent_users)

@admin_bp.route('/history')
@admin_required
def history():
    db = get_db()
    logs = list(db.history.find().sort("timestamp", -1).limit(100))
    return render_template('dashboard.html', mode='history', logs=logs)


# ==================== USERS MANAGEMENT ====================

@admin_bp.route('/users')
@admin_required
def users():
    db = get_db()
    all_users = list(db.users.find().sort("email", 1))
    return render_template('admin_users.html', users=all_users)

@admin_bp.route('/users/<user_id>/toggle', methods=['POST'])
@admin_required
def toggle_user(user_id):
    db = get_db()
    user = db.users.find_one({"_id": ObjectId(user_id)})
    if user:
        new_status = not user.get('is_active', True)
        db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"is_active": new_status}}
        )
        log_history("USER_TOGGLE", f"Utilisateur {user['email']} {'activé' if new_status else 'désactivé'}",
                   user=session.get('email'))
        flash(f"Utilisateur {'activé' if new_status else 'désactivé'}", "success")
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/<user_id>/role', methods=['POST'])
@admin_required
def change_role(user_id):
    db = get_db()
    new_role = request.form.get('role', 'user')
    db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"role": new_role}}
    )
    log_history("USER_ROLE", f"Rôle modifié à {new_role}", user=session.get('email'))
    flash(f"Rôle modifié en {new_role}", "success")
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/<user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    db = get_db()
    user = db.users.find_one({"_id": ObjectId(user_id)})
    if user:
        # Don't allow deleting yourself
        if str(user['_id']) == session['user_id']:
            flash("Vous ne pouvez pas supprimer votre propre compte", "error")
            return redirect(url_for('admin.users'))

        db.users.delete_one({"_id": ObjectId(user_id)})
        db.wallets.delete_many({"user_id": user_id})
        log_history("USER_DELETE", f"Utilisateur {user['email']} supprimé", user=session.get('email'))
        flash("Utilisateur supprimé", "success")
    return redirect(url_for('admin.users'))


# ==================== WALLETS MANAGEMENT ====================

@admin_bp.route('/wallets')
@admin_required
def wallets():
    db = get_db()
    all_wallets = list(db.wallets.find())

    # Enrichir avec les infos utilisateur
    for wallet in all_wallets:
        try:
            user_id = wallet.get('user_id')
            if user_id:
                if isinstance(user_id, str) and len(user_id) == 24:
                    user = db.users.find_one({"_id": ObjectId(user_id)})
                else:
                    user = db.users.find_one({"_id": user_id})
                wallet['user_email'] = user.get('email', 'Unknown') if user else 'Unknown'
            else:
                wallet['user_email'] = 'Unknown'
        except Exception:
            wallet['user_email'] = 'Unknown'

    return render_template('admin_wallets.html', wallets=all_wallets)


@admin_bp.route('/wallets/<wallet_id>/history')
@admin_required
def wallet_history(wallet_id):
    """Récupère l'historique d'un portefeuille (API)"""
    from app.services.wallet_service import get_wallet_history

    history = get_wallet_history(wallet_id, limit=100)

    # Enrichir avec les infos admin
    db = get_db()
    for item in history:
        admin_id = item.get('admin_id')
        if admin_id:
            try:
                if isinstance(admin_id, str) and len(admin_id) == 24:
                    admin = db.users.find_one({"_id": ObjectId(admin_id)})
                else:
                    admin = db.users.find_one({"_id": admin_id})
                item['admin_email'] = admin.get('email', 'Unknown') if admin else 'System'
            except:
                item['admin_email'] = 'System'
        else:
            item['admin_email'] = 'System'

        # Formater les dates
        if 'created_at' in item:
            item['created_at'] = item['created_at'].isoformat()

    return {'history': history}


@admin_bp.route('/wallets/<wallet_id>/adjust', methods=['POST'])
@admin_required
def adjust_wallet(wallet_id):
    db = get_db()
    currency = request.form.get('currency', 'USD')
    amount = float(request.form.get('amount', 0))
    reason = request.form.get('reason', '')

    wallet = db.wallets.find_one({"wallet_id": wallet_id})
    if not wallet:
        flash("Portefeuille non trouvé", "error")
        return redirect(url_for('admin.wallets'))

    old_balance = wallet.get('balances', {}).get(currency, 0)
    new_balance = old_balance + amount

    # Vérifier si le solde est suffisant pour une soustraction
    if amount < 0 and new_balance < 0:
        flash(f"Solde insuffisant! Le solde actuel en {currency} est {old_balance:.2f}. Vous ne pouvez pas retirer plus de {old_balance:.2f} {currency}.", "error")
        return redirect(url_for('admin.wallets'))

    # Vérifier que la devise existe dans le wallet pour une soustraction
    if amount < 0 and old_balance <= 0:
        flash(f"Impossible de soustraire: aucun solde en {currency} disponible.", "error")
        return redirect(url_for('admin.wallets'))

    # Record adjustment
    adjustment_type = "crédit" if amount > 0 else "débit"
    db.wallet_adjustments.insert_one({
        "wallet_id": wallet_id,
        "user_id": wallet['user_id'],
        "currency": currency,
        "old_balance": old_balance,
        "new_balance": new_balance,
        "difference": amount,
        "type": adjustment_type,
        "admin_id": session['user_id'],
        "reason": reason,
        "created_at": datetime.utcnow()
    })

    # Update balance
    db.wallets.update_one(
        {"wallet_id": wallet_id},
        {"$set": {f"balances.{currency}": new_balance, "updated_at": datetime.utcnow()}}
    )

    log_history("WALLET_ADJUST", f"Ajustement {amount:+.2f} {currency} sur wallet {wallet_id[:8]}... ({adjustment_type})",
               user=session.get('email'))
    flash(f"Solde ajusté: {amount:+.2f} {currency} (Nouveau solde: {new_balance:.2f} {currency})", "success")

    return redirect(url_for('admin.wallets'))


@admin_bp.route('/my-wallet')
@admin_required
def admin_my_wallet():
    """Vue du portefeuille de l'administrateur connecté."""
    from app.services.wallet_service import get_total_balance_in_usd, get_user_transactions, get_wallet_by_user_id

    db = get_db()
    admin_id = session.get('user_id')

    # Récupérer l'admin
    admin = None
    try:
        admin = db.users.find_one({"_id": ObjectId(admin_id)})
    except Exception:
        admin = db.users.find_one({"email": session.get('email')})

    # Récupérer ou créer le wallet
    wallet, error = get_wallet_by_user_id(admin_id)

    total_balance, _ = get_total_balance_in_usd(admin_id)
    transactions, _ = get_user_transactions(admin_id, limit=20)

    return render_template('admin_my_wallet.html',
        admin=admin,
        wallet=wallet,
        total_balance=total_balance,
        transactions=transactions
    )


# ==================== TRANSACTIONS MANAGEMENT ====================

@admin_bp.route('/transactions')
@admin_required
def transactions():
    db = get_db()

    # Vérifier si la collection existe
    if 'transactions' not in db.list_collection_names():
        return render_template('admin_transactions.html', transactions=[])

    # Filtres
    status = request.args.get('status')
    user_id = request.args.get('user_id')

    query = {}
    if status:
        query['status'] = status
    if user_id:
        query['user_id'] = user_id

    try:
        all_transactions = list(db.transactions.find(query).sort("created_at", -1).limit(100))
    except Exception as e:
        print(f"Erreur transactions: {e}")
        all_transactions = []

    # Enrichir avec les infos utilisateur
    for tx in all_transactions:
        try:
            user_id_str = tx.get('user_id')
            if user_id_str:
                # Essayer de convertir en ObjectId si c'est une chaîne valide
                if isinstance(user_id_str, str) and len(user_id_str) == 24:
                    user = db.users.find_one({"_id": ObjectId(user_id_str)})
                else:
                    user = db.users.find_one({"_id": user_id_str})
                tx['user_email'] = user.get('email', 'Unknown') if user else 'Unknown'
            else:
                tx['user_email'] = 'Unknown'
        except Exception:
            tx['user_email'] = 'Unknown'

    return render_template('admin_transactions.html', transactions=all_transactions)

@admin_bp.route('/transactions/<tx_id>/status', methods=['POST'])
@admin_required
def update_transaction_status(tx_id):
    db = get_db()
    new_status = request.form.get('status', 'completed')

    db.transactions.update_one(
        {"transaction_id": tx_id},
        {"$set": {"status": new_status, "updated_at": datetime.utcnow()}}
    )

    log_history("TX_STATUS", f"Transaction {tx_id[:8]}... → {new_status}", user=session.get('email'))
    flash(f"Statut mis à jour: {new_status}", "success")

    return redirect(url_for('admin.transactions'))


# ==================== BENEFICIARIES MANAGEMENT ====================

@admin_bp.route('/beneficiaries')
@admin_required
def beneficiaries():
    db = get_db()

    # Get all beneficiaries with user info
    all_beneficiaries = list(db.beneficiaries.find().sort("created_at", -1)) if 'beneficiaries' in db.list_collection_names() else []

    # Enrich with user email
    for ben in all_beneficiaries:
        user = db.users.find_one({"_id": ObjectId(ben['user_id'])}) if ben.get('user_id') else None
        ben['owner_email'] = user['email'] if user else 'Unknown'

    return render_template('admin_beneficiaries.html', beneficiaries=all_beneficiaries)


@admin_bp.route('/beneficiaries/<ben_id>/delete', methods=['POST'])
@admin_required
def delete_beneficiary(ben_id):
    db = get_db()
    beneficiary = db.beneficiaries.find_one({"_id": ObjectId(ben_id)})
    if beneficiary:
        db.beneficiaries.delete_one({"_id": ObjectId(ben_id)})
        log_history("BENEFICIARY_DELETE", f"Bénéficiaire {beneficiary.get('name', 'N/A')} supprimé", user=session.get('email'))
        flash("Bénéficiaire supprimé", "success")
    return redirect(url_for('admin.beneficiaries'))


# ==================== EXPORT CSV ====================

@admin_bp.route('/export/users')
@admin_required
def export_users():
    db = get_db()
    users = list(db.users.find())

    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow(['ID', 'Email', 'Rôle', 'Statut', 'Vérifié', 'Date Création'])

    # Data
    for user in users:
        writer.writerow([
            str(user['_id']),
            user.get('email', ''),
            user.get('role', 'user'),
            'Actif' if user.get('is_active', True) else 'Inactif',
            'Oui' if user.get('verified', False) else 'Non',
            user.get('created_at', '').strftime('%d/%m/%Y %H:%M') if user.get('created_at') else ''
        ])

    output.seek(0)

    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=sarfx_users_{datetime.now().strftime("%Y%m%d")}.csv'}
    )


@admin_bp.route('/export/transactions')
@admin_required
def export_transactions():
    db = get_db()
    transactions = list(db.transactions.find().sort("created_at", -1))

    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow(['ID Transaction', 'Email User', 'Montant', 'Devise Source', 'Devise Cible', 'Montant Final', 'Taux', 'Statut', 'Date'])

    # Data
    for tx in transactions:
        user = db.users.find_one({"_id": ObjectId(tx['user_id'])}) if tx.get('user_id') else None
        writer.writerow([
            tx.get('transaction_id', ''),
            user['email'] if user else 'Unknown',
            tx.get('amount', 0),
            tx.get('from_currency', ''),
            tx.get('to_currency', ''),
            tx.get('final_amount', 0),
            tx.get('rate', 0),
            tx.get('status', ''),
            tx.get('created_at', '').strftime('%d/%m/%Y %H:%M') if tx.get('created_at') else ''
        ])

    output.seek(0)

    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=sarfx_transactions_{datetime.now().strftime("%Y%m%d")}.csv'}
    )


# ==================== API ENDPOINTS FOR DASHBOARD ====================

@admin_bp.route('/api/volume-data')
@admin_required
def api_volume_data():
    """Get volume data for chart"""
    db = get_db()
    days = int(request.args.get('days', 7))

    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    volume_data = []
    volume_labels = []

    for i in range(days - 1, -1, -1):
        day = today - timedelta(days=i)
        next_day = day + timedelta(days=1)
        day_volume = list(db.transactions.aggregate([
            {"$match": {"created_at": {"$gte": day, "$lt": next_day}}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]))
        volume_data.append(day_volume[0]['total'] if day_volume else 0)
        volume_labels.append(day.strftime('%d/%m'))

    return jsonify({
        "values": volume_data,
        "labels": volume_labels
    })


@admin_bp.route('/api/notifications')
@admin_required
def api_notifications():
    """Get new notifications since timestamp"""
    db = get_db()
    since = request.args.get('since')

    if since:
        since_time = datetime.fromtimestamp(int(since) / 1000)
    else:
        since_time = datetime.utcnow() - timedelta(minutes=1)

    # Count new transactions
    new_transactions = db.transactions.count_documents({"created_at": {"$gte": since_time}})

    # Count new users
    new_users = db.users.count_documents({"created_at": {"$gte": since_time}})

    return jsonify({
        "new_transactions": new_transactions,
        "new_users": new_users,
        "timestamp": datetime.utcnow().isoformat()
    })


@admin_bp.route('/api/user/<user_id>/details')
@admin_required
def api_user_details(user_id):
    """Get detailed user information"""
    db = get_db()

    user = db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Get user's wallet
    wallet = db.wallets.find_one({"user_id": user_id})

    # Get user's transactions
    transactions = list(db.transactions.find({"user_id": user_id}).sort("created_at", -1).limit(10))

    # Get user's beneficiaries
    beneficiaries = list(db.beneficiaries.find({"user_id": user_id})) if 'beneficiaries' in db.list_collection_names() else []

    return jsonify({
        "user": {
            "id": str(user['_id']),
            "email": user.get('email'),
            "role": user.get('role', 'user'),
            "is_active": user.get('is_active', True),
            "verified": user.get('verified', False),
            "created_at": user.get('created_at').isoformat() if user.get('created_at') else None
        },
        "wallet": {
            "balances": wallet.get('balances', {}) if wallet else {},
            "wallet_id": wallet.get('wallet_id') if wallet else None
        },
        "transactions_count": len(transactions),
        "recent_transactions": [{
            "id": tx.get('transaction_id'),
            "amount": tx.get('amount'),
            "from": tx.get('from_currency'),
            "to": tx.get('to_currency'),
            "status": tx.get('status'),
            "date": tx.get('created_at').isoformat() if tx.get('created_at') else None
        } for tx in transactions],
        "beneficiaries_count": len(beneficiaries)
    })


# ==================== ATM MANAGEMENT ====================

# Configuration for photo uploads
UPLOAD_FOLDER = 'app/static/images/atms'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Moroccan cities list for forms
MOROCCAN_CITIES = [
    "Casablanca", "Rabat", "Marrakech", "Fès", "Tanger", "Agadir", "Meknès", "Oujda",
    "Kenitra", "Tétouan", "El Jadida", "Safi", "Mohammedia", "Béni Mellal", "Nador",
    "Khouribga", "Settat", "Taza", "Errachidia", "Essaouira", "Khémisset", "Larache",
    "Ksar El Kébir", "Guelmim", "Ouarzazate", "Al Hoceima", "Berkane", "Taourirt",
    "Dakhla", "Laayoune", "Tan-Tan", "Tiznit", "Taroudant", "Chefchaouen", "Ifrane", "Azrou"
]


# ==================== ATM MANAGEMENT ====================

@admin_bp.route('/atms')
@admin_required
def atms():
    """List all ATMs with filtering and pagination"""
    db = get_db()
    atm_service = ATMService(db)

    # Pagination
    page = int(request.args.get('page', 1))
    per_page = 20
    skip = (page - 1) * per_page

    # Filters
    bank_filter = request.args.get('bank', '')
    city_filter = request.args.get('city', '')
    status_filter = request.args.get('status', '')
    search_query = request.args.get('q', '')

    # Build query
    query = {}
    if bank_filter:
        query['bank_code'] = bank_filter
    if city_filter:
        query['city'] = city_filter
    if status_filter:
        query['status'] = status_filter
    if search_query:
        query['$or'] = [
            {'name': {'$regex': search_query, '$options': 'i'}},
            {'address': {'$regex': search_query, '$options': 'i'}},
            {'atm_id': {'$regex': search_query, '$options': 'i'}}
        ]

    # Get ATMs
    total_atms = db.atm_locations.count_documents(query)
    atms_list = list(db.atm_locations.find(query).skip(skip).limit(per_page).sort("created_at", -1))
    total_pages = (total_atms + per_page - 1) // per_page

    # Get banks for filter
    banks = atm_service.get_all_banks()
    banks_dict = {bank['code']: bank for bank in banks}

    # Get cities for filter
    cities = atm_service.get_cities_with_atms()

    return render_template('admin_atms.html',
                         atms=atms_list,
                         banks=banks,
                         banks_dict=banks_dict,
                         cities=cities,
                         total_atms=total_atms,
                         page=page,
                         total_pages=total_pages,
                         selected_bank=bank_filter)


@admin_bp.route('/atms/dashboard')
@admin_required
def atm_dashboard():
    """ATM Analytics Dashboard"""
    db = get_db()
    atm_service = ATMService(db)

    # Basic stats
    total_atms = db.atm_locations.count_documents({})
    active_atms = db.atm_locations.count_documents({'status': 'active'})
    inactive_atms = db.atm_locations.count_documents({'status': {'$ne': 'active'}})

    # Banks data
    banks = atm_service.get_all_banks()
    banks_stats = []
    banks_chart_data = {'labels': [], 'values': [], 'colors': []}

    for bank in banks:
        count = bank.get('atm_count', 0)
        percent = round((count / total_atms * 100), 1) if total_atms > 0 else 0
        banks_stats.append({
            'name': bank['name'],
            'code': bank['code'],
            'color': bank.get('color', '#666'),
            'count': count,
            'percent': percent
        })
        banks_chart_data['labels'].append(bank['name'].split()[0])
        banks_chart_data['values'].append(count)
        banks_chart_data['colors'].append(bank.get('color', '#666'))

    # Cities data
    cities = atm_service.get_cities_with_atms()[:10]
    cities_chart_data = {
        'labels': [c['city'] for c in cities],
        'values': [c['atm_count'] for c in cities]
    }

    # Location type distribution
    location_pipeline = [
        {'$group': {'_id': '$location_type', 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}}
    ]
    location_types = list(db.atm_locations.aggregate(location_pipeline))
    location_type_data = {
        'labels': [lt['_id'] or 'Unknown' for lt in location_types],
        'values': [lt['count'] for lt in location_types]
    }

    # Services stats
    services_config = {
        'withdrawal': {'icon': 'banknote', 'color': '#22c55e'},
        'deposit': {'icon': 'wallet', 'color': '#3b82f6'},
        'balance': {'icon': 'eye', 'color': '#8b5cf6'},
        'transfer': {'icon': 'arrow-left-right', 'color': '#f59e0b'},
        'bill_payment': {'icon': 'receipt', 'color': '#ec4899'},
        'mobile_topup': {'icon': 'smartphone', 'color': '#06b6d4'}
    }

    services_stats = {}
    for svc, config in services_config.items():
        count = db.atm_locations.count_documents({'services': svc})
        percent = round((count / total_atms * 100), 1) if total_atms > 0 else 0
        services_stats[svc] = {
            'count': count,
            'percent': percent,
            'icon': config['icon'],
            'color': config['color']
        }

    # Accessibility stats
    wheelchair_count = db.atm_locations.count_documents({'has_wheelchair_access': True})
    nfc_count = db.atm_locations.count_documents({'has_nfc': True})
    deposit_count = db.atm_locations.count_documents({'has_deposit': True})
    atm_24h_count = db.atm_locations.count_documents({'available_24h': True})

    wheelchair_percent = round((wheelchair_count / total_atms * 100), 1) if total_atms > 0 else 0
    nfc_percent = round((nfc_count / total_atms * 100), 1) if total_atms > 0 else 0
    deposit_percent = round((deposit_count / total_atms * 100), 1) if total_atms > 0 else 0
    atm_24h_percent = round((atm_24h_count / total_atms * 100), 1) if total_atms > 0 else 0

    # Sources
    sources = list(db.sources.find().sort('imported_at', -1).limit(5)) if 'sources' in db.list_collection_names() else []

    return render_template('admin_atm_dashboard.html',
                         total_atms=total_atms,
                         active_atms=active_atms,
                         inactive_atms=inactive_atms,
                         banks=banks,
                         banks_stats=banks_stats,
                         banks_chart_data=json.dumps(banks_chart_data),
                         cities=cities,
                         cities_chart_data=json.dumps(cities_chart_data),
                         location_type_data=json.dumps(location_type_data),
                         services_stats=services_stats,
                         wheelchair_percent=wheelchair_percent,
                         nfc_percent=nfc_percent,
                         deposit_percent=deposit_percent,
                         atm_24h_percent=atm_24h_percent,
                         sources=sources)


@admin_bp.route('/atms/add', methods=['GET', 'POST'])
@admin_required
def add_atm():
    """Add new ATM"""
    db = get_db()
    atm_service = ATMService(db)

    if request.method == 'POST':
        # Get form data
        atm_data = {
            'bank_code': request.form.get('bank_code'),
            'name': request.form.get('name'),
            'address': request.form.get('address'),
            'city': request.form.get('city'),
            'district': request.form.get('district', ''),
            'location': {
                'type': 'Point',
                'coordinates': [
                    float(request.form.get('longitude', 0)),
                    float(request.form.get('latitude', 0))
                ]
            },
            'location_type': request.form.get('location_type', 'branch'),
            'services': request.form.getlist('services'),
            'available_24h': 'available_24h' in request.form,
            'hours': request.form.get('hours') if 'available_24h' not in request.form else None,
            'has_wheelchair_access': 'has_wheelchair_access' in request.form,
            'has_nfc': 'has_nfc' in request.form,
            'has_deposit': 'has_deposit' in request.form,
            'has_audio': 'has_audio' in request.form,
            'status': 'active',
            'photos': []
        }

        # Handle photo uploads
        if 'photos' in request.files:
            photos = request.files.getlist('photos')
            for photo in photos[:5]:  # Max 5 photos
                if photo and allowed_file(photo.filename):
                    filename = secure_filename(f"{atm_data['bank_code']}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{photo.filename}")

                    # Create directory if not exists
                    upload_path = os.path.join(UPLOAD_FOLDER, atm_data['bank_code'])
                    os.makedirs(upload_path, exist_ok=True)

                    filepath = os.path.join(upload_path, filename)
                    photo.save(filepath)
                    atm_data['photos'].append(f"/static/images/atms/{atm_data['bank_code']}/{filename}")

        # Add ATM
        result = atm_service.add_atm(atm_data)

        if result:
            log_history("ATM_CREATE", f"ATM {result.get('atm_id')} créé à {atm_data['city']}", user=session.get('email'))
            flash(f"ATM créé avec succès: {result.get('atm_id')}", "success")
            return redirect(url_for('admin.atms'))
        else:
            flash("Erreur lors de la création de l'ATM", "error")

    banks = atm_service.get_all_banks()
    return render_template('admin_atm_form.html', atm=None, banks=banks, cities=MOROCCAN_CITIES)


@admin_bp.route('/atms/<atm_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_atm(atm_id):
    """Edit existing ATM"""
    db = get_db()
    atm_service = ATMService(db)

    atm = atm_service.get_atm_by_id(atm_id)
    if not atm:
        flash("ATM non trouvé", "error")
        return redirect(url_for('admin.atms'))

    if request.method == 'POST':
        update_data = {
            'bank_code': request.form.get('bank_code'),
            'name': request.form.get('name'),
            'address': request.form.get('address'),
            'city': request.form.get('city'),
            'district': request.form.get('district', ''),
            'location': {
                'type': 'Point',
                'coordinates': [
                    float(request.form.get('longitude', 0)),
                    float(request.form.get('latitude', 0))
                ]
            },
            'location_type': request.form.get('location_type', 'branch'),
            'services': request.form.getlist('services'),
            'available_24h': 'available_24h' in request.form,
            'hours': request.form.get('hours') if 'available_24h' not in request.form else None,
            'has_wheelchair_access': 'has_wheelchair_access' in request.form,
            'has_nfc': 'has_nfc' in request.form,
            'has_deposit': 'has_deposit' in request.form,
            'has_audio': 'has_audio' in request.form,
            'status': request.form.get('status', 'active')
        }

        # Handle removed photos
        remove_photos = request.form.getlist('remove_photos')
        current_photos = atm.get('photos', [])
        update_data['photos'] = [p for p in current_photos if p not in remove_photos]

        # Handle new photo uploads
        if 'photos' in request.files:
            photos = request.files.getlist('photos')
            for photo in photos:
                if photo and photo.filename and allowed_file(photo.filename):
                    filename = secure_filename(f"{update_data['bank_code']}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{photo.filename}")

                    upload_path = os.path.join(UPLOAD_FOLDER, update_data['bank_code'])
                    os.makedirs(upload_path, exist_ok=True)

                    filepath = os.path.join(upload_path, filename)
                    photo.save(filepath)
                    update_data['photos'].append(f"/static/images/atms/{update_data['bank_code']}/{filename}")

        if atm_service.update_atm(atm_id, update_data):
            log_history("ATM_UPDATE", f"ATM {atm_id} modifié", user=session.get('email'))
            flash("ATM mis à jour avec succès", "success")
            return redirect(url_for('admin.atms'))
        else:
            flash("Erreur lors de la mise à jour", "error")

    banks = atm_service.get_all_banks()
    return render_template('admin_atm_form.html', atm=atm, banks=banks, cities=MOROCCAN_CITIES)


@admin_bp.route('/atms/<atm_id>/view')
@admin_required
def view_atm(atm_id):
    """View ATM details"""
    db = get_db()
    atm_service = ATMService(db)

    atm = atm_service.get_atm_by_id(atm_id)
    if not atm:
        flash("ATM non trouvé", "error")
        return redirect(url_for('admin.atms'))

    # Get bank info
    bank = atm_service.get_bank_by_code(atm.get('bank_code'))

    return render_template('admin_atm_view.html', atm=atm, bank=bank)


@admin_bp.route('/atms/<atm_id>/toggle', methods=['POST'])
@admin_required
def toggle_atm(atm_id):
    """Toggle ATM status"""
    db = get_db()

    atm = db.atm_locations.find_one({'atm_id': atm_id})
    if atm:
        new_status = 'inactive' if atm.get('status') == 'active' else 'active'
        db.atm_locations.update_one(
            {'atm_id': atm_id},
            {'$set': {'status': new_status, 'updated_at': datetime.now()}}
        )
        log_history("ATM_TOGGLE", f"ATM {atm_id} → {new_status}", user=session.get('email'))
        return jsonify({'success': True, 'new_status': new_status})

    return jsonify({'success': False, 'error': 'ATM non trouvé'}), 404


@admin_bp.route('/atms/<atm_id>/delete', methods=['POST'])
@admin_required
def delete_atm(atm_id):
    """Delete ATM (soft delete)"""
    db = get_db()
    atm_service = ATMService(db)

    if atm_service.delete_atm(atm_id):
        log_history("ATM_DELETE", f"ATM {atm_id} supprimé", user=session.get('email'))
        flash("ATM supprimé", "success")
    else:
        flash("Erreur lors de la suppression", "error")

    return redirect(url_for('admin.atms'))


@admin_bp.route('/atms/bulk', methods=['POST'])
@admin_required
def bulk_atm_action():
    """Bulk actions on ATMs"""
    db = get_db()

    data = request.get_json()
    action = data.get('action')
    atm_ids = data.get('atm_ids', [])

    if not atm_ids:
        return jsonify({'success': False, 'error': 'No ATMs selected'}), 400

    if action == 'activate':
        db.atm_locations.update_many(
            {'atm_id': {'$in': atm_ids}},
            {'$set': {'status': 'active', 'updated_at': datetime.now()}}
        )
        log_history("ATM_BULK_ACTIVATE", f"{len(atm_ids)} ATMs activés", user=session.get('email'))

    elif action == 'deactivate':
        db.atm_locations.update_many(
            {'atm_id': {'$in': atm_ids}},
            {'$set': {'status': 'inactive', 'updated_at': datetime.now()}}
        )
        log_history("ATM_BULK_DEACTIVATE", f"{len(atm_ids)} ATMs désactivés", user=session.get('email'))

    elif action == 'delete':
        db.atm_locations.update_many(
            {'atm_id': {'$in': atm_ids}},
            {'$set': {'status': 'deleted', 'deleted_at': datetime.now()}}
        )
        log_history("ATM_BULK_DELETE", f"{len(atm_ids)} ATMs supprimés", user=session.get('email'))

    else:
        return jsonify({'success': False, 'error': 'Invalid action'}), 400

    return jsonify({'success': True, 'count': len(atm_ids)})


@admin_bp.route('/atms/export')
@admin_required
def export_atms():
    """Export ATMs to CSV"""
    db = get_db()

    # Get filter params
    bank_filter = request.args.get('bank', '')
    city_filter = request.args.get('city', '')

    query = {'status': {'$ne': 'deleted'}}
    if bank_filter:
        query['bank_code'] = bank_filter
    if city_filter:
        query['city'] = city_filter

    atms = list(db.atm_locations.find(query))

    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        'ATM ID', 'Banque', 'Nom', 'Adresse', 'Ville', 'District',
        'Latitude', 'Longitude', 'Type', 'Services', 'Statut',
        '24h', 'Horaires', 'Accès PMR', 'NFC', 'Date création'
    ])

    # Data
    for atm in atms:
        coords = atm.get('location', {}).get('coordinates', [0, 0])
        writer.writerow([
            atm.get('atm_id', ''),
            atm.get('bank_code', ''),
            atm.get('name', ''),
            atm.get('address', ''),
            atm.get('city', ''),
            atm.get('district', ''),
            coords[1] if len(coords) > 1 else 0,
            coords[0] if len(coords) > 0 else 0,
            atm.get('location_type', ''),
            ','.join(atm.get('services', [])),
            atm.get('status', ''),
            'Oui' if atm.get('available_24h') else 'Non',
            atm.get('hours', ''),
            'Oui' if atm.get('has_wheelchair_access') else 'Non',
            'Oui' if atm.get('has_nfc') else 'Non',
            atm.get('created_at', '').strftime('%d/%m/%Y') if atm.get('created_at') else ''
        ])

    output.seek(0)

    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=sarfx_atms_{datetime.now().strftime("%Y%m%d")}.csv'}
    )


@admin_bp.route('/atms/import', methods=['GET', 'POST'])
@admin_required
def import_atms():
    """Import ATMs from CSV"""
    db = get_db()

    if request.method == 'POST':
        if 'file' not in request.files:
            flash("Aucun fichier sélectionné", "error")
            return redirect(url_for('admin.import_atms'))

        file = request.files['file']
        if file.filename == '':
            flash("Aucun fichier sélectionné", "error")
            return redirect(url_for('admin.import_atms'))

        if file and file.filename.endswith('.csv'):
            try:
                stream = io.StringIO(file.stream.read().decode('utf-8'))
                reader = csv.DictReader(stream)

                # Create source record
                source_id = f"SRC_IMPORT_{datetime.now().strftime('%Y%m%d%H%M%S')}"

                imported = 0
                errors = 0

                for row in reader:
                    try:
                        atm_data = {
                            'atm_id': row.get('ATM ID') or f"ATM_{row.get('Banque', 'UNK')}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{imported}",
                            'bank_code': row.get('Banque', ''),
                            'name': row.get('Nom', ''),
                            'address': row.get('Adresse', ''),
                            'city': row.get('Ville', ''),
                            'district': row.get('District', ''),
                            'location': {
                                'type': 'Point',
                                'coordinates': [
                                    float(row.get('Longitude', 0) or 0),
                                    float(row.get('Latitude', 0) or 0)
                                ]
                            },
                            'location_type': row.get('Type', 'branch'),
                            'services': row.get('Services', 'withdrawal,balance').split(','),
                            'status': row.get('Statut', 'active'),
                            'available_24h': row.get('24h', '').lower() == 'oui',
                            'hours': row.get('Horaires', ''),
                            'has_wheelchair_access': row.get('Accès PMR', '').lower() == 'oui',
                            'has_nfc': row.get('NFC', '').lower() == 'oui',
                            'source_id': source_id,
                            'created_at': datetime.now()
                        }

                        db.atm_locations.insert_one(atm_data)
                        imported += 1
                    except Exception as e:
                        errors += 1
                        print(f"Error importing row: {e}")

                # Record source
                db.sources.insert_one({
                    'source_id': source_id,
                    'type': 'csv_import',
                    'name': f"Import CSV - {file.filename}",
                    'total_atms': imported,
                    'errors': errors,
                    'imported_at': datetime.now(),
                    'imported_by': session.get('email'),
                    'status': 'completed'
                })

                log_history("ATM_IMPORT", f"{imported} ATMs importés depuis {file.filename}", user=session.get('email'))
                flash(f"{imported} ATMs importés avec succès ({errors} erreurs)", "success")
                return redirect(url_for('admin.atms'))

            except Exception as e:
                flash(f"Erreur lors de l'import: {str(e)}", "error")
        else:
            flash("Format de fichier invalide (CSV requis)", "error")

    return render_template('admin_atm_import.html')


# ==================== SOURCES MANAGEMENT ====================

@admin_bp.route('/sources')
@admin_required
def sources():
    """List all data sources"""
    db = get_db()

    sources_list = list(db.sources.find().sort('imported_at', -1)) if 'sources' in db.list_collection_names() else []

    return render_template('admin_sources.html', sources=sources_list)


# ==================== DEMO AUTOMATION ====================

@admin_bp.route('/demo')
@admin_required
def demo_page():
    """Page de démonstration automatisée avec Robot Framework"""
    db = get_db()

    # Récupérer les résultats des dernières démos
    demo_results = []
    demo_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'robot_results', 'demo')
    video_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'robot_results', 'videos')

    # Lister les rapports existants
    if os.path.exists(demo_dir):
        for f in sorted(os.listdir(demo_dir), reverse=True):
            if f.startswith('report-') and f.endswith('.html'):
                timestamp = f.replace('report-', '').replace('.html', '')
                demo_results.append({
                    'timestamp': timestamp,
                    'report_file': f,
                    'log_file': f.replace('report-', 'log-'),
                })

    # Dernière vidéo
    latest_video = None
    if os.path.exists(video_dir):
        videos = [f for f in os.listdir(video_dir) if f.endswith('.mp4')]
        if videos:
            latest_video = sorted(videos, reverse=True)[0]

    # Compter les screenshots
    screenshot_count = 0
    if os.path.exists(demo_dir):
        screenshot_count = len([f for f in os.listdir(demo_dir) if f.endswith('.png')])

    return render_template('admin_demo.html',
                         demo_results=demo_results[:10],
                         latest_video=latest_video,
                         screenshot_count=screenshot_count)


@admin_bp.route('/demo/run', methods=['POST'])
@admin_required
def run_demo():
    """Lance la démonstration Robot Framework en arrière-plan"""
    import subprocess
    import threading
    import shutil

    # Vérifier les prérequis
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    script_path = os.path.join(base_dir, 'run_demo_robot.sh')
    robot_tests_dir = os.path.join(base_dir, 'robot_tests')

    # Vérifier si le script existe
    if not os.path.exists(script_path):
        return jsonify({
            'success': False,
            'message': 'Script run_demo_robot.sh non trouvé. La démo doit être exécutée localement.'
        }), 400

    # Vérifier si robot est installé
    robot_installed = shutil.which('robot') is not None
    if not robot_installed:
        # Vérifier dans le venv
        try:
            result = subprocess.run(['python', '-c', 'import robot'], capture_output=True)
            robot_installed = result.returncode == 0
        except:
            pass

    if not robot_installed:
        return jsonify({
            'success': False,
            'message': 'Robot Framework non installé. Installez avec: pip install robotframework robotframework-seleniumlibrary'
        }), 400

    # Vérifier Chrome/Chromium
    chrome_path = shutil.which('google-chrome') or shutil.which('chromium') or shutil.which('chromium-browser')
    if not chrome_path:
        return jsonify({
            'success': False,
            'message': 'Chrome/Chromium non trouvé. La démo nécessite un navigateur Chrome.'
        }), 400

    # Créer le dossier de résultats
    demo_dir = os.path.join(base_dir, 'robot_results', 'demo')
    os.makedirs(demo_dir, exist_ok=True)

    def run_demo_thread():
        try:
            # Exécuter le script
            subprocess.run(
                ['bash', script_path, '--headless'],
                cwd=base_dir,
                timeout=600,  # 10 minutes max
                capture_output=True
            )
        except subprocess.TimeoutExpired:
            print("Demo timeout after 10 minutes")
        except Exception as e:
            print(f"Demo error: {e}")

    # Lancer dans un thread
    thread = threading.Thread(target=run_demo_thread, daemon=True)
    thread.start()

    log_history("DEMO_STARTED", "Démonstration Robot Framework lancée", user=session.get('email'))

    return jsonify({
        'success': True,
        'message': 'Démonstration lancée en arrière-plan'
    })


@admin_bp.route('/demo/status')
@admin_required
def demo_status():
    """Vérifie le statut de la dernière démo"""
    import subprocess

    # Vérifier si un processus robot est en cours
    try:
        result = subprocess.run(['pgrep', '-f', 'robot'], capture_output=True, text=True)
        is_running = result.returncode == 0
    except:
        is_running = False

    # Récupérer les derniers résultats
    demo_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'robot_results', 'demo')

    latest_report = None
    screenshot_count = 0

    if os.path.exists(demo_dir):
        reports = [f for f in os.listdir(demo_dir) if f.startswith('report-') and f.endswith('.html')]
        if reports:
            latest_report = sorted(reports, reverse=True)[0]
        screenshot_count = len([f for f in os.listdir(demo_dir) if f.endswith('.png')])

    return jsonify({
        'running': is_running,
        'latest_report': latest_report,
        'screenshot_count': screenshot_count
    })


@admin_bp.route('/demo/screenshots')
@admin_required
def demo_screenshots():
    """Liste les screenshots de la démo"""
    demo_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'robot_results', 'demo')

    screenshots = []
    if os.path.exists(demo_dir):
        for f in sorted(os.listdir(demo_dir)):
            if f.endswith('.png'):
                screenshots.append({
                    'name': f,
                    'path': f'/admin/demo/screenshot/{f}'
                })

    return jsonify(screenshots)


@admin_bp.route('/demo/screenshot/<filename>')
@admin_required
def get_demo_screenshot(filename):
    """Retourne un screenshot de la démo"""
    from flask import send_from_directory

    demo_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'robot_results', 'demo')

    # Sécurité: vérifier que le fichier est bien un PNG
    if not filename.endswith('.png') or '..' in filename:
        return "Invalid file", 400

    return send_from_directory(demo_dir, filename)


@admin_bp.route('/demo/video')
@admin_required
def get_demo_video():
    """Retourne la dernière vidéo de démo"""
    from flask import send_from_directory

    video_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'robot_results', 'videos')

    if os.path.exists(os.path.join(video_dir, 'demo_latest.mp4')):
        return send_from_directory(video_dir, 'demo_latest.mp4')

    return "No video available", 404


@admin_bp.route('/demo/report')
@admin_required
def get_demo_report():
    """Retourne le dernier rapport HTML"""
    from flask import send_from_directory

    demo_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'robot_results', 'demo')

    if os.path.exists(demo_dir):
        reports = [f for f in os.listdir(demo_dir) if f.startswith('report') and f.endswith('.html')]
        if reports:
            latest = sorted(reports, reverse=True)[0]
            return send_from_directory(demo_dir, latest)

    return "No report available", 404


# ==================== PLAYWRIGHT DEMO ROUTES ====================

@admin_bp.route('/demo/playwright/run/<role>', methods=['POST'])
@admin_required
def run_playwright_demo(role):
    """Lance une démo Playwright pour un rôle spécifique"""
    from app.services.demo_service import run_demo_async, check_playwright_installed, init_demo_dirs

    # Vérifier que le rôle est valide
    if role not in ['admin', 'bank', 'user']:
        return jsonify({'success': False, 'message': 'Rôle invalide'}), 400

    # Vérifier Playwright
    pw_check = check_playwright_installed()
    if not pw_check['installed']:
        return jsonify({
            'success': False,
            'message': 'Playwright non installé. Exécutez: pip install playwright && playwright install chromium'
        }), 400

    if not pw_check['browsers_installed']:
        return jsonify({
            'success': False,
            'message': 'Navigateurs Playwright non installés. Exécutez: playwright install chromium'
        }), 400

    # Initialiser les dossiers
    init_demo_dirs()

    # Lancer la démo
    headless = request.json.get('headless', True) if request.is_json else True
    started = run_demo_async(role, headless=headless)

    if not started:
        return jsonify({
            'success': False,
            'message': f'Une démo {role} est déjà en cours'
        }), 409

    log_history("PLAYWRIGHT_DEMO_STARTED", f"Démo Playwright {role} lancée", user=session.get('email'))

    return jsonify({
        'success': True,
        'message': f'Démo {role} lancée en arrière-plan',
        'role': role
    })


@admin_bp.route('/demo/playwright/status')
@admin_required
def get_playwright_demo_status():
    """Récupère le statut de toutes les démos Playwright"""
    from app.services.demo_service import get_all_demo_statuses

    return jsonify(get_all_demo_statuses())


@admin_bp.route('/demo/playwright/status/<role>')
@admin_required
def get_playwright_demo_status_role(role):
    """Récupère le statut d'une démo spécifique"""
    from app.services.demo_service import get_demo_status

    if role not in ['admin', 'bank', 'user']:
        return jsonify({'error': 'Rôle invalide'}), 400

    return jsonify(get_demo_status(role))


@admin_bp.route('/demo/playwright/videos')
@admin_required
def get_playwright_videos():
    """Liste toutes les vidéos de démo Playwright"""
    from app.services.demo_service import get_demo_videos

    return jsonify(get_demo_videos())


@admin_bp.route('/demo/video/<filename>')
@admin_required
def serve_demo_video(filename):
    """Sert une vidéo de démo"""
    from flask import send_from_directory

    # Sécurité
    if '..' in filename or not (filename.endswith('.mp4') or filename.endswith('.webm')):
        return "Invalid file", 400

    # Essayer les deux dossiers possibles
    video_dirs = [
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'robot_results', 'playwright', 'videos'),
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'robot_results', 'videos')
    ]

    for video_dir in video_dirs:
        filepath = os.path.join(video_dir, filename)
        if os.path.exists(filepath):
            return send_from_directory(video_dir, filename)

    return "Video not found", 404


@admin_bp.route('/demo/playwright/screenshots')
@admin_required
def get_playwright_screenshots():
    """Liste les screenshots des démos Playwright"""
    from app.services.demo_service import get_demo_screenshots

    role = request.args.get('role')
    return jsonify(get_demo_screenshots(role))


@admin_bp.route('/demo/playwright/screenshot/<filename>')
@admin_required
def serve_playwright_screenshot(filename):
    """Sert un screenshot de démo Playwright"""
    from flask import send_from_directory

    if '..' in filename or not filename.endswith('.png'):
        return "Invalid file", 400

    screenshot_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        'robot_results', 'playwright', 'screenshots'
    )

    if os.path.exists(os.path.join(screenshot_dir, filename)):
        return send_from_directory(screenshot_dir, filename)

    return "Screenshot not found", 404


@admin_bp.route('/demo/playwright/check')
@admin_required
def check_playwright():
    """Vérifie l'installation de Playwright"""
    from app.services.demo_service import check_playwright_installed

    return jsonify(check_playwright_installed())


@admin_bp.route('/demo/download-script')
@admin_required
def download_demo_script():
    """Télécharge le script de démo Playwright standalone pour exécution locale"""
    from flask import Response

    # Récupérer l'URL de base de l'app
    base_url = request.host_url.rstrip('/')

    script_content = f'''#!/usr/bin/env python3
"""
SarfX Demo Robot - Script standalone pour exécution locale
Généré depuis {base_url}

Usage:
    python sarfx_demo.py --role admin --visible
    python sarfx_demo.py --role bank --visible
    python sarfx_demo.py --role user --visible
    python sarfx_demo.py --role admin --headless

Prérequis:
    pip install playwright
    playwright install chromium
"""
import argparse
import time
import os
from datetime import datetime

# Configuration
BASE_URL = "{base_url}"
DEMO_ACCOUNTS = {{
    'admin': {{'email': 'admin@sarfx.io', 'password': 'Admin123!'}},
    'bank': {{'email': 'bank@sarfx.io', 'password': 'Bank123!'}},
    'user': {{'email': 'user@sarfx.io', 'password': 'User123!'}}
}}

# Scénarios de navigation pour chaque rôle
SCENARIOS = {{
    'admin': [
        ('/', 'Accueil SarfX'),
        ('/login', 'Connexion'),
        ('/app', 'Dashboard App'),
        ('/admin', 'Dashboard Admin'),
        ('/admin/users', 'Gestion Utilisateurs'),
        ('/admin/banks', 'Gestion Banques'),
        ('/admin/atms', 'Gestion ATMs'),
        ('/app/transactions', 'Historique Transactions'),
    ],
    'bank': [
        ('/', 'Accueil SarfX'),
        ('/login', 'Connexion'),
        ('/app', 'Dashboard App'),
        ('/app/bank/settings', 'Configuration Banque'),
        ('/app/bank/atms', 'ATMs de la Banque'),
        ('/app/converter', 'Convertisseur'),
        ('/app/wallets', 'Wallets'),
    ],
    'user': [
        ('/', 'Accueil SarfX'),
        ('/login', 'Connexion'),
        ('/app', 'Dashboard App'),
        ('/app/wallets', 'Mes Wallets'),
        ('/app/converter', 'Convertisseur'),
        ('/app/atms', 'Trouver ATMs'),
        ('/app/beneficiaries', 'Bénéficiaires'),
        ('/app/transactions', 'Historique'),
        ('/app/ai-forecast', 'IA Prédictions'),
        ('/app/faq', 'FAQ'),
    ]
}}


def run_demo(role: str, headless: bool = False):
    """Exécute la démo pour un rôle donné"""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("❌ Playwright non installé. Exécutez:")
        print("   pip install playwright")
        print("   playwright install chromium")
        return

    account = DEMO_ACCOUNTS.get(role)
    scenario = SCENARIOS.get(role)

    if not account or not scenario:
        print(f"❌ Rôle invalide: {{role}}")
        return

    print(f"🎬 Démarrage de la démo {{role.upper()}}...")
    print(f"   Mode: {{'headless' if headless else 'visible'}}")
    print(f"   URL: {{BASE_URL}}")
    print()

    # Dossier de sortie
    output_dir = os.path.join(os.getcwd(), 'sarfx_demo_output')
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    video_path = os.path.join(output_dir, f'demo_{{role}}_{{timestamp}}')

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            slow_mo=300  # Ralentir pour mieux voir
        )

        context = browser.new_context(
            viewport={{'width': 1920, 'height': 1080}},
            record_video_dir=video_path,
            record_video_size={{'width': 1920, 'height': 1080}}
        )

        page = context.new_page()

        try:
            # Login
            print(f"🔐 Connexion en tant que {{account['email']}}...")
            page.goto(f"{{BASE_URL}}/login")
            time.sleep(1)

            # Remplir le formulaire
            page.fill('input[name="email"], input[type="email"]', account['email'])
            page.fill('input[name="password"], input[type="password"]', account['password'])
            page.click('button[type="submit"]')
            time.sleep(2)

            print("✅ Connecté!")
            print()

            # Parcourir le scénario
            for path, description in scenario:
                if path == '/login':
                    continue  # Déjà fait

                print(f"📍 {{description}}...")
                url = f"{{BASE_URL}}{{path}}"
                page.goto(url)
                time.sleep(2)

                # Screenshot
                screenshot_path = os.path.join(output_dir, f'{{role}}_{{path.replace("/", "_")}}.png')
                page.screenshot(path=screenshot_path)

                # Scroll pour montrer le contenu
                page.evaluate('window.scrollTo(0, document.body.scrollHeight / 2)')
                time.sleep(1)

            print()
            print("✅ Démo terminée!")

        finally:
            context.close()
            browser.close()

    # Trouver la vidéo générée
    for f in os.listdir(video_path):
        if f.endswith('.webm'):
            final_video = os.path.join(output_dir, f'demo_{{role}}_{{timestamp}}.webm')
            os.rename(os.path.join(video_path, f), final_video)
            print(f"🎥 Vidéo: {{final_video}}")
            break

    print(f"📁 Screenshots: {{output_dir}}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='SarfX Demo Robot')
    parser.add_argument('--role', choices=['admin', 'bank', 'user'], required=True,
                        help='Rôle à démontrer')
    parser.add_argument('--visible', action='store_true',
                        help='Mode visible (ouvre le navigateur)')
    parser.add_argument('--headless', action='store_true',
                        help='Mode headless (invisible)')

    args = parser.parse_args()

    headless = args.headless or not args.visible
    run_demo(args.role, headless=headless)
'''

    response = Response(
        script_content,
        mimetype='text/x-python',
        headers={'Content-Disposition': 'attachment;filename=sarfx_demo.py'}
    )
    return response
