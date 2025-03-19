from flask import render_template, current_app
from flask_mail import Message
from app import mail
from itsdangerous import URLSafeTimedSerializer
import threading

def send_async_email(app, msg):
    """Envia email de forma assíncrona"""
    with app.app_context():
        mail.send(msg)

def send_email(subject, recipients, html_body, text_body=None):
    """Função base para envio de emails"""
    msg = Message(subject, recipients=recipients)
    msg.body = text_body or html_body
    msg.html = html_body
    
    # Enviar em background para não bloquear a resposta
    threading.Thread(
        target=send_async_email,
        args=(current_app._get_current_object(), msg)
    ).start()

def send_welcome_email(user):
    """Envia email de boas-vindas para novos usuários"""
    send_email(
        subject='Bem-vindo ao Sistema de Importação',
        recipients=[user.email],
        html_body=render_template('emails/welcome.html', user=user),
        text_body=render_template('emails/welcome.txt', user=user)
    )

def send_password_reset_email(user):
    """Envia email com link para redefinição de senha"""
    token = generate_reset_token(user.email)
    send_email(
        subject='Redefinição de Senha',
        recipients=[user.email],
        html_body=render_template('emails/reset_password.html', user=user, token=token),
        text_body=render_template('emails/reset_password.txt', user=user, token=token)
    )

def send_license_purchase_email(user, license):
    """Envia email após compra de licença"""
    send_email(
        subject='Licença Ativada com Sucesso',
        recipients=[user.email],
        html_body=render_template('emails/license_purchase.html', user=user, license=license),
        text_body=render_template('emails/license_purchase.txt', user=user, license=license)
    )

def send_contact_email(name, email, subject, message):
    """Envia email a partir do formulário de contato"""
    send_email(
        subject=f'Contato do Site: {subject}',
        recipients=[current_app.config['MAIL_DEFAULT_SENDER']],
        html_body=render_template('emails/contact.html', 
                                 name=name, 
                                 email=email, 
                                 subject=subject, 
                                 message=message)
    )

def generate_reset_token(email):
    """Gera token seguro para redefinição de senha"""
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt='password-reset-salt')

def verify_reset_token(token, expiration=3600):
    """Verifica token de redefinição de senha"""
    from app.models.users import User
    
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(
            token,
            salt='password-reset-salt',
            max_age=expiration
        )
        return User.query.filter_by(email=email).first()
    except:
        return None
