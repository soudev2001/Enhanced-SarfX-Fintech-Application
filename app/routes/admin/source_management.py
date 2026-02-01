from flask import render_template
from app.routes.admin import admin_bp
from app.decorators import admin_required
from app.services.db_service import get_db


@admin_bp.route('/sources')
@admin_required
def sources():
    """List all data sources"""
    db = get_db()

    sources_list = list(db.sources.find().sort('imported_at', -1)) if 'sources' in db.list_collection_names() else []

    return render_template('admin/sources.html', sources=sources_list)
