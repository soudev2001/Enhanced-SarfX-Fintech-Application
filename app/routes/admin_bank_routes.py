from flask import Blueprint, render_template, session, redirect, url_for, request, flash, jsonify
from app.services.db_service import get_db
from app.decorators import admin_required
from werkzeug.utils import secure_filename
import os
from bson import ObjectId
from datetime import datetime

admin_banks_bp = Blueprint('admin_banks', __name__, url_prefix='/admin/banks')

UPLOAD_FOLDER = 'app/static/images/banks'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'svg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@admin_banks_bp.route('/')
@admin_required
def list_banks():
    """Liste toutes les banques partenaires"""
    db = get_db()
    banks = list(db.banks.find().sort("name", 1))

    # Récupérer les utilisateurs vérifiés avec le rôle 'bank_respo'
    bank_respos = list(db.users.find({
        "role": "bank_respo",
        "verified": True
    }).sort("email", 1))

    # Convertir ObjectId en string pour la template
    for bank in banks:
        bank['_id'] = str(bank['_id'])
        # Convertir aussi assigned_user_id si présent (legacy single user)
        if 'assigned_user_id' in bank and bank['assigned_user_id']:
            bank['assigned_user_id'] = str(bank['assigned_user_id'])
        # Convertir assigned_users array (multiple users)
        if 'assigned_users' in bank and bank['assigned_users']:
            bank['assigned_users'] = [str(uid) for uid in bank['assigned_users']]
        else:
            bank['assigned_users'] = []
    for user in bank_respos:
        user['_id'] = str(user['_id'])

    return render_template('admin/banks_2026.html', banks=banks, users=bank_respos, active_tab='admin_banks')

