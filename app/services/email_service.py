import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app

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

    subject = "SarfX Admin - Verify your account"
    body = f"Welcome to SarfX Admin.\nPlease verify your account using this token: {token}\n\n(This is a secure automated message)"

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