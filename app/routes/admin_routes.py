from flask import Blueprint, render_template, session, redirect, url_for, request, flash, jsonify, Response
from app.services.db_service import get_db, log_history
from functools import wraps
from bson import ObjectId
from datetime import datetime, timedelta
import csv
import io

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
        user = db.users.find_one({"_id": ObjectId(session['user_id'])})
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
        user = db.users.find_one({"_id": ObjectId(wallet['user_id'])}) if wallet.get('user_id') else None
        wallet['user_email'] = user['email'] if user else 'Unknown'
    
    return render_template('admin_wallets.html', wallets=all_wallets)

@admin_bp.route('/wallets/<wallet_id>/adjust', methods=['POST'])
@admin_required
def adjust_wallet(wallet_id):
    db = get_db()
    currency = request.form.get('currency', 'USD')
    amount = float(request.form.get('amount', 0))
    reason = request.form.get('reason', '')
    
    wallet = db.wallets.find_one({"wallet_id": wallet_id})
    if wallet:
        old_balance = wallet.get('balances', {}).get(currency, 0)
        new_balance = old_balance + amount
        
        # Record adjustment
        db.wallet_adjustments.insert_one({
            "wallet_id": wallet_id,
            "user_id": wallet['user_id'],
            "currency": currency,
            "old_balance": old_balance,
            "new_balance": new_balance,
            "difference": amount,
            "admin_id": session['user_id'],
            "reason": reason,
            "created_at": datetime.utcnow()
        })
        
        # Update balance
        db.wallets.update_one(
            {"wallet_id": wallet_id},
            {"$set": {f"balances.{currency}": new_balance, "updated_at": datetime.utcnow()}}
        )
        
        log_history("WALLET_ADJUST", f"Ajustement {amount} {currency} sur wallet {wallet_id[:8]}...", 
                   user=session.get('email'))
        flash(f"Solde ajusté: {amount:+.2f} {currency}", "success")
    
    return redirect(url_for('admin.wallets'))


# ==================== TRANSACTIONS MANAGEMENT ====================

@admin_bp.route('/transactions')
@admin_required
def transactions():
    db = get_db()
    
    # Filtres
    status = request.args.get('status')
    user_id = request.args.get('user_id')
    
    query = {}
    if status:
        query['status'] = status
    if user_id:
        query['user_id'] = user_id
    
    all_transactions = list(db.transactions.find(query).sort("created_at", -1).limit(100))
    
    # Enrichir avec les infos utilisateur
    for tx in all_transactions:
        user = db.users.find_one({"_id": ObjectId(tx['user_id'])}) if tx.get('user_id') else None
        tx['user_email'] = user['email'] if user else 'Unknown'
    
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
