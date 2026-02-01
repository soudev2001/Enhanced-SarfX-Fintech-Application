from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from app.services.db_service import get_db, log_history
from app.services.email_service import send_verification_email, send_password_reset_email
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import uuid

auth_bp = Blueprint('auth', __name__)


# ============================================
# GOOGLE OAUTH ROUTES
# ============================================

@auth_bp.route('/login/google')
def google_login():
    """Initiate Google OAuth login"""
    oauth = current_app.oauth

    if not hasattr(oauth, 'google') or not oauth.google:
        flash("Google OAuth n'est pas configuré", "error")
        return redirect(url_for('auth.login'))

    # Get redirect URI from config or build it
    redirect_uri = current_app.config.get('OAUTH_REDIRECT_URI') or url_for('auth.google_callback', _external=True)

    return oauth.google.authorize_redirect(redirect_uri)


@auth_bp.route('/login/google/callback')
def google_callback():
    """Handle Google OAuth callback"""
    oauth = current_app.oauth

    if not hasattr(oauth, 'google') or not oauth.google:
        flash("Google OAuth n'est pas configuré", "error")
        return redirect(url_for('auth.login'))

    try:
        # Get token from Google
        token = oauth.google.authorize_access_token()

        # Get user info from token
        user_info = token.get('userinfo')
        if not user_info:
            # Fallback: fetch from userinfo endpoint
            user_info = oauth.google.get('https://openidconnect.googleapis.com/v1/userinfo').json()

        if not user_info or not user_info.get('email'):
            flash("Impossible de récupérer les informations Google", "error")
            return redirect(url_for('auth.login'))

        google_email = user_info['email']
        google_id = user_info.get('sub')  # Google's unique user ID
        google_name = user_info.get('name', google_email.split('@')[0])
        google_picture = user_info.get('picture')

        db = get_db()
        if db is None:
            flash("Erreur de connexion à la base de données", "error")
            return redirect(url_for('auth.login'))

        # Check if user exists by Google ID or email
        user = db.users.find_one({
            "$or": [
                {"google_id": google_id},
                {"email": google_email}
            ]
        })

        if user:
            # Existing user - link Google account if not already linked
            if not user.get('google_id'):
                db.users.update_one(
                    {"_id": user['_id']},
                    {"$set": {
                        "google_id": google_id,
                        "google_picture": google_picture,
                        "google_linked_at": datetime.utcnow()
                    }}
                )
                log_history("GOOGLE_LINK", f"Compte Google lié: {google_email}", user=google_email)

            # Update picture if changed
            elif google_picture and user.get('google_picture') != google_picture:
                db.users.update_one(
                    {"_id": user['_id']},
                    {"$set": {"google_picture": google_picture}}
                )

            # Login the user
            session.permanent = True
            session['user_id'] = str(user['_id'])
            session['email'] = user['email']
            session['role'] = user.get('role', 'user')
            session['auth_method'] = 'google'

            log_history("LOGIN_GOOGLE", f"Connexion Google réussie: {google_email}", user=google_email)
            flash(f"Bienvenue {google_name} !", "success")
            return redirect(url_for('app.home'))

        else:
            # New user - create account
            user_doc = {
                "email": google_email,
                "full_name": google_name,
                "password": None,  # No password for Google-only accounts
                "role": "user",
                "verified": True,  # Google accounts are pre-verified
                "google_id": google_id,
                "google_picture": google_picture,
                "google_linked_at": datetime.utcnow(),
                "created_at": datetime.utcnow(),
                "auth_provider": "google"
            }
            result = db.users.insert_one(user_doc)

            # Create wallet for new user
            from app.services.wallet_service import create_wallet
            create_wallet(str(result.inserted_id), google_email)

            # Login the new user
            session.permanent = True
            session['user_id'] = str(result.inserted_id)
            session['email'] = google_email
            session['role'] = 'user'
            session['auth_method'] = 'google'

            log_history("REGISTER_GOOGLE", f"Nouveau compte Google créé: {google_email}", user=google_email)
            flash(f"Bienvenue sur SarfX, {google_name} ! Votre compte a été créé.", "success")
            return redirect(url_for('app.home'))

    except Exception as e:
        current_app.logger.error(f"Google OAuth error: {str(e)}")
        flash("Erreur lors de la connexion avec Google. Veuillez réessayer.", "error")
        return redirect(url_for('auth.login'))


