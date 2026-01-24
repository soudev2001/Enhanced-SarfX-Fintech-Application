"""
Landing Page Routes
Public routes for the landing page (home, about, contact, services)
"""

from flask import Blueprint, render_template

landing_bp = Blueprint('landing', __name__)


@landing_bp.route('/')
def home():
    """Landing page - Home"""
    return render_template('landing.html')


@landing_bp.route('/about')
def about():
    """About page - redirect to landing with anchor"""
    return render_template('landing.html')


@landing_bp.route('/contact')
def contact():
    """Contact page - redirect to landing with anchor"""
    return render_template('landing.html')


@landing_bp.route('/services')
def services():
    """Services page - redirect to landing with anchor"""
    return render_template('landing.html')
