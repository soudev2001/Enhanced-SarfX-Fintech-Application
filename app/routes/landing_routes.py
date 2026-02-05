"""
Landing Page Routes
Public routes for the landing page (home, about, contact, services)
"""

from flask import Blueprint, render_template, send_from_directory, current_app, make_response
import os
from app.services.db_service import get_db

landing_bp = Blueprint('landing', __name__)


@landing_bp.route('/sw.js')
def service_worker():
    """Serve the Service Worker from root path with proper headers"""
    response = make_response(
        send_from_directory(
            os.path.join(current_app.root_path, 'static', 'js'),
            'sw.js',
            mimetype='application/javascript'
        )
    )
    # Allow the SW to control the entire site
    response.headers['Service-Worker-Allowed'] = '/'
    response.headers['Cache-Control'] = 'no-cache'
    return response


def get_platform_stats():
    """Get dynamic stats for landing page with fallback values"""
    db = get_db()
    stats = {
        'bank_count': 6,
        'atm_count': 250,
        'user_count': 1000,
        'transaction_count': 50000
    }

    if db is None:
        return stats

    try:
        # Count active banks
        if 'banks' in db.list_collection_names():
            count = db.banks.count_documents({"is_active": True})
            if count > 0:
                stats['bank_count'] = count

        # Count ATMs
        if 'atm_locations' in db.list_collection_names():
            stats['atm_count'] = db.atm_locations.count_documents({})

        # Count active users
        if 'users' in db.list_collection_names():
            stats['user_count'] = db.users.count_documents({"is_active": True})

        # Count transactions
        if 'transactions' in db.list_collection_names():
            stats['transaction_count'] = db.transactions.count_documents({})
    except Exception:
        pass  # Use fallback values

    return stats


@landing_bp.route('/')
def home():
    """Landing page - Home"""
    stats = get_platform_stats()
    return render_template('landing_new.html', **stats)


@landing_bp.route('/about')
def about():
    """About page - redirect to landing with anchor"""
    stats = get_platform_stats()
    return render_template('landing.html', **stats)


@landing_bp.route('/contact')
def contact():
    """Contact page - redirect to landing with anchor"""
    stats = get_platform_stats()
    return render_template('landing.html', **stats)


@landing_bp.route('/services')
def services():
    """Services page - redirect to landing with anchor"""
    stats = get_platform_stats()
    return render_template('landing.html', **stats)
