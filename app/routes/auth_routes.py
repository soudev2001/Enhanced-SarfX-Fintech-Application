from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.services.db_service import get_db, log_history
from app.services.email_service import send_verification_email
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        db = get_db()
        if db is None:
            flash("Erreur de connexion à la base de données", "error")
            return render_template('app_login.html')

        user = db.users.find_one({"email": email})
        
        if user and check_password_hash(user['password'], password):
            session.permanent = True
            session['user_id'] = str(user['_id'])
            session['email'] = user['email']
            session['role'] = user.get('role', 'user')
            log_history("LOGIN", f"Connexion réussie: {email}", user=email)
            return redirect(url_for('app.home'))
        else:
            flash("Identifiants incorrects", "error")
            
    return render_template('app_login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    # En production, vous voudrez peut-être désactiver l'enregistrement public
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        db = get_db()
        if db.users.find_one({"email": email}):
            flash("Cet email est déjà utilisé", "error")
        else:
            hashed_pw = generate_password_hash(password)
            token = str(uuid.uuid4())
            
            user_doc = {
                "email": email,
                "password": hashed_pw,
                "role": "user",
                "verified": False,
                "token": token
            }
            result = db.users.insert_one(user_doc)
            
            # Créer un wallet pour le nouvel utilisateur
            from app.services.wallet_service import create_wallet
            create_wallet(str(result.inserted_id), email)
            
            # Envoi Email (Non bloquant pour l'UX)
            try:
                send_verification_email(email, token)
            except:
                pass # Ne pas bloquer l'inscription si l'email échoue
                
            flash("Compte créé. Vérifiez vos emails.", "success")
            return redirect(url_for('auth.login'))
            
    return render_template('app_login.html', mode='register')

@auth_bp.route('/logout')
def logout():
    user = session.get('email', 'Unknown')
    log_history("LOGOUT", "Déconnexion", user=user)
    session.clear()
    return redirect(url_for('auth.login'))