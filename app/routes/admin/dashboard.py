from flask import render_template, session, request, jsonify
from app.routes.admin import admin_bp
from app.decorators import admin_required
from app.services.db_service import get_db, log_history
from bson import ObjectId
from datetime import datetime, timedelta


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

    return render_template('admin/dashboard.html',
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
    return render_template('common/dashboard.html', mode='history', logs=logs)


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
