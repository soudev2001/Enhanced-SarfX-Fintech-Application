from functools import wraps
from flask import session, redirect, url_for, flash, jsonify
from app.services.db_service import get_db, safe_object_id


def login_required(f):
    """Decorator to protect routes - requires authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator to protect admin routes - requires admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        db = get_db()
        user_id = safe_object_id(session['user_id'])
        user = db.users.find_one({"_id": user_id}) if user_id else db.users.find_one({"email": session.get('email')})
        if not user or user.get('role') != 'admin':
            flash("Acces non autorise", "error")
            return redirect(url_for('app.home'))
        return f(*args, **kwargs)
    return decorated_function


def role_required(*allowed_roles):
    """Decorator to check user roles"""
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
                flash('Acces non autorise', 'error')
                return redirect(url_for('app.home'))

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def login_required_api(f):
    """Decorator to protect API routes - returns JSON 401"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"error": "Non authentifie"}), 401
        return f(*args, **kwargs)
    return decorated_function


def get_current_user():
    """Get the currently logged-in user from session"""
    if 'user_id' not in session:
        return None
    db = get_db()
    if db is None:
        return None
    from bson import ObjectId
    from bson.errors import InvalidId
    try:
        user_id = session['user_id']
        if isinstance(user_id, ObjectId):
            return db.users.find_one({"_id": user_id})
        return db.users.find_one({"_id": ObjectId(user_id)})
    except (InvalidId, TypeError):
        return db.users.find_one({"email": session.get('email')}) or None


def get_user_wallet(user_id):
    """Get user wallet by user_id"""
    db = get_db()
    if db is None:
        return None
    return db.wallets.find_one({"user_id": str(user_id)})
