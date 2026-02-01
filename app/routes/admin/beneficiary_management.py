from flask import render_template, session, redirect, url_for, flash
from app.routes.admin import admin_bp
from app.decorators import admin_required
from app.services.db_service import get_db, log_history
from bson import ObjectId


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

    return render_template('admin/beneficiaries.html', beneficiaries=all_beneficiaries)


@admin_bp.route('/beneficiaries/<ben_id>/delete', methods=['POST'])
@admin_required
def delete_beneficiary(ben_id):
    db = get_db()
    beneficiary = db.beneficiaries.find_one({"_id": ObjectId(ben_id)})
    if beneficiary:
        db.beneficiaries.delete_one({"_id": ObjectId(ben_id)})
        log_history("BENEFICIARY_DELETE", f"Beneficiaire {beneficiary.get('name', 'N/A')} supprime", user=session.get('email'))
        flash("Beneficiaire supprime", "success")
    return redirect(url_for('admin.beneficiaries'))
