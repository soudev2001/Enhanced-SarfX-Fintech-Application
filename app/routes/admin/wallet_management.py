from flask import render_template, session, redirect, url_for, request, flash
from app.routes.admin import admin_bp
from app.decorators import admin_required
from app.services.db_service import get_db, log_history
from bson import ObjectId
from datetime import datetime


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

    return render_template('admin/wallets_2026.html', wallets=all_wallets, active_tab='admin_wallets')


@admin_bp.route('/wallets/<wallet_id>/history')
@admin_required
def wallet_history(wallet_id):
    """Recupere l'historique d'un portefeuille (API)"""
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
        flash("Portefeuille non trouve", "error")
        return redirect(url_for('admin.wallets'))

    old_balance = wallet.get('balances', {}).get(currency, 0)
    new_balance = old_balance + amount

    # Verifier si le solde est suffisant pour une soustraction
    if amount < 0 and new_balance < 0:
        flash(f"Solde insuffisant! Le solde actuel en {currency} est {old_balance:.2f}. Vous ne pouvez pas retirer plus de {old_balance:.2f} {currency}.", "error")
        return redirect(url_for('admin.wallets'))

    # Verifier que la devise existe dans le wallet pour une soustraction
    if amount < 0 and old_balance <= 0:
        flash(f"Impossible de soustraire: aucun solde en {currency} disponible.", "error")
        return redirect(url_for('admin.wallets'))

    # Record adjustment
    adjustment_type = "credit" if amount > 0 else "debit"
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
    flash(f"Solde ajuste: {amount:+.2f} {currency} (Nouveau solde: {new_balance:.2f} {currency})", "success")

    return redirect(url_for('admin.wallets'))


@admin_bp.route('/my-wallet')
@admin_required
def admin_my_wallet():
    """Vue du portefeuille de l'administrateur connecte."""
    from app.services.wallet_service import get_total_balance_in_usd, get_user_transactions, get_wallet_by_user_id

    db = get_db()
    admin_id = session.get('user_id')

    # Recuperer l'admin
    admin = None
    try:
        admin = db.users.find_one({"_id": ObjectId(admin_id)})
    except Exception:
        admin = db.users.find_one({"email": session.get('email')})

    # Recuperer ou creer le wallet
    wallet, error = get_wallet_by_user_id(admin_id)

    total_balance, _ = get_total_balance_in_usd(admin_id)
    transactions, _ = get_user_transactions(admin_id, limit=20)

    return render_template('admin/my_wallet_2026.html',
        admin=admin,
        wallet=wallet,
        total_balance=total_balance,
        transactions=transactions
    )
