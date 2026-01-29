from flask import Blueprint, render_template, session, redirect, url_for, request, flash, jsonify
from functools import wraps
from app.services.db_service import get_db
from werkzeug.utils import secure_filename
import os
from bson import ObjectId
from datetime import datetime

admin_banks_bp = Blueprint('admin_banks', __name__, url_prefix='/admin/banks')

UPLOAD_FOLDER = 'app/static/images/banks'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'svg'}

def admin_required(f):
    """Décorateur pour protéger les routes admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        
        db = get_db()
        from app.services.db_service import safe_object_id
        user_id = safe_object_id(session['user_id'])
        user = db.users.find_one({"_id": user_id}) if user_id else db.users.find_one({"email": session.get('email')})
        
        if not user or user.get('role') != 'admin':
            flash('Accès refusé. Admin uniquement.', 'error')
            return redirect(url_for('app.home'))
        
        return f(*args, **kwargs)
    return decorated_function

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@admin_banks_bp.route('/')
@admin_required
def list_banks():
    """Liste toutes les banques partenaires"""
    db = get_db()
    banks = list(db.banks.find().sort("name", 1))
    
    # Convertir ObjectId en string
    for bank in banks:
        bank['_id'] = str(bank['_id'])
    
    return render_template('admin_banks.html', banks=banks, active_tab='banks')

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
    
    return render_template('admin_bank_form.html', bank=None, action='create')

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
    return render_template('admin_bank_form.html', bank=bank, action='edit')

@admin_banks_bp.route('/delete/<bank_id>', methods=['POST'])
@admin_required
def delete_bank(bank_id):
    """Supprimer une banque partenaire"""
    db = get_db()
    bank = db.banks.find_one({"_id": ObjectId(bank_id)})
    
    if bank:
        db.banks.delete_one({"_id": ObjectId(bank_id)})
        flash(f'Banque "{bank.get("name")}" supprimée avec succès!', 'success')
    else:
        flash('Banque introuvable', 'error')
    
    return redirect(url_for('admin_banks.list_banks'))

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
