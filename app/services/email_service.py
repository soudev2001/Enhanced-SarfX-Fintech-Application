import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app, url_for

def send_verification_email(to_email, token):
    """
    Sends a verification email using the configured SMTP server.
    """
    smtp_server = current_app.config['SMTP_SERVER']
    smtp_port = current_app.config['SMTP_PORT']
    smtp_user = current_app.config['SMTP_EMAIL']
    smtp_password = current_app.config['SMTP_PASSWORD']

    if not all([smtp_server, smtp_user, smtp_password]):
        print("⚠️ SMTP credentials missing. Email skipped.")
        return False

    verify_url = url_for('auth.verify_email', token=token, _external=True)

    subject = "SarfX - Vérifiez votre compte"
    body = f"""Bienvenue sur SarfX !

Cliquez sur le lien ci-dessous pour vérifier votre compte :

{verify_url}

Si vous n'avez pas créé de compte sur SarfX, ignorez ce message.

L'équipe SarfX"""

    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
        server.quit()
        print(f"✅ Email sent to {to_email}")
        return True
    except Exception as e:
        print(f"❌ Email sending failed: {e}")
        return False


def send_password_reset_email(to_email, token):
    """
    Sends a password reset email using the configured SMTP server.
    """
    smtp_server = current_app.config['SMTP_SERVER']
    smtp_port = current_app.config['SMTP_PORT']
    smtp_user = current_app.config['SMTP_EMAIL']
    smtp_password = current_app.config['SMTP_PASSWORD']

    if not all([smtp_server, smtp_user, smtp_password]):
        print("⚠️ SMTP credentials missing. Email skipped.")
        return False

    reset_url = url_for('auth.reset_password', token=token, _external=True)

    subject = "SarfX - Réinitialisation de votre mot de passe"
    body = f"""Bonjour,

Vous avez demandé la réinitialisation de votre mot de passe SarfX.

Cliquez sur le lien ci-dessous pour créer un nouveau mot de passe :

{reset_url}

Ce lien expire dans 1 heure.

Si vous n'avez pas demandé cette réinitialisation, ignorez ce message.

L'équipe SarfX"""

    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
        server.quit()
        print(f"✅ Password reset email sent to {to_email}")
        return True
    except Exception as e:
        print(f"❌ Password reset email failed: {e}")
        return False