@admin_banks_bp.route('/create', methods=['GET', 'POST'])
@admin_required
def create_bank():
    """Créer une nouvelle banque partenaire"""
    if request.method == 'POST':
        db = get_db()

        # Récupérer les données du formulaire
        name = request.form.get('name')
        code = request.form.get('code')
        website = request.form.get('website')
        description = request.form.get('description', '')
        is_active = request.form.get('is_active') == 'on'

        # Upload du logo
        logo_path = None
        if 'logo' in request.files:
            file = request.files['logo']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(f"{code.lower()}.{file.filename.rsplit('.', 1)[1].lower()}")
                filepath = os.path.join(UPLOAD_FOLDER, filename)

                # Créer le dossier si nécessaire
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)

                file.save(filepath)
                logo_path = f"/static/images/banks/{filename}"

        # Insérer dans la base de données
        bank_data = {
            "name": name,
            "code": code,
            "website": website,
            "description": description,
            "logo": logo_path,
            "is_active": is_active,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        result = db.banks.insert_one(bank_data)

        # Créer aussi l'entrée dans atm_locations pour la cohérence
        db.atm_locations.update_many(
            {"bank_code": code},
            {"$set": {"bank_name": name}},
            upsert=False
        )

        flash(f'Banque "{name}" créée avec succès!', 'success')
        return redirect(url_for('admin_banks.list_banks'))

    return render_template('admin/bank_form_2026.html', bank=None, action='create')

@admin_banks_bp.route('/edit/<bank_id>', methods=['GET', 'POST'])
@admin_required
def edit_bank(bank_id):
    """Éditer une banque partenaire"""
    db = get_db()
    bank = db.banks.find_one({"_id": ObjectId(bank_id)})

    if not bank:
        flash('Banque introuvable', 'error')
        return redirect(url_for('admin_banks.list_banks'))

    if request.method == 'POST':
        name = request.form.get('name')
        code = request.form.get('code')
        website = request.form.get('website')
        description = request.form.get('description', '')
        is_active = request.form.get('is_active') == 'on'

        update_data = {
            "name": name,
            "code": code,
            "website": website,
            "description": description,
            "is_active": is_active,
            "updated_at": datetime.utcnow()
        }

        # Upload nouveau logo si fourni
        if 'logo' in request.files:
            file = request.files['logo']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(f"{code.lower()}.{file.filename.rsplit('.', 1)[1].lower()}")
                filepath = os.path.join(UPLOAD_FOLDER, filename)

                os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                file.save(filepath)
                update_data["logo"] = f"/static/images/banks/{filename}"

        db.banks.update_one({"_id": ObjectId(bank_id)}, {"$set": update_data})

        flash(f'Banque "{name}" modifiée avec succès!', 'success')
        return redirect(url_for('admin_banks.list_banks'))

    bank['_id'] = str(bank['_id'])
    return render_template('admin/bank_form_2026.html', bank=bank, action='edit')

@admin_banks_bp.route('/delete/<bank_id>', methods=['POST'])
@admin_required
def delete_bank(bank_id):
    """Supprimer une banque partenaire et retourner une réponse JSON."""
    db = get_db()
    from app.services.db_service import safe_object_id

    bank_oid = safe_object_id(bank_id)
    if not bank_oid:
        return jsonify({"success": False, "message": "ID de banque invalide"}), 400

    bank = db.banks.find_one({"_id": bank_oid})

    if bank:
        db.banks.delete_one({"_id": bank_oid})
        # Optionnel: Supprimer aussi les associations ou autres données liées
        message = f'La banque "{bank.get("name")}" a été supprimée avec succès!'
        flash(message, 'success')
        return jsonify({"success": True, "message": message})
    else:
        message = 'Banque introuvable.'
        flash(message, 'error')
        return jsonify({"success": False, "message": message}), 404

@admin_banks_bp.route('/toggle/<bank_id>', methods=['POST'])
@admin_required
def toggle_active(bank_id):
    """Activer/désactiver une banque"""
    db = get_db()
    bank = db.banks.find_one({"_id": ObjectId(bank_id)})

    if bank:
        new_status = not bank.get('is_active', True)
        db.banks.update_one(
            {"_id": ObjectId(bank_id)},
            {"$set": {"is_active": new_status, "updated_at": datetime.utcnow()}}
        )
        status_text = "activée" if new_status else "désactivée"
        return jsonify({"success": True, "message": f"Banque {status_text}", "is_active": new_status})

    return jsonify({"success": False, "message": "Banque introuvable"}), 404

@admin_banks_bp.route('/<bank_id>/assign-user', methods=['POST'])
@admin_required
def assign_user_to_bank(bank_id):
    """Assigne un utilisateur (bank_respo) à une banque."""
    db = get_db()
    from app.services.db_service import safe_object_id

    bank_oid = safe_object_id(bank_id)
    if not bank_oid:
        return jsonify({"success": False, "message": "ID de banque invalide."}), 400

    data = request.get_json()
    user_id = data.get('user_id')
    user_oid = safe_object_id(user_id)
    if not user_oid:
        return jsonify({"success": False, "message": "ID d'utilisateur invalide."}), 400

    # Vérifier que la banque et l'utilisateur existent
    bank = db.banks.find_one({"_id": bank_oid})
    if not bank:
        return jsonify({"success": False, "message": "Banque introuvable."}), 404

    user = db.users.find_one({"_id": user_oid, "role": "bank_respo"})
    if not user:
        return jsonify({"success": False, "message": "Utilisateur introuvable ou rôle incorrect."}), 404

    # Vérifier si l'utilisateur est déjà assigné à cette banque (support multi-assignation)
    assigned_users = bank.get('assigned_users', [])
    if user_oid in assigned_users:
        return jsonify({"success": False, "message": "Cet utilisateur est déjà assigné à cette banque."}), 400

    # Ajouter l'utilisateur à la liste des utilisateurs assignés
    db.banks.update_one(
        {"_id": bank_oid},
        {
            "$addToSet": {"assigned_users": user_oid},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )

    flash(f"L'utilisateur {user['email']} a été assigné à la banque {bank['name']}.", 'success')
    return jsonify({"success": True, "message": "Utilisateur assigné avec succès!"})

@admin_banks_bp.route('/<bank_id>/remove-user', methods=['POST'])
@admin_required
def remove_user_from_bank(bank_id):
    """Retire un utilisateur assigné d'une banque."""
    db = get_db()
    from app.services.db_service import safe_object_id

    bank_oid = safe_object_id(bank_id)
    if not bank_oid:
        return jsonify({"success": False, "message": "ID de banque invalide."}), 400

    data = request.get_json()
    user_id = data.get('user_id')
    user_oid = safe_object_id(user_id)
    if not user_oid:
        return jsonify({"success": False, "message": "ID d'utilisateur invalide."}), 400

    # Vérifier que la banque existe
    bank = db.banks.find_one({"_id": bank_oid})
    if not bank:
        return jsonify({"success": False, "message": "Banque introuvable."}), 404

    # Retirer l'utilisateur de la liste
    db.banks.update_one(
        {"_id": bank_oid},
        {
            "$pull": {"assigned_users": user_oid},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )

    return jsonify({"success": True, "message": "Utilisateur retiré avec succès!"})
