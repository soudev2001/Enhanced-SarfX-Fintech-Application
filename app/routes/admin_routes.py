from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from app.services.db_service import get_db, log_history
from functools import wraps
from bson import ObjectId
from datetime import datetime

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
    
    # Fetch Stats
    user_count = db.users.count_documents({})
    supplier_count = db.suppliers.count_documents({})
    wallet_count = db.wallets.count_documents({})
    transaction_count = db.transactions.count_documents({})
    
    # Calculate total volume
    pipeline = [
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]
    total_volume = list(db.transactions.aggregate(pipeline))
    volume = total_volume[0]['total'] if total_volume else 0
    
    recent_history = list(db.history.find().sort("timestamp", -1).limit(10))
    recent_transactions = list(db.transactions.find().sort("created_at", -1).limit(5))
    
    return render_template('dashboard.html', 
                         user_count=user_count, 
                         supplier_count=supplier_count,
                         wallet_count=wallet_count,
                         transaction_count=transaction_count,
                         total_volume=volume,
                         history=recent_history,
                         recent_transactions=recent_transactions)

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
