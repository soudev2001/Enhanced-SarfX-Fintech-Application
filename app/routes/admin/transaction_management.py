from flask import render_template, session, redirect, url_for, request, flash, Response
from app.routes.admin import admin_bp
from app.decorators import admin_required
from app.services.db_service import get_db, log_history
from bson import ObjectId
from datetime import datetime
import csv
import io


@admin_bp.route('/transactions')
@admin_required
def transactions():
    db = get_db()

    # Verifier si la collection existe
    if 'transactions' not in db.list_collection_names():
        return render_template('admin/transactions.html', transactions=[])

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
                if isinstance(user_id_str, str) and len(user_id_str) == 24:
                    user = db.users.find_one({"_id": ObjectId(user_id_str)})
                else:
                    user = db.users.find_one({"_id": user_id_str})
                tx['user_email'] = user.get('email', 'Unknown') if user else 'Unknown'
            else:
                tx['user_email'] = 'Unknown'
        except Exception:
            tx['user_email'] = 'Unknown'

    return render_template('admin/transactions.html', transactions=all_transactions)


@admin_bp.route('/transactions/<tx_id>/status', methods=['POST'])
@admin_required
def update_transaction_status(tx_id):
    db = get_db()
    new_status = request.form.get('status', 'completed')

    db.transactions.update_one(
        {"transaction_id": tx_id},
        {"$set": {"status": new_status, "updated_at": datetime.utcnow()}}
    )

    log_history("TX_STATUS", f"Transaction {tx_id[:8]}... -> {new_status}", user=session.get('email'))
    flash(f"Statut mis a jour: {new_status}", "success")

    return redirect(url_for('admin.transactions'))


# ==================== EXPORT CSV ====================

@admin_bp.route('/export/users')
@admin_required
def export_users():
    db = get_db()
    users = list(db.users.find())

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(['ID', 'Email', 'Role', 'Statut', 'Verifie', 'Date Creation'])

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
    all_transactions = list(db.transactions.find().sort("created_at", -1))

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(['ID Transaction', 'Email User', 'Montant', 'Devise Source', 'Devise Cible', 'Montant Final', 'Taux', 'Statut', 'Date'])

    for tx in all_transactions:
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
