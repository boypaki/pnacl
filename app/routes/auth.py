from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse

from app import db
from app.models.users import User
from app.utils.email_sender import send_password_reset_email, send_welcome_email

auth_blueprint = Blueprint('auth', __name__)

@auth_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = 'remember' in request.form
        
        user = User.query.filter_by(email=email).first()
        
        # Verificar usuário e senha
        if not user or not user.check_password(password):
            flash('Email ou senha incorretos', 'danger')
            return render_template('auth/login.html')
            
        # Verificar se conta está ativa
        if not user.is_active:
            flash('Sua conta está inativa. Entre em contato com o suporte.', 'warning')
            return render_template('auth/login.html')
            
        # Login bem sucedido
        login_user(user, remember=remember)
        
        # Atualizar data de último login
        user.last_login = db.func.now()
        db.session.commit()
        
        # Redirecionar para página pretendida ou dashboard
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.dashboard')
            
        return redirect(next_page)
        
    return render_template('auth/login.html')

@auth_blueprint.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validar campos
        if not name or not email or not password:
            flash('Todos os campos são obrigatórios', 'danger')
            return render_template('auth/register.html')
            
        if password != confirm_password:
            flash('As senhas não coincidem', 'danger')
            return render_template('auth/register.html')
            
        # Verificar se email já existe
        if User.query.filter_by(email=email).first():
            flash('Este email já está registrado', 'danger')
            return render_template('auth/register.html')
            
        # Criar novo usuário
        user = User(name=name, email=email)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # Enviar email de boas-vindas
        send_welcome_email(user)
        
        flash('Registro realizado com sucesso! Você já pode fazer login.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/register.html')

@auth_blueprint.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@auth_blueprint.route('/reset-password', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        
        user = User.query.filter_by(email=email).first()
        
        if user:
            send_password_reset_email(user)
            
        # Sempre mostrar a mesma mensagem para evitar vazamento de informação
        flash('Um email com instruções foi enviado para o endereço fornecido.', 'info')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/reset_password_request.html')

@auth_blueprint.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    from app.utils.email_sender import verify_reset_token
    
    user = verify_reset_token(token)
    
    if not user:
        flash('Link inválido ou expirado', 'danger')
        return redirect(url_for('auth.reset_password_request'))
        
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not password or password != confirm_password:
            flash('As senhas não coincidem', 'danger')
            return render_template('auth/reset_password.html')
            
        user.set_password(password)
        db.session.commit()
        
        flash('Sua senha foi atualizada com sucesso!', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/reset_password.html')

@auth_blueprint.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        name = request.form.get('name')
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Atualizar nome
        if name and name != current_user.name:
            current_user.name = name
            db.session.commit()
            flash('Nome atualizado com sucesso', 'success')
            
        # Atualizar senha
        if current_password and new_password:
            if not current_user.check_password(current_password):
                flash('Senha atual incorreta', 'danger')
            elif new_password != confirm_password:
                flash('As senhas não coincidem', 'danger')
            else:
                current_user.set_password(new_password)
                db.session.commit()
                flash('Senha atualizada com sucesso', 'success')
    
    # Obter licenças do usuário
    licenses = License.query.filter_by(user_id=current_user.id).order_by(License.created_at.desc()).all()
    
    return render_template('auth/profile.html', licenses=licenses)
