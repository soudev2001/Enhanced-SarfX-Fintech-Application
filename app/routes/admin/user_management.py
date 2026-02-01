from flask import render_template, session, redirect, url_for, request, flash, jsonify
from app.routes.admin import admin_bp
from app.decorators import admin_required
from app.services.db_service import get_db, log_history, safe_object_id
from bson import ObjectId
from datetime import datetime


@admin_bp.route('/users')
@admin_required
def users():
    db = get_db()
    all_users = list(db.users.find().sort("email", 1))
    return render_template('admin/users.html', users=all_users)


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
        log_history("USER_TOGGLE", f"Utilisateur {user['email']} {'active' if new_status else 'desactive'}",
                   user=session.get('email'))
        flash(f"Utilisateur {'active' if new_status else 'desactive'}", "success")
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
    log_history("USER_ROLE", f"Role modifie a {new_role}", user=session.get('email'))
    flash(f"Role modifie en {new_role}", "success")
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
        log_history("USER_DELETE", f"Utilisateur {user['email']} supprime", user=session.get('email'))
        flash("Utilisateur supprime", "success")
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<user_id>/toggle-verified', methods=['POST'])
@admin_required
def toggle_user_verified(user_id):
    """Toggle le statut verifie d'un utilisateur"""
    db = get_db()

    user_oid = safe_object_id(user_id)
    if not user_oid:
        return jsonify({"success": False, "message": "ID utilisateur invalide"}), 400

    user = db.users.find_one({"_id": user_oid})
    if not user:
        return jsonify({"success": False, "message": "Utilisateur introuvable"}), 404

    current_verified = user.get('verified', False)
    new_verified = not current_verified

    db.users.update_one(
        {"_id": user_oid},
        {"$set": {"verified": new_verified, "updated_at": datetime.utcnow()}}
    )

    status_text = "verifie" if new_verified else "non verifie"
    log_history("USER_VERIFY", f"Utilisateur {user['email']} marque {status_text}", user=session.get('email'))

    return jsonify({
        "success": True,
        "message": f"Utilisateur marque comme {status_text}",
        "verified": new_verified
    })


@admin_bp.route('/api/user/<user_id>/role', methods=['POST'])
@admin_required
def change_user_role(user_id):
    """Modifier le role d'un utilisateur"""
    db = get_db()

    user_oid = safe_object_id(user_id)
    if not user_oid:
        return jsonify({"success": False, "error": "ID utilisateur invalide"}), 400

    user = db.users.find_one({"_id": user_oid})
    if not user:
        return jsonify({"success": False, "error": "Utilisateur introuvable"}), 404

    # Don't allow changing your own role
    if str(user['_id']) == session.get('user_id'):
        return jsonify({"success": False, "error": "Vous ne pouvez pas modifier votre propre role"}), 403

    data = request.get_json()
    new_role = data.get('role', 'user')

    # Validate role
    valid_roles = ['user', 'admin', 'bank_respo', 'bank_user', 'bank_admin', 'bank_superadmin', 'admin_associate_bank']
    if new_role not in valid_roles:
        return jsonify({"success": False, "error": f"Role invalide. Roles acceptes: {', '.join(valid_roles)}"}), 400

    old_role = user.get('role', 'user')
    db.users.update_one(
        {"_id": user_oid},
        {"$set": {"role": new_role, "updated_at": datetime.utcnow()}}
    )

    log_history("USER_ROLE_CHANGE", f"Role de {user['email']} modifie: {old_role} -> {new_role}", user=session.get('email'))

    return jsonify({
        "success": True,
        "message": f"Role modifie en {new_role}",
        "old_role": old_role,
        "new_role": new_role
    })


@admin_bp.route('/users/bulk-verify', methods=['POST'])
@admin_required
def bulk_verify_users():
    """Marque plusieurs utilisateurs comme verifies"""
    db = get_db()

    data = request.get_json()
    user_ids = data.get('user_ids', [])

    if not user_ids:
        return jsonify({"success": False, "message": "Aucun utilisateur selectionne"}), 400

    # Convert to ObjectIds
    object_ids = [safe_object_id(uid) for uid in user_ids]
    object_ids = [oid for oid in object_ids if oid]

    if not object_ids:
        return jsonify({"success": False, "message": "IDs utilisateurs invalides"}), 400

    # Update users
    result = db.users.update_many(
        {"_id": {"$in": object_ids}},
        {"$set": {"verified": True, "updated_at": datetime.utcnow()}}
    )

    log_history("BULK_VERIFY", f"{result.modified_count} utilisateurs verifies", user=session.get('email'))

    return jsonify({
        "success": True,
        "message": f"{result.modified_count} utilisateur(s) verifie(s)"
    })


@admin_bp.route('/users/bulk-delete', methods=['POST'])
@admin_required
def bulk_delete_users():
    """Supprime plusieurs utilisateurs"""
    db = get_db()

    data = request.get_json()
    user_ids = data.get('user_ids', [])

    if not user_ids:
        return jsonify({"success": False, "message": "Aucun utilisateur selectionne"}), 400

    # Convert to ObjectIds
    object_ids = [safe_object_id(uid) for uid in user_ids]
    object_ids = [oid for oid in object_ids if oid]

    if not object_ids:
        return jsonify({"success": False, "message": "IDs utilisateurs invalides"}), 400

    # Don't delete yourself
    current_user_id = safe_object_id(session.get('user_id'))
    if current_user_id in object_ids:
        object_ids.remove(current_user_id)
        if not object_ids:
            return jsonify({"success": False, "message": "Vous ne pouvez pas supprimer votre propre compte"}), 403

    # Delete users
    result = db.users.delete_many({"_id": {"$in": object_ids}})

    # Delete associated wallets
    for oid in object_ids:
        db.wallets.delete_many({"user_id": str(oid)})

    log_history("BULK_DELETE", f"{result.deleted_count} utilisateurs supprimes", user=session.get('email'))

    return jsonify({
        "success": True,
        "message": f"{result.deleted_count} utilisateur(s) supprime(s)"
    })
