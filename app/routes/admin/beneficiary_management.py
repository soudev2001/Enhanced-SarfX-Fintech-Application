from flask import render_template, session, redirect, url_for, flash, request, jsonify
from app.routes.admin import admin_bp
from app.decorators import admin_required
from app.services.db_service import get_db, log_history
from bson import ObjectId
from datetime import datetime


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

    return render_template('admin/beneficiaries_2026.html', beneficiaries=all_beneficiaries, active_tab='admin_beneficiaries')


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


# ==================== BENEFICIARY KYC & TAGS MANAGEMENT ====================

@admin_bp.route('/beneficiaries/<ben_id>/kyc', methods=['POST'])
@admin_required
def update_beneficiary_kyc(ben_id):
    """Update KYC status for a beneficiary"""
    db = get_db()
    data = request.get_json() or {}

    status = data.get('status', 'none')
    note = data.get('note', '')

    update_data = {
        "kyc_status": status,
        "kyc_updated_at": datetime.utcnow(),
        "kyc_updated_by": session.get('email')
    }

    if note:
        update_data["kyc_note"] = note

    result = db.beneficiaries.update_one(
        {"_id": ObjectId(ben_id)},
        {"$set": update_data}
    )

    if result.modified_count > 0 or result.matched_count > 0:
        log_history("BENEFICIARY_KYC_UPDATE", f"KYC bénéficiaire mis à jour: {status}", user=session.get('email'))
        return jsonify({"success": True, "message": "Statut KYC mis à jour"})

    return jsonify({"success": False, "message": "Erreur lors de la mise à jour"}), 400


@admin_bp.route('/beneficiaries/<ben_id>/tags', methods=['POST'])
@admin_required
def update_beneficiary_tags(ben_id):
    """Update tags for a beneficiary"""
    db = get_db()
    data = request.get_json() or {}

    tags = data.get('tags', [])
    append = data.get('append', False)

    if append:
        # Add tags to existing ones
        result = db.beneficiaries.update_one(
            {"_id": ObjectId(ben_id)},
            {
                "$addToSet": {"tags": {"$each": tags}},
                "$set": {
                    "tags_updated_at": datetime.utcnow(),
                    "tags_updated_by": session.get('email')
                }
            }
        )
    else:
        # Replace tags
        result = db.beneficiaries.update_one(
            {"_id": ObjectId(ben_id)},
            {"$set": {
                "tags": tags,
                "tags_updated_at": datetime.utcnow(),
                "tags_updated_by": session.get('email')
            }}
        )

    if result.modified_count > 0 or result.matched_count > 0:
        log_history("BENEFICIARY_TAGS_UPDATE", f"Tags bénéficiaire mis à jour: {', '.join(tags)}", user=session.get('email'))
        return jsonify({"success": True, "message": "Tags mis à jour"})

    return jsonify({"success": False, "message": "Erreur lors de la mise à jour"}), 400


@admin_bp.route('/beneficiaries/bulk/kyc', methods=['POST'])
@admin_required
def bulk_update_beneficiary_kyc():
    """Bulk update KYC status for beneficiaries"""
    db = get_db()
    data = request.get_json() or {}

    ben_ids = data.get('ids', [])
    status = data.get('status', 'verified')

    if not ben_ids:
        return jsonify({"success": False, "message": "Aucun bénéficiaire sélectionné"}), 400

    object_ids = [ObjectId(bid) for bid in ben_ids]

    result = db.beneficiaries.update_many(
        {"_id": {"$in": object_ids}},
        {"$set": {
            "kyc_status": status,
            "kyc_updated_at": datetime.utcnow(),
            "kyc_updated_by": session.get('email')
        }}
    )

    log_history("BULK_BENEFICIARY_KYC", f"{result.modified_count} bénéficiaires KYC mis à jour: {status}",
               user=session.get('email'))

    return jsonify({
        "success": True,
        "message": f"{result.modified_count} bénéficiaire(s) mis à jour",
        "count": result.modified_count
    })


@admin_bp.route('/beneficiaries/bulk/tags', methods=['POST'])
@admin_required
def bulk_update_beneficiary_tags():
    """Bulk add tags to beneficiaries"""
    db = get_db()
    data = request.get_json() or {}

    ben_ids = data.get('ids', [])
    tags = data.get('tags', [])

    if not ben_ids:
        return jsonify({"success": False, "message": "Aucun bénéficiaire sélectionné"}), 400

    object_ids = [ObjectId(bid) for bid in ben_ids]

    result = db.beneficiaries.update_many(
        {"_id": {"$in": object_ids}},
        {
            "$addToSet": {"tags": {"$each": tags}},
            "$set": {
                "tags_updated_at": datetime.utcnow(),
                "tags_updated_by": session.get('email')
            }
        }
    )

    log_history("BULK_BENEFICIARY_TAGS", f"{result.modified_count} bénéficiaires tags ajoutés: {', '.join(tags)}",
               user=session.get('email'))

    return jsonify({
        "success": True,
        "message": f"Tags ajoutés à {result.modified_count} bénéficiaire(s)",
        "count": result.modified_count
    })