# ============================================
# STANDARD LOGIN/REGISTER ROUTES
# ============================================

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        db = get_db()
        if db is None:
            flash("Erreur de connexion à la base de données", "error")
            return render_template('auth/login.html')

        user = db.users.find_one({"email": email})

        if user:
            # Check if this is a Google-only account
            if user.get('auth_provider') == 'google' and not user.get('password'):
                flash("Ce compte utilise Google. Cliquez sur 'Se connecter avec Google'.", "info")
                return render_template('auth/login.html')

            if user.get('password') and check_password_hash(user['password'], password):
                session.permanent = True
                session['user_id'] = str(user['_id'])
                session['email'] = user['email']
                session['role'] = user.get('role', 'user')
                session['auth_method'] = 'email'
                log_history("LOGIN", f"Connexion réussie: {email}", user=email)
                return redirect(url_for('app.home'))

        flash("Identifiants incorrects", "error")

    return render_template('auth/login.html')

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
                "token": token,
                "created_at": datetime.utcnow(),
                "auth_provider": "email"
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

    return render_template('auth/login.html', mode='register')

@auth_bp.route('/logout')
def logout():
    user = session.get('email', 'Unknown')
    log_history("LOGOUT", "Déconnexion", user=user)
    session.clear()
    return redirect(url_for('auth.login'))


# ============================================
# EMAIL VERIFICATION ROUTE
# ============================================

@auth_bp.route('/verify/<token>')
def verify_email(token):
    """Verify user email with token"""
    db = get_db()
    if db is None:
        flash("Erreur de connexion à la base de données", "error")
        return redirect(url_for('auth.login'))

    user = db.users.find_one({"token": token})

    if not user:
        flash("Lien de vérification invalide ou expiré", "error")
        return redirect(url_for('auth.login'))

    if user.get('verified'):
        flash("Votre compte est déjà vérifié", "info")
        return redirect(url_for('auth.login'))

    # Mark user as verified
    db.users.update_one(
        {"_id": user['_id']},
        {
            "$set": {"verified": True, "verified_at": datetime.utcnow()},
            "$unset": {"token": ""}
        }
    )

    log_history("EMAIL_VERIFIED", f"Email vérifié: {user['email']}", user=user['email'])
    flash("Votre email a été vérifié avec succès ! Vous pouvez maintenant vous connecter.", "success")
    return redirect(url_for('auth.login'))


# ============================================
# PASSWORD RESET ROUTES
# ============================================

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Request password reset"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()

        if not email:
            flash("Veuillez entrer votre adresse email", "error")
            return render_template('auth/forgot_password.html')

        db = get_db()
        if db is None:
            flash("Erreur de connexion à la base de données", "error")
            return render_template('auth/forgot_password.html')

        user = db.users.find_one({"email": email})

        # Always show success message to prevent email enumeration
        if user:
            # Check if it's a Google-only account
            if user.get('auth_provider') == 'google' and not user.get('password'):
                flash("Ce compte utilise Google. Connectez-vous avec Google.", "info")
                return redirect(url_for('auth.login'))

            # Generate reset token
            reset_token = str(uuid.uuid4())
            reset_expires = datetime.utcnow() + timedelta(hours=1)

            db.users.update_one(
                {"_id": user['_id']},
                {"$set": {
                    "reset_token": reset_token,
                    "reset_token_expires": reset_expires
                }}
            )

            # Send email
            try:
                send_password_reset_email(email, reset_token)
            except Exception as e:
                current_app.logger.error(f"Failed to send reset email: {e}")

            log_history("PASSWORD_RESET_REQUEST", f"Demande de réinitialisation: {email}", user=email)

        flash("Si un compte existe avec cet email, vous recevrez un lien de réinitialisation.", "success")
        return redirect(url_for('auth.login'))

    return render_template('auth/forgot_password.html')


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password with token"""
    db = get_db()
    if db is None:
        flash("Erreur de connexion à la base de données", "error")
        return redirect(url_for('auth.login'))

    user = db.users.find_one({
        "reset_token": token,
        "reset_token_expires": {"$gt": datetime.utcnow()}
    })

    if not user:
        flash("Lien de réinitialisation invalide ou expiré", "error")
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')

        if not password or len(password) < 6:
            flash("Le mot de passe doit contenir au moins 6 caractères", "error")
            return render_template('auth/reset_password.html', token=token)

        if password != password_confirm:
            flash("Les mots de passe ne correspondent pas", "error")
            return render_template('auth/reset_password.html', token=token)

        # Update password
        hashed_pw = generate_password_hash(password)
        db.users.update_one(
            {"_id": user['_id']},
            {
                "$set": {"password": hashed_pw, "password_changed_at": datetime.utcnow()},
                "$unset": {"reset_token": "", "reset_token_expires": ""}
            }
        )

        log_history("PASSWORD_RESET_SUCCESS", f"Mot de passe réinitialisé: {user['email']}", user=user['email'])
        flash("Mot de passe modifié avec succès ! Vous pouvez maintenant vous connecter.", "success")
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', token=token, email=user['email'